from db import fetch_all, fetch_one
from services.location_service import resolve_location_to_airports


def _placeholders(values):
    return ", ".join(["%s"] * len(values))


def search_upcoming_flights(origin_input, destination_input, departure_date=None):
    """Search upcoming flights using resolved multi-airport city inputs."""
    origin_airports = resolve_location_to_airports(origin_input)
    destination_airports = resolve_location_to_airports(destination_input)
    if not origin_airports or not destination_airports:
        return []

    params = origin_airports + destination_airports
    sql = f"""
        SELECT *
        FROM flight_status_view
        WHERE current_status = 'upcoming'
          AND departure_airport IN ({_placeholders(origin_airports)})
          AND arrival_airport IN ({_placeholders(destination_airports)})
    """
    if departure_date:
        sql += " AND DATE(departure_time) = %s"
        params.append(departure_date)
    sql += " ORDER BY departure_time"
    return fetch_all(sql, params)


def get_flight_status(airline_name, flight_num):
    """Return one flight with dynamic current_status from the SQL view."""
    return fetch_one(
        """
        SELECT *
        FROM flight_status_view
        WHERE airline_name = %s AND flight_num = %s
        """,
        (airline_name, flight_num),
    )


def get_flight_by_id(airline_name, flight_num):
    """Return a flight by composite id using flight_status_view."""
    return get_flight_status(airline_name, flight_num)
