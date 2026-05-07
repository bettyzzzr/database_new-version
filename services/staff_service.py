from datetime import datetime, timedelta

from pymysql.err import IntegrityError

from db import execute, execute_affected, fetch_all, fetch_one
from services.audit_service import log_action
from services.location_service import resolve_location_to_airports


def _require_admin(staff):
    if not staff.get("is_admin"):
        raise PermissionError("Admin staff permission is required.")


def _require_operator(staff):
    if not staff.get("is_operator"):
        raise PermissionError("Operator staff permission is required.")


def _require_values(*values):
    if any(str(value or "").strip() == "" for value in values):
        raise ValueError("Please fill in all required fields.")


def _get_or_create_city(city_name):
    city = fetch_one("SELECT city_id FROM city WHERE LOWER(city_name) = LOWER(%s)", (city_name,))
    if city:
        return city["city_id"]
    return execute("INSERT INTO city (city_name) VALUES (%s)", (city_name,))


def _mysql_datetime(value):
    return value.replace("T", " ")


def _parse_datetime(value):
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Time must be a valid date and time.") from exc


def _format_datetime(value):
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _resolve_single_airport(location_input, field_name):
    airports = resolve_location_to_airports(location_input)
    if not airports:
        raise ValueError(f"{field_name} airport was not found.")
    if len(airports) > 1:
        raise ValueError(f"{field_name} must resolve to one airport. Use a specific airport code.")
    return airports[0]


def _airport_timezone_offset(airport_code):
    timezone = fetch_one(
        """
        SELECT tz.utc_offset_minutes
        FROM airport a
        JOIN airport_timezone tz ON a.timezone_name = tz.timezone_name
        WHERE a.airport_code = %s
        """,
        (airport_code,),
    )
    if not timezone:
        raise ValueError(f"Timezone is missing for airport {airport_code}.")
    return timezone["utc_offset_minutes"]


def _airport_local_to_utc(local_time, airport_code):
    offset = _airport_timezone_offset(airport_code)
    local_dt = _parse_datetime(local_time)
    return _format_datetime(local_dt - timedelta(minutes=offset))


def get_timezones():
    """Return available airport timezones for admin forms."""
    return fetch_all(
        """
        SELECT timezone_name, display_name
        FROM airport_timezone
        ORDER BY display_name
        """
    )


def add_airport(staff, airport_code, airport_name, city_name, timezone_name):
    """Allow admin staff to add an airport under a city."""
    _require_admin(staff)
    _require_values(airport_code, airport_name, city_name, timezone_name)
    city_id = _get_or_create_city(city_name)
    try:
        execute(
            """
            INSERT INTO airport (airport_code, airport_name, city_id, timezone_name)
            VALUES (UPPER(%s), %s, %s, %s)
            """,
            (airport_code, airport_name, city_id, timezone_name),
        )
    except IntegrityError as exc:
        raise ValueError("Airport code already exists, city is invalid, or timezone is invalid.") from exc
    log_action("staff", staff["username"], "add_airport", "airport", airport_code.upper(), "")


def add_city(staff, city_name):
    """Allow admin staff to add a city."""
    _require_admin(staff)
    _require_values(city_name)
    try:
        city_id = execute("INSERT INTO city (city_name) VALUES (%s)", (city_name,))
    except IntegrityError as exc:
        raise ValueError("City already exists.") from exc
    log_action("staff", staff["username"], "add_city", "city", str(city_id), city_name)
    return city_id


def add_city_alias(staff, city_name, alias_name):
    """Allow admin staff to add a city alias as structured data."""
    _require_admin(staff)
    _require_values(city_name, alias_name)
    city_id = _get_or_create_city(city_name)
    try:
        alias_id = execute(
            """
            INSERT INTO city_alias (city_id, alias_name)
            VALUES (%s, %s)
            """,
            (city_id, alias_name),
        )
    except IntegrityError as exc:
        raise ValueError("City alias already exists.") from exc
    log_action("staff", staff["username"], "add_alias", "city_alias", str(alias_id), f"{city_name}:{alias_name}")
    return alias_id


def add_airplane(staff, airplane_id, seats):
    """Allow admin staff to add an airplane for their own airline."""
    _require_admin(staff)
    _require_values(airplane_id, seats)
    if int(seats) <= 0:
        raise ValueError("Seat capacity must be positive.")
    try:
        execute(
            """
            INSERT INTO airplane (airplane_id, airline_name, seats)
            VALUES (%s, %s, %s)
            """,
            (airplane_id, staff["airline_name"], seats),
        )
    except IntegrityError as exc:
        raise ValueError("Airplane id already exists.") from exc
    log_action("staff", staff["username"], "add_airplane", "airplane", str(airplane_id), "")


