from datetime import date, datetime, timedelta

from db import fetch_all, fetch_one
from services.location_service import resolve_location_to_airports


def _placeholders(values):
    return ", ".join(["%s"] * len(values))


def _month_start(day):
    return day.replace(day=1)


def _next_month(day):
    if day.month == 12:
        return date(day.year + 1, 1, 1)
    return date(day.year, day.month + 1, 1)


def _add_months(day, months):
    month_index = day.month - 1 + months
    year = day.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def _parse_date_input(value, field_name):
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid date.") from exc


def _attach_bar_percent(rows, key):
    max_value = max((float(row[key] or 0) for row in rows), default=0)
    for row in rows:
        value = float(row[key] or 0)
        row["bar_percent"] = 0 if max_value <= 0 else round(value / max_value * 100, 2)
    return rows


def _monthly_chart_rows(raw_rows, start_month, end_month, value_key):
    value_map = {
        str(row["month_key"]): float(row[value_key] or 0)
        for row in raw_rows
    }
    months = []
    month_cursor = start_month
    max_value = max(value_map.values(), default=0)
    while month_cursor <= end_month:
        month_key = month_cursor.isoformat()
        value = value_map.get(month_key, 0)
        months.append(
            {
                "month_key": month_key,
                "month_label": month_cursor.strftime("%b %Y"),
                "value": value,
                "bar_percent": 0 if max_value <= 0 else round(value / max_value * 100, 2),
            }
        )
        month_cursor = _next_month(month_cursor)
    return months


def _active_ticket_join():
    return """
        LEFT JOIN ticket t
          ON f.airline_name = t.airline_name
         AND f.flight_num = t.flight_num
         AND t.ticket_status = 'active'
    """


def get_agent_commission_summary(agent_email):
    """Summarize a booking agent's commission for tickets sold in last 30 days."""
    summary = fetch_one(
        """
        SELECT
            COUNT(*) AS tickets_sold,
            COALESCE(SUM(sold_price * 0.10), 0) AS total_commission,
            COALESCE(AVG(sold_price * 0.10), 0) AS average_commission
        FROM ticket
        WHERE booking_agent_email = %s
          AND ticket_status = 'active'
          AND purchase_date >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL 30 DAY)
        """,
        (agent_email,),
    )
    return summary or {"tickets_sold": 0, "total_commission": 0, "average_commission": 0}


def get_customer_default_spending(customer_email):
    """Return last-12-month spending and a last-6-month monthly chart."""
    total = fetch_one(
        """
        SELECT COALESCE(SUM(sold_price), 0) AS total_spending
        FROM ticket
        WHERE customer_email = %s
          AND ticket_status = 'active'
          AND purchase_date >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL 12 MONTH)
        """,
        (customer_email,),
    )

    current_month = _month_start(datetime.utcnow().date())
    start_month = _add_months(current_month, -5)
    rows = fetch_all(
        """
        SELECT DATE_FORMAT(purchase_date, '%%Y-%%m-01') AS month_key,
               COALESCE(SUM(sold_price), 0) AS total_spending
        FROM ticket
        WHERE customer_email = %s
          AND ticket_status = 'active'
          AND purchase_date >= %s
          AND purchase_date < %s
        GROUP BY month_key
        ORDER BY month_key
        """,
        (customer_email, start_month, _next_month(current_month)),
    )
    return {
        "total_spending": float((total or {}).get("total_spending", 0) or 0),
        "chart_rows": _monthly_chart_rows(rows, start_month, current_month, "total_spending"),
    }


