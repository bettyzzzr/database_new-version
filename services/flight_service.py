from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from functools import lru_cache

from db import fetch_all, fetch_one
from services.location_service import resolve_location_to_airports

SORT_OPTIONS = {
    "departure_early": "f.departure_time ASC",
    "departure_late": "f.departure_time DESC",
    "price_low": "f.price ASC",
    "price_high": "f.price DESC",
    "seats_left": "seats_left DESC",
    "duration_short": "duration_minutes ASC",
}

PRICE_CALENDAR_DAY_OPTIONS = {7, 14, 30, 60}


def _placeholders(values):
    return ", ".join(["%s"] * len(values))


@lru_cache(maxsize=1)
def _ticket_has_status_column():
    return bool(fetch_one("SHOW COLUMNS FROM ticket LIKE 'ticket_status'"))


def _clean_text(value):
    return (value or "").strip()


def _has_search_filters(
    origin_input,
    destination_input,
    departure_date,
    airline,
    max_price,
    available_only,
):
    return any(
        [
            origin_input,
            destination_input,
            departure_date,
            airline,
            str(max_price).strip() if max_price is not None else "",
            available_only,
        ]
    )


def _flight_capacity_join():
    status_filter = "WHERE ticket_status = 'active'" if _ticket_has_status_column() else ""
    return """
        JOIN airplane a
          ON f.airline_name = a.airline_name AND f.airplane_id = a.airplane_id
        LEFT JOIN (
            SELECT airline_name, flight_num, COUNT(*) AS active_tickets
            FROM ticket
            {status_filter}
            GROUP BY airline_name, flight_num
        ) tc
          ON f.airline_name = tc.airline_name AND f.flight_num = tc.flight_num
    """.format(status_filter=status_filter)


def _flight_select():
    return """
        SELECT f.*,
               TIMESTAMPDIFF(MINUTE, f.departure_time, f.arrival_time) AS duration_minutes,
               a.seats - COALESCE(tc.active_tickets, 0) AS seats_left
        FROM flight_status_view f
    """


def _add_recommendation_labels(flights):
    if not flights:
        return flights

    cheapest = min(flights, key=lambda flight: flight["price"])["price"]
    earliest = min(flights, key=lambda flight: flight["departure_time"])["departure_time"]
    for flight in flights:
        seats_left = flight["seats_left"]
        if seats_left <= 0:
            label = "Sold Out"
        elif flight["price"] == cheapest:
            label = "Best Price"
        elif flight["departure_time"] == earliest:
            label = "Earliest"
        elif seats_left <= 3:
            label = "Almost Full"
        elif seats_left <= 10:
            label = "Selling Fast"
        else:
            label = "Available"
        flight["recommendation_label"] = label
    return flights


def _normalize_max_price(max_price):
    if max_price is None or str(max_price).strip() == "":
        return None
    try:
        value = Decimal(str(max_price))
    except InvalidOperation as exc:
        raise ValueError("Maximum price must be a valid number.") from exc
    if value < 0:
        raise ValueError("Maximum price cannot be negative.")
    return value


def _parse_calendar_start_date(value):
    if not value:
        return date.today()
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Enter a valid calendar start date.") from exc


def _normalize_calendar_days(days):
    try:
        value = int(days or 30)
    except (TypeError, ValueError) as exc:
        raise ValueError("Choose a valid calendar range.") from exc
    if value not in PRICE_CALENDAR_DAY_OPTIONS:
        raise ValueError("Choose a valid calendar range.")
    return value


def _calendar_row_date(value):
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def search_upcoming_flights(
    origin_input,
    destination_input,
    departure_date=None,
    airline=None,
    max_price=None,
    available_only=False,
    sort_by="departure_early",
):
    """Search upcoming flights using resolved multi-airport city inputs."""
    origin_input = _clean_text(origin_input)
    destination_input = _clean_text(destination_input)
    airline = _clean_text(airline)
    if not _has_search_filters(
        origin_input,
        destination_input,
        departure_date,
        airline,
        max_price,
        available_only,
    ):
        raise ValueError("Enter at least one search field before searching.")

    origin_airports = resolve_location_to_airports(origin_input) if origin_input else []
    destination_airports = resolve_location_to_airports(destination_input) if destination_input else []
    if origin_input and not origin_airports:
        return []
    if destination_input and not destination_airports:
        return []

    max_price = _normalize_max_price(max_price)
    params = []
    sql = f"""
        {_flight_select()}
        {_flight_capacity_join()}
        WHERE current_status = 'upcoming'
    """
    if origin_airports:
        sql += f" AND departure_airport IN ({_placeholders(origin_airports)})"
        params.extend(origin_airports)
    if destination_airports:
        sql += f" AND arrival_airport IN ({_placeholders(destination_airports)})"
        params.extend(destination_airports)
    if departure_date:
        sql += " AND DATE(departure_time) = %s"
        params.append(departure_date)
    if airline:
        sql += " AND f.airline_name = %s"
        params.append(airline)
    if max_price is not None:
        sql += " AND f.price <= %s"
        params.append(max_price)
    if available_only:
        sql += " AND a.seats - COALESCE(tc.active_tickets, 0) > 0"

    order_by = SORT_OPTIONS.get(sort_by, SORT_OPTIONS["departure_early"])
    sql += f" ORDER BY {order_by}, f.airline_name ASC, f.flight_num ASC"
    return _add_recommendation_labels(fetch_all(sql, params))


