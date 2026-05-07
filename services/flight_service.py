from decimal import Decimal, InvalidOperation

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


def _placeholders(values):
    return ", ".join(["%s"] * len(values))


def _flight_capacity_join():
    return """
        JOIN airplane a
          ON f.airline_name = a.airline_name AND f.airplane_id = a.airplane_id
        LEFT JOIN (
            SELECT airline_name, flight_num, COUNT(*) AS active_tickets
            FROM ticket
            WHERE ticket_status = 'active'
            GROUP BY airline_name, flight_num
        ) tc
          ON f.airline_name = tc.airline_name AND f.flight_num = tc.flight_num
    """


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
    if not max_price:
        return None
    try:
        value = Decimal(str(max_price))
    except InvalidOperation as exc:
        raise ValueError("Maximum price must be a valid number.") from exc
    if value < 0:
        raise ValueError("Maximum price cannot be negative.")
    return value


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
    origin_airports = resolve_location_to_airports(origin_input)
    destination_airports = resolve_location_to_airports(destination_input)
    if not origin_airports or not destination_airports:
        return []

    max_price = _normalize_max_price(max_price)
    params = origin_airports + destination_airports
    sql = f"""
        {_flight_select()}
        {_flight_capacity_join()}
        WHERE current_status = 'upcoming'
          AND departure_airport IN ({_placeholders(origin_airports)})
          AND arrival_airport IN ({_placeholders(destination_airports)})
    """
    if departure_date:
        sql += " AND DATE(departure_time) = %s"
        params.append(departure_date)
    if airline:
        sql += " AND f.airline_name = %s"
        params.append(airline)
    if max_price:
        sql += " AND f.price <= %s"
        params.append(max_price)
    if available_only:
        sql += " AND a.seats - COALESCE(tc.active_tickets, 0) > 0"

    order_by = SORT_OPTIONS.get(sort_by, SORT_OPTIONS["departure_early"])
    sql += f" ORDER BY {order_by}, f.airline_name ASC, f.flight_num ASC"
    return _add_recommendation_labels(fetch_all(sql, params))


def get_flight_status(airline_name, flight_num):
    """Return one flight with dynamic current_status from the SQL view."""
    return fetch_one(
        """
        SELECT f.*,
               TIMESTAMPDIFF(MINUTE, f.departure_time, f.arrival_time) AS duration_minutes,
               a.seats - COALESCE(tc.active_tickets, 0) AS seats_left
        FROM flight_status_view f
        JOIN airplane a
          ON f.airline_name = a.airline_name AND f.airplane_id = a.airplane_id
        LEFT JOIN (
            SELECT airline_name, flight_num, COUNT(*) AS active_tickets
            FROM ticket
            WHERE ticket_status = 'active'
            GROUP BY airline_name, flight_num
        ) tc
          ON f.airline_name = tc.airline_name AND f.flight_num = tc.flight_num
        WHERE f.airline_name = %s AND f.flight_num = %s
        """,
        (airline_name, flight_num),
    )


def get_flight_by_id(airline_name, flight_num):
    """Return a flight by composite id using flight_status_view."""
    return get_flight_status(airline_name, flight_num)