def get_customer_custom_spending(customer_email, start_date, end_date):
    """Return spending analytics for a custom inclusive date range."""
    start_day = _parse_date_input(start_date, "Start date")
    end_day = _parse_date_input(end_date, "End date")
    if end_day < start_day:
        raise ValueError("End date cannot be earlier than start date.")

    total = fetch_one(
        """
        SELECT COALESCE(SUM(sold_price), 0) AS total_spending
        FROM ticket
        WHERE customer_email = %s
          AND ticket_status = 'active'
          AND purchase_date >= %s
          AND purchase_date < %s
        """,
        (customer_email, start_day, end_day + timedelta(days=1)),
    )
    start_month = _month_start(start_day)
    end_month = _month_start(end_day)
    rows = fetch_all(
        """
        SELECT DATE_FORMAT(purchase_date, '%%Y-%%m-01') AS month_key,
               COALESCE(SUM(sold_price), 0) AS total_spending
        FROM ticket
        WHERE customer_email = %s
          AND ticket_status = 'active'
          AND purchase_date >= %s
          AND purchase_date < %s
        GROUP BY month_key
        ORDER BY month_key
        """,
        (customer_email, start_day, end_day + timedelta(days=1)),
    )
    return {
        "start_date": start_day.isoformat(),
        "end_date": end_day.isoformat(),
        "total_spending": float((total or {}).get("total_spending", 0) or 0),
        "chart_rows": _monthly_chart_rows(rows, start_month, end_month, "total_spending"),
    }


def get_agent_customer_crm(agent_email):
    """Summarize customers served by a booking agent."""
    return fetch_all(
        """
        SELECT
            customer_email,
            COUNT(*) AS tickets_bought,
            COALESCE(SUM(sold_price), 0) AS total_revenue,
            COALESCE(SUM(sold_price * 0.10), 0) AS total_commission,
            MAX(purchase_date) AS last_purchase_date,
            CASE
                WHEN COUNT(*) >= 3 THEN 'High-value customer'
                ELSE 'Regular customer'
            END AS customer_label
        FROM ticket
        WHERE booking_agent_email = %s
          AND ticket_status = 'active'
        GROUP BY customer_email
        ORDER BY total_revenue DESC, last_purchase_date DESC
        """,
        (agent_email,),
    )


def get_agent_top_customers_by_tickets(agent_email):
    """Return top five customers by tickets in the last six months."""
    rows = fetch_all(
        """
        SELECT customer_email, COUNT(*) AS tickets_sold
        FROM ticket
        WHERE booking_agent_email = %s
          AND ticket_status = 'active'
          AND purchase_date >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL 6 MONTH)
        GROUP BY customer_email
        ORDER BY tickets_sold DESC, customer_email ASC
        LIMIT 5
        """,
        (agent_email,),
    )
    return _attach_bar_percent(rows, "tickets_sold")


def get_agent_top_customers_by_commission(agent_email):
    """Return top five customers by commission in the last year."""
    rows = fetch_all(
        """
        SELECT customer_email, COALESCE(SUM(sold_price * 0.10), 0) AS total_commission
        FROM ticket
        WHERE booking_agent_email = %s
          AND ticket_status = 'active'
          AND purchase_date >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 YEAR)
        GROUP BY customer_email
        ORDER BY total_commission DESC, customer_email ASC
        LIMIT 5
        """,
        (agent_email,),
    )
    return _attach_bar_percent(rows, "total_commission")


def get_staff_flight_summary(airline_name):
    """Count this airline's flights by dynamic current status."""
    return fetch_one(
        """
        SELECT
            SUM(current_status = 'upcoming') AS upcoming_count,
            SUM(current_status = 'in_progress') AS in_progress_count,
            SUM(current_status = 'completed') AS completed_count,
            SUM(current_status = 'delayed') AS delayed_count,
            SUM(current_status = 'cancelled') AS cancelled_count
        FROM flight_status_view
        WHERE airline_name = %s
        """,
        (airline_name,),
    )


def get_admin_top_agents_by_tickets(airline_name, year, month=None):
    """Return top booking agents by tickets sold for a selected month or full year."""
    sql = """
        SELECT booking_agent_email AS agent_email, COUNT(*) AS tickets_sold
        FROM ticket
        WHERE airline_name = %s
          AND booking_agent_email IS NOT NULL
          AND ticket_status = 'active'
          AND YEAR(purchase_date) = %s
    """
    params = [airline_name, year]
    if month is not None:
        sql += " AND MONTH(purchase_date) = %s"
        params.append(month)
    sql += """
        GROUP BY booking_agent_email
        ORDER BY tickets_sold DESC, agent_email ASC
        LIMIT 5
    """
    return fetch_all(sql, params)