def get_lowest_price_calendar(
    origin_input,
    destination_input,
    start_date=None,
    days=30,
    airline=None,
    max_price=None,
    available_only=True,
):
    """Return the lowest upcoming flight price for each day in a date window."""
    origin_input = _clean_text(origin_input)
    destination_input = _clean_text(destination_input)
    airline = _clean_text(airline)
    if not origin_input or not destination_input:
        raise ValueError("Enter both origin and destination to view the price calendar.")

    origin_airports = resolve_location_to_airports(origin_input)
    destination_airports = resolve_location_to_airports(destination_input)
    if not origin_airports or not destination_airports:
        return []

    start = _parse_calendar_start_date(start_date)
    day_count = _normalize_calendar_days(days)
    end = start + timedelta(days=day_count)
    max_price = _normalize_max_price(max_price)

    params = []
    sql = f"""
        SELECT
            DATE(f.departure_time) AS travel_date,
            MIN(f.price) AS lowest_price,
            COUNT(*) AS flight_count,
            MAX(a.seats - COALESCE(tc.active_tickets, 0)) AS best_seats_left
        FROM flight_status_view f
        {_flight_capacity_join()}
        WHERE current_status = 'upcoming'
          AND departure_airport IN ({_placeholders(origin_airports)})
          AND arrival_airport IN ({_placeholders(destination_airports)})
          AND DATE(f.departure_time) >= %s
          AND DATE(f.departure_time) < %s
    """
    params.extend(origin_airports)
    params.extend(destination_airports)
    params.extend([start, end])
    if airline:
        sql += " AND f.airline_name = %s"
        params.append(airline)
    if max_price is not None:
        sql += " AND f.price <= %s"
        params.append(max_price)
    if available_only:
        sql += " AND a.seats - COALESCE(tc.active_tickets, 0) > 0"
    sql += " GROUP BY DATE(f.departure_time) ORDER BY travel_date ASC"

    prices_by_date = {_calendar_row_date(row["travel_date"]): row for row in fetch_all(sql, params)}
    calendar = []
    for offset in range(day_count):
        travel_date = start + timedelta(days=offset)
        row = prices_by_date.get(travel_date)
        calendar.append(
            {
                "travel_date": travel_date,
                "lowest_price": row["lowest_price"] if row else None,
                "flight_count": row["flight_count"] if row else 0,
                "best_seats_left": row["best_seats_left"] if row else 0,
            }
        )
    return calendar


def search_flight_statuses(airline_name="", flight_num=""):
    """Search flight statuses by airline, flight number, or both."""
    airline_name = _clean_text(airline_name)
    flight_num = _clean_text(flight_num)
    if not airline_name and not flight_num:
        raise ValueError("Enter at least one search field before checking flight status.")

    params = []
    sql = f"""
        {_flight_select()}
        {_flight_capacity_join()}
        WHERE 1 = 1
    """
    if airline_name:
        sql += " AND LOWER(f.airline_name) = LOWER(%s)"
        params.append(airline_name)
    if flight_num:
        sql += " AND LOWER(f.flight_num) = LOWER(%s)"
        params.append(flight_num)
    sql += " ORDER BY f.departure_time ASC, f.airline_name ASC, f.flight_num ASC"
    return fetch_all(sql, params)


def get_flight_status(airline_name, flight_num):
    """Return one flight with dynamic current_status from the SQL view."""
    return fetch_one(
        f"""
        {_flight_select()}
        {_flight_capacity_join()}
        WHERE f.airline_name = %s AND f.flight_num = %s
        """,
        (airline_name, flight_num),
    )


def get_flight_by_id(airline_name, flight_num):
    """Return a flight by composite id using flight_status_view."""
    return get_flight_status(airline_name, flight_num)
