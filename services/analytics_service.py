from db import fetch_all, fetch_one
from services.location_service import resolve_location_to_airports


def _placeholders(values):
    return ", ".join(["%s"] * len(values))


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