def get_admin_top_agents_by_commission(airline_name, year, month=None):
    """Return top booking agents by commission for a selected month or full year."""
    sql = """
        SELECT booking_agent_email AS agent_email,
               COALESCE(SUM(sold_price * 0.10), 0) AS total_commission
        FROM ticket
        WHERE airline_name = %s
          AND booking_agent_email IS NOT NULL
          AND ticket_status = 'active'
          AND YEAR(purchase_date) = %s
    """
    params = [airline_name, year]
    if month is not None:
        sql += " AND MONTH(purchase_date) = %s"
        params.append(month)
    sql += """
        GROUP BY booking_agent_email
        ORDER BY total_commission DESC, agent_email ASC
        LIMIT 5
    """
    return fetch_all(sql, params)


def get_admin_most_frequent_customer(airline_name):
    """Return the most frequent customer in the last year."""
    return fetch_one(
        """
        SELECT customer_email, COUNT(*) AS tickets_sold, COALESCE(SUM(sold_price), 0) AS total_spending
        FROM ticket
        WHERE airline_name = %s
          AND ticket_status = 'active'
          AND purchase_date >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 YEAR)
        GROUP BY customer_email
        ORDER BY tickets_sold DESC, total_spending DESC, customer_email ASC
        LIMIT 1
        """,
        (airline_name,),
    )


def get_admin_tickets_sold_per_month(airline_name, start_date=None, end_date=None):
    """Return a ticket-sales bar chart for the default or custom date window."""
    if start_date is None and end_date is None:
        current_day = datetime.utcnow().date()
        current_month = _month_start(current_day)
        start_month = _add_months(current_month, -11)
        rows = fetch_all(
            """
            SELECT DATE_FORMAT(purchase_date, '%%Y-%%m-01') AS month_key,
                   COUNT(*) AS tickets_sold
            FROM ticket
            WHERE airline_name = %s
              AND ticket_status = 'active'
              AND purchase_date >= %s
              AND purchase_date < %s
            GROUP BY month_key
            ORDER BY month_key
            """,
            (airline_name, start_month, _next_month(current_month)),
        )
        return {
            "start_date": start_month.isoformat(),
            "end_date": current_day.isoformat(),
            "chart_rows": _monthly_chart_rows(rows, start_month, current_month, "tickets_sold"),
        }

    start_day = _parse_date_input(start_date, "Tickets chart start date")
    end_day = _parse_date_input(end_date, "Tickets chart end date")
    if end_day < start_day:
        raise ValueError("Tickets chart end date cannot be earlier than the start date.")

    start_month = _month_start(start_day)
    end_month = _month_start(end_day)
    rows = fetch_all(
        """
        SELECT DATE_FORMAT(purchase_date, '%%Y-%%m-01') AS month_key,
               COUNT(*) AS tickets_sold
        FROM ticket
        WHERE airline_name = %s
          AND ticket_status = 'active'
          AND purchase_date >= %s
          AND purchase_date < %s
        GROUP BY month_key
        ORDER BY month_key
        """,
        (airline_name, start_day, end_day + timedelta(days=1)),
    )
    return {
        "start_date": start_day.isoformat(),
        "end_date": end_day.isoformat(),
        "chart_rows": _monthly_chart_rows(rows, start_month, end_month, "tickets_sold"),
    }


def get_admin_delay_vs_on_time_stats(airline_name):
    """Return delayed versus on-time stats for flights that departed in the last year."""
    stats = fetch_one(
        """
        SELECT
            SUM(status = 'scheduled') AS on_time_flights,
            SUM(status = 'delayed') AS delayed_flights,
            SUM(status = 'cancelled') AS cancelled_flights
        FROM flight
        WHERE airline_name = %s
          AND departure_time_utc >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 YEAR)
          AND departure_time_utc < UTC_TIMESTAMP()
        """,
        (airline_name,),
    ) or {"on_time_flights": 0, "delayed_flights": 0, "cancelled_flights": 0}
    total_tracked = (stats["on_time_flights"] or 0) + (stats["delayed_flights"] or 0)
    stats["delayed_rate"] = 0 if total_tracked == 0 else round((stats["delayed_flights"] or 0) / total_tracked * 100, 2)
    return stats


