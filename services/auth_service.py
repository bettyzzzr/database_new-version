from pymysql.err import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from db import execute, execute_affected, fetch_all, fetch_one


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


def reset_customer_password(email, passport_number, new_password):
    """Reset a customer password after matching the stored passport number."""
    _require_values(email, passport_number, new_password)
    password_hash = generate_password_hash(new_password)
    affected = execute_affected(
        """
        UPDATE customer
        SET password_hash = %s
        WHERE email = %s AND passport_number = %s
        """,
        (password_hash, email, passport_number),
    )
    if affected == 0:
        raise ValueError("Customer email and passport number did not match.")


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


def get_airlines():
    """Return the standardized airline list for registration and admin forms."""
    return fetch_all(
        """
        SELECT airline_name
        FROM airline
        ORDER BY airline_name
        """
    )


def authenticate_user(role, identifier, password):
    """Verify login credentials and return the session-safe user record."""
    if role == "customer":
        user = fetch_one("SELECT * FROM customer WHERE email = %s", (identifier,))
    elif role == "agent":
        user = fetch_one("SELECT * FROM booking_agent WHERE email = %s", (identifier,))
    elif role == "staff":
        user = fetch_one(
            """
            SELECT *
            FROM airline_staff
            WHERE username = %s OR email = %s
            """,
            (identifier, identifier),
        )
    else:
        return None

    if not user or not check_password_hash(user["password_hash"], password):
        return None
    if role == "staff" and not (user["is_admin"] or user["is_operator"] or user.get("can_delete")):
        raise ValueError(
            "Staff account is pending permissions. Ask a staff member with both admin and operator access to grant access."
        )
    return user
