from pymysql.err import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from db import execute, fetch_one


def _require_values(*values):
    if any(str(value or "").strip() == "" for value in values):
        raise ValueError("Please fill in all required fields for this account type.")


def register_customer(email, name, password, passport_number, passport_expiration, passport_country):
    """Create a customer account with passport details and a hashed password."""
    _require_values(email, name, password, passport_number, passport_expiration, passport_country)
    password_hash = generate_password_hash(password)
    try:
        execute(
            """
            INSERT INTO customer
                (email, name, password_hash, passport_number, passport_expiration, passport_country)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (email, name, password_hash, passport_number, passport_expiration, passport_country),
        )
    except IntegrityError as exc:
        raise ValueError("A customer with this email or passport already exists.") from exc


def _next_booking_agent_id():
    record = fetch_one(
        "SELECT COALESCE(MAX(booking_agent_id), 500) + 1 AS next_id FROM booking_agent"
    )
    return record["next_id"]


def register_agent(email, name, password):
    """Create a booking agent account with a generated unique agent id."""
    _require_values(email, name, password)
    password_hash = generate_password_hash(password)
    try:
        execute(
            """
            INSERT INTO booking_agent (email, name, booking_agent_id, password_hash)
            VALUES (%s, %s, %s, %s)
            """,
            (email, name, _next_booking_agent_id(), password_hash),
        )
    except IntegrityError as exc:
        raise ValueError("A booking agent with this email already exists.") from exc


def register_staff(email, username, password, first_name, last_name, airline_name):
    """Create a regular airline staff account without admin/operator privileges."""
    _require_values(email, username, password, first_name, last_name, airline_name)
    password_hash = generate_password_hash(password)
    try:
        execute(
            """
            INSERT INTO airline_staff
                (email, username, password_hash, first_name, last_name, airline_name)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (email, username, password_hash, first_name, last_name, airline_name),
        )
    except IntegrityError as exc:
        raise ValueError("Staff email/username exists or airline is invalid.") from exc


def authenticate_user(role, identifier, password):
    """Verify login credentials and return the session-safe user record."""
    if role == "customer":
        user = fetch_one("SELECT * FROM customer WHERE email = %s", (identifier,))
    elif role == "agent":
        user = fetch_one("SELECT * FROM booking_agent WHERE email = %s", (identifier,))
    elif role == "staff":
        user = fetch_one("SELECT * FROM airline_staff WHERE username = %s", (identifier,))
    else:
        return None

    if not user or not check_password_hash(user["password_hash"], password):
        return None
    return user