def get_admin_top_destinations(airline_name, months, group_by="airport"):
    """Return top destinations by tickets sold over the given month window."""
    if group_by == "city":
        rows = fetch_all(
            """
            SELECT c.city_name AS destination_name,
                   COUNT(t.ticket_id) AS tickets_sold,
                   COALESCE(SUM(t.sold_price), 0) AS revenue
            FROM ticket t
            JOIN flight f
              ON t.airline_name = f.airline_name AND t.flight_num = f.flight_num
            JOIN airport a
              ON f.arrival_airport = a.airport_code
            JOIN city c
              ON a.city_id = c.city_id
            WHERE t.airline_name = %s
              AND t.ticket_status = 'active'
              AND t.purchase_date >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL %s MONTH)
            GROUP BY c.city_name
            ORDER BY tickets_sold DESC, revenue DESC, destination_name ASC
            LIMIT 5
            """,
            (airline_name, months),
        )
    else:
        rows = fetch_all(
            """
            SELECT f.arrival_airport AS destination_name,
                   COUNT(t.ticket_id) AS tickets_sold,
                   COALESCE(SUM(t.sold_price), 0) AS revenue
            FROM ticket t
            JOIN flight f
              ON t.airline_name = f.airline_name AND t.flight_num = f.flight_num
            WHERE t.airline_name = %s
              AND t.ticket_status = 'active'
              AND t.purchase_date >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL %s MONTH)
            GROUP BY f.arrival_airport
            ORDER BY tickets_sold DESC, revenue DESC, destination_name ASC
            LIMIT 5
            """,
            (airline_name, months),
        )
    return _attach_bar_percent(rows, "tickets_sold")


def get_flight_revenue_dashboard(airline_name):
    """Return load factor and revenue management metrics per flight."""
    return fetch_all(
        f"""
        SELECT
            f.airline_name,
            f.flight_num,
            CONCAT(f.departure_airport, ' -> ', f.arrival_airport) AS route,
            f.current_status,
            a.seats AS capacity,
            COUNT(t.ticket_id) AS active_tickets_sold,
            a.seats - COUNT(t.ticket_id) AS seats_left,
            ROUND(COUNT(t.ticket_id) / a.seats * 100, 2) AS load_factor,
            COALESCE(SUM(t.sold_price), 0) AS revenue,
            CASE
                WHEN a.seats - COUNT(t.ticket_id) = 0 THEN 'Sold Out'
                WHEN COUNT(t.ticket_id) / a.seats >= 0.90 THEN 'High Demand'
                WHEN COUNT(t.ticket_id) / a.seats >= 0.50 THEN 'Normal'
                ELSE 'Consider Promotion'
            END AS business_signal
        FROM flight_status_view f
        JOIN airplane a
          ON f.airline_name = a.airline_name AND f.airplane_id = a.airplane_id
        {_active_ticket_join()}
        WHERE f.airline_name = %s
        GROUP BY f.airline_name, f.flight_num, f.departure_airport, f.arrival_airport,
                 f.current_status, a.seats, f.departure_time
        ORDER BY f.departure_time DESC
        """,
        (airline_name,),
    )


def get_agent_performance_summary(airline_name):
    """Summarize booking agent performance for an airline."""
    return fetch_all(
        """
        SELECT
            ba.email AS agent_email,
            COALESCE(SUM(t.ticket_status = 'active'), 0) AS tickets_sold,
            COALESCE(SUM(CASE WHEN t.ticket_status = 'active' THEN t.sold_price ELSE 0 END), 0) AS revenue_generated,
            COALESCE(SUM(CASE WHEN t.ticket_status = 'active' THEN t.sold_price * 0.10 ELSE 0 END), 0) AS commission,
            MAX(t.purchase_date) AS last_purchase_date,
            COALESCE(SUM(t.ticket_status = 'cancelled'), 0) AS cancelled_ticket_count
        FROM booking_agent_work_for awf
        JOIN booking_agent ba ON awf.email = ba.email
        LEFT JOIN ticket t
          ON t.booking_agent_email = ba.email
         AND t.airline_name = awf.airline_name
        WHERE awf.airline_name = %s
        GROUP BY ba.email
        ORDER BY revenue_generated DESC, tickets_sold DESC
        """,
        (airline_name,),
    )