def create_flight(staff, flight_num, departure_airport, departure_time,
                  arrival_airport, arrival_time, price, airplane_id):
    """Allow admin staff to create a scheduled flight for their own airline."""
    _require_admin(staff)
    _require_values(
        flight_num, departure_airport, departure_time,
        arrival_airport, arrival_time, price, airplane_id,
    )
    departure_airport = _resolve_single_airport(departure_airport, "Departure")
    arrival_airport = _resolve_single_airport(arrival_airport, "Arrival")
    departure_time_utc = _airport_local_to_utc(departure_time, departure_airport)
    arrival_time_utc = _airport_local_to_utc(arrival_time, arrival_airport)
    if datetime.fromisoformat(arrival_time_utc) <= datetime.fromisoformat(departure_time_utc):
        raise ValueError("Arrival UTC time must be after departure UTC time.")

    airplane = fetch_one(
        "SELECT 1 FROM airplane WHERE airplane_id = %s AND airline_name = %s",
        (airplane_id, staff["airline_name"]),
    )
    if not airplane:
        raise ValueError("Airplane must belong to your airline.")

    try:
        execute(
            """
            INSERT INTO flight
                (airline_name, flight_num, departure_airport, departure_time,
                 departure_time_utc, arrival_airport, arrival_time, arrival_time_utc,
                 price, status, airplane_id)
            VALUES (%s, %s, UPPER(%s), %s, %s, UPPER(%s), %s, %s, %s, 'scheduled', %s)
            """,
            (
                staff["airline_name"],
                flight_num,
                departure_airport,
                _mysql_datetime(departure_time),
                departure_time_utc,
                arrival_airport,
                _mysql_datetime(arrival_time),
                arrival_time_utc,
                price, airplane_id,
            ),
        )
    except IntegrityError as exc:
        raise ValueError("Flight could not be created. Check flight number and airports.") from exc
    log_action("staff", staff["username"], "create_flight", "flight", flight_num, staff["airline_name"])


def associate_agent_with_airline(staff, agent_email):
    """Allow admin staff to authorize an agent for their own airline."""
    _require_admin(staff)
    _require_values(agent_email)
    try:
        execute(
            """
            INSERT INTO booking_agent_work_for (email, airline_name)
            VALUES (%s, %s)
            """,
            (agent_email, staff["airline_name"]),
        )
    except IntegrityError as exc:
        raise ValueError("Agent does not exist or is already associated.") from exc
    log_action("staff", staff["username"], "associate_agent", "agent", agent_email, staff["airline_name"])


def update_flight_status(staff, flight_num, status):
    """Allow operator staff to set only staff-controlled operational statuses."""
    _require_operator(staff)
    _require_values(flight_num, status)
    if status not in {"scheduled", "delayed", "cancelled"}:
        raise ValueError("Status must be scheduled, delayed, or cancelled.")

    affected = execute_affected(
        """
        UPDATE flight
        SET status = %s
        WHERE airline_name = %s AND flight_num = %s
        """,
        (status, staff["airline_name"], flight_num),
    )
    if affected == 0:
        raise ValueError("Flight was not found for your airline.")
    log_action("staff", staff["username"], "update_status", "flight", flight_num, status)


def get_passenger_list(staff, flight_num):
    """List passengers for a flight operated by the staff member's airline."""
    return fetch_all(
        """
        SELECT c.email, c.name, t.ticket_id, t.booking_agent_email, t.purchase_date
        FROM ticket t
        JOIN customer c ON t.customer_email = c.email
        WHERE t.airline_name = %s AND t.flight_num = %s
        ORDER BY c.email
        """,
        (staff["airline_name"], flight_num),
    )


def get_city_airport_alias_mapping():
    """Return cities with their airports and aliases."""
    return fetch_all(
        """
        SELECT
            c.city_name,
            a.airport_code,
            a.airport_name,
            a.timezone_name,
            COALESCE(GROUP_CONCAT(ca.alias_name ORDER BY ca.alias_name SEPARATOR ', '), '') AS aliases
        FROM city c
        LEFT JOIN airport a ON c.city_id = a.city_id
        LEFT JOIN city_alias ca ON c.city_id = ca.city_id
        GROUP BY c.city_name, a.airport_code, a.airport_name, a.timezone_name
        ORDER BY c.city_name, a.airport_code
        """
    )


def get_staff_flights(airline_name):
    """List airline flights using dynamic flight_status_view statuses."""
    return fetch_all(
        """
        SELECT *
        FROM flight_status_view
        WHERE airline_name = %s
        ORDER BY departure_time DESC
        """,
        (airline_name,),
    )