def _flight_market_subquery(where_clause):
    return f"""
        SELECT
            f.airline_name,
            f.flight_num,
            f.departure_airport,
            f.arrival_airport,
            f.current_status,
            f.price,
            a.seats,
            COUNT(t.ticket_id) AS tickets_sold,
            COALESCE(SUM(t.sold_price), 0) AS revenue,
            COUNT(t.ticket_id) / a.seats * 100 AS load_factor
        FROM flight_status_view f
        JOIN airplane a
          ON f.airline_name = a.airline_name AND f.airplane_id = a.airplane_id
        {_active_ticket_join()}
        WHERE {where_clause}
        GROUP BY f.airline_name, f.flight_num, f.departure_airport, f.arrival_airport,
                 f.current_status, f.price, a.seats
    """


def _summarize_market(per_flight_sql, params):
    return fetch_one(
        f"""
        SELECT
            COUNT(*) AS total_flights,
            COALESCE(SUM(tickets_sold), 0) AS tickets_sold,
            COALESCE(SUM(revenue), 0) AS revenue,
            COALESCE(ROUND(AVG(load_factor), 2), 0) AS average_load_factor,
            COALESCE(ROUND(AVG(current_status = 'delayed') * 100, 2), 0) AS delay_rate
        FROM ({per_flight_sql}) market
        """,
        params,
    )


def get_city_market_analysis(airline_name, city_input):
    """Analyze one city/alias market for a staff member's airline."""
    airports = resolve_location_to_airports(city_input)
    if not airports:
        return {"city_input": city_input, "airports": [], "summary": {}, "popular_destination": None, "airports_table": []}

    airport_clause = _placeholders(airports)
    where_clause = f"f.airline_name = %s AND (f.departure_airport IN ({airport_clause}) OR f.arrival_airport IN ({airport_clause}))"
    params = [airline_name] + airports + airports
    per_flight = _flight_market_subquery(where_clause)
    summary = _summarize_market(per_flight, params)

    popular_destination = fetch_one(
        f"""
        SELECT f.arrival_airport, COUNT(t.ticket_id) AS tickets_sold
        FROM flight_status_view f
        {_active_ticket_join()}
        WHERE f.airline_name = %s
          AND f.departure_airport IN ({airport_clause})
        GROUP BY f.arrival_airport
        ORDER BY tickets_sold DESC, f.arrival_airport ASC
        LIMIT 1
        """,
        [airline_name] + airports,
    )

    airports_table = fetch_all(
        f"""
        SELECT
            airport,
            COUNT(*) AS flights,
            COALESCE(SUM(tickets_sold), 0) AS tickets_sold,
            COALESCE(SUM(revenue), 0) AS revenue,
            COALESCE(ROUND(AVG(load_factor), 2), 0) AS average_load_factor,
            COALESCE(ROUND(AVG(current_status = 'delayed') * 100, 2), 0) AS delay_rate
        FROM (
            SELECT departure_airport AS airport, market.*
            FROM ({per_flight}) market
            WHERE departure_airport IN ({airport_clause})
            UNION ALL
            SELECT arrival_airport AS airport, market.*
            FROM ({per_flight}) market
            WHERE arrival_airport IN ({airport_clause})
        ) airport_market
        GROUP BY airport
        ORDER BY flights DESC, airport ASC
        """,
        params + airports + params + airports,
    )

    return {
        "city_input": city_input,
        "airports": airports,
        "summary": summary,
        "popular_destination": popular_destination,
        "airports_table": airports_table,
    }


def get_city_pair_market_analysis(airline_name, origin_input, destination_input):
    """Analyze one city-pair market using all airports in each city market."""
    origin_airports = resolve_location_to_airports(origin_input)
    destination_airports = resolve_location_to_airports(destination_input)
    if not origin_airports or not destination_airports:
        return {
            "origin_input": origin_input,
            "destination_input": destination_input,
            "origin_airports": origin_airports,
            "destination_airports": destination_airports,
            "summary": {},
            "cheapest_pair": None,
            "popular_pair": None,
            "pairs_table": [],
        }

    origin_clause = _placeholders(origin_airports)
    destination_clause = _placeholders(destination_airports)
    where_clause = f"f.airline_name = %s AND f.departure_airport IN ({origin_clause}) AND f.arrival_airport IN ({destination_clause})"
    params = [airline_name] + origin_airports + destination_airports
    per_flight = _flight_market_subquery(where_clause)
    summary = _summarize_market(per_flight, params)

    pairs_table = fetch_all(
        f"""
        SELECT
            departure_airport AS origin_airport,
            arrival_airport AS destination_airport,
            COUNT(*) AS flights,
            COALESCE(SUM(tickets_sold), 0) AS tickets_sold,
            COALESCE(SUM(revenue), 0) AS revenue,
            COALESCE(ROUND(AVG(load_factor), 2), 0) AS average_load_factor,
            COALESCE(ROUND(AVG(current_status = 'delayed') * 100, 2), 0) AS delay_rate,
            MIN(price) AS cheapest_price
        FROM ({per_flight}) market
        GROUP BY departure_airport, arrival_airport
        ORDER BY tickets_sold DESC, revenue DESC
        """,
        params,
    )

    cheapest_pair = min(pairs_table, key=lambda row: row["cheapest_price"]) if pairs_table else None
    popular_pair = max(pairs_table, key=lambda row: row["tickets_sold"]) if pairs_table else None
    return {
        "origin_input": origin_input,
        "destination_input": destination_input,
        "origin_airports": origin_airports,
        "destination_airports": destination_airports,
        "summary": summary,
        "cheapest_pair": cheapest_pair,
        "popular_pair": popular_pair,
        "pairs_table": pairs_table,
    }


def get_route_opportunity_alerts(airline_name):
    """Return simple rule-based business alerts for airline routes."""
    alerts = []
    for flight in get_flight_revenue_dashboard(airline_name):
        if flight["load_factor"] >= 90:
            alerts.append({
                "route": flight["route"],
                "message": "High demand route: consider larger aircraft or more frequency.",
            })
        elif flight["load_factor"] < 40:
            alerts.append({
                "route": flight["route"],
                "message": "Low demand route: consider promotion.",
            })

    route_delays = fetch_all(
        """
        SELECT
            CONCAT(departure_airport, ' -> ', arrival_airport) AS route,
            ROUND(AVG(current_status = 'delayed') * 100, 2) AS delay_rate
        FROM flight_status_view
        WHERE airline_name = %s
        GROUP BY departure_airport, arrival_airport
        HAVING delay_rate > 30
        """,
        (airline_name,),
    )
    for route in route_delays:
        alerts.append({
            "route": route["route"],
            "message": "Operational risk: high delay rate.",
        })
    return alerts


def get_disruption_assistant(airline_name, flight_num):
    """Return disrupted flight, affected passengers, and same-city-market alternatives."""
    flight = fetch_one(
        """
        SELECT *
        FROM flight_status_view
        WHERE airline_name = %s AND flight_num = %s
        """,
        (airline_name, flight_num),
    )
    if not flight:
        raise ValueError("Flight was not found.")
    if flight["current_status"] not in {"delayed", "cancelled"}:
        raise ValueError("Disruption assistant is only available for delayed or cancelled flights.")

    passengers = fetch_all(
        """
        SELECT c.email, c.name, t.ticket_id, t.sold_price
        FROM ticket t
        JOIN customer c ON t.customer_email = c.email
        WHERE t.airline_name = %s
          AND t.flight_num = %s
          AND t.ticket_status = 'active'
        ORDER BY c.email
        """,
        (airline_name, flight_num),
    )

    alternatives = fetch_all(
        """
        SELECT alt.*
        FROM flight_status_view alt
        JOIN airport dep_alt ON alt.departure_airport = dep_alt.airport_code
        JOIN airport arr_alt ON alt.arrival_airport = arr_alt.airport_code
        JOIN airport dep_bad ON dep_bad.airport_code = %s
        JOIN airport arr_bad ON arr_bad.airport_code = %s
        WHERE alt.airline_name = %s
          AND alt.current_status = 'upcoming'
          AND dep_alt.city_id = dep_bad.city_id
          AND arr_alt.city_id = arr_bad.city_id
          AND NOT (alt.airline_name = %s AND alt.flight_num = %s)
        ORDER BY alt.departure_time ASC
        """,
        (
            flight["departure_airport"],
            flight["arrival_airport"],
            airline_name,
            airline_name,
            flight_num,
        ),
    )
    return {"flight": flight, "passengers": passengers, "alternatives": alternatives}
