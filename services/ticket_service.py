from db import execute, fetch_all, fetch_one, get_db
from services.audit_service import log_action
from services.flight_service import get_flight_by_id


def _flight_capacity(airline_name, flight_num):
    """Return seats sold and airplane capacity for a flight."""
    return fetch_one(
        """
        SELECT a.seats, COUNT(t.ticket_id) AS sold
        FROM flight f
        JOIN airplane a ON f.airplane_id = a.airplane_id
        LEFT JOIN ticket t
          ON f.airline_name = t.airline_name
         AND f.flight_num = t.flight_num
         AND t.ticket_status = 'active'
        WHERE f.airline_name = %s AND f.flight_num = %s
        GROUP BY a.seats
        """,
        (airline_name, flight_num),
    )


def _ensure_can_purchase(airline_name, flight_num, requested_seats=1):
    """Enforce upcoming status and capacity before ticket purchases."""
    flight = get_flight_by_id(airline_name, flight_num)
    if not flight:
        raise ValueError("Flight was not found.")
    if flight["current_status"] != "upcoming":
        raise ValueError("Only upcoming flights can be purchased.")

    capacity = _flight_capacity(airline_name, flight_num)
    seats_left = 0 if not capacity else capacity["seats"] - capacity["sold"]
    if seats_left <= 0:
        raise ValueError("This flight is full.")
    if seats_left < requested_seats:
        raise ValueError(f"Only {seats_left} seat(s) left on this flight.")
    return flight


def _parse_customer_emails(customer_emails):
    emails = [
        email.strip().lower()
        for email in (customer_emails or "").split(",")
        if email.strip()
    ]
    if not emails:
        raise ValueError("Enter at least one customer email.")
    if len(set(emails)) != len(emails):
        raise ValueError("Customer emails must be unique.")
    return emails


def _placeholders(values):
    return ", ".join(["%s"] * len(values))


def _ensure_agent_authorized(agent_email, airline_name):
    authorized = fetch_one(
        """
        SELECT 1
        FROM booking_agent_work_for
        WHERE email = %s AND airline_name = %s
        """,
        (agent_email, airline_name),
    )
    if not authorized:
        raise ValueError("This agent is not authorized to sell for that airline.")


def _ensure_customers_exist(customer_emails):
    rows = fetch_all(
        f"""
        SELECT email
        FROM customer
        WHERE email IN ({_placeholders(customer_emails)})
        """,
        customer_emails,
    )
    found = {row["email"].lower() for row in rows}
    missing = [email for email in customer_emails if email not in found]
    if missing:
        raise ValueError(f"Customer account was not found: {', '.join(missing)}.")


def get_seats_left(airline_name, flight_num):
    """Return available seats for a flight."""
    capacity = _flight_capacity(airline_name, flight_num)
    if not capacity:
        return 0
    return max(capacity["seats"] - capacity["sold"], 0)


def validate_customer_purchase(customer_email, airline_name, flight_num):
    """Validate a customer and return the purchasable flight."""
    customer = fetch_one("SELECT email FROM customer WHERE email = %s", (customer_email,))
    if not customer:
        raise ValueError("Customer account was not found.")
    return _ensure_can_purchase(airline_name, flight_num)


def insert_direct_ticket(cursor, customer_email, flight):
    """Insert a direct customer ticket with an existing transaction cursor."""
    cursor.execute(
        """
        INSERT INTO ticket
            (airline_name, flight_num, customer_email, booking_agent_email, sold_price)
        VALUES (%s, %s, %s, NULL, %s)
        """,
        (flight["airline_name"], flight["flight_num"], customer_email, flight["price"]),
    )
    return cursor.lastrowid


def purchase_ticket(customer_email, airline_name, flight_num):
    """Purchase one direct customer ticket after server-side checks."""
    flight = validate_customer_purchase(customer_email, airline_name, flight_num)
    ticket_id = execute(
        """
        INSERT INTO ticket
            (airline_name, flight_num, customer_email, booking_agent_email, sold_price)
        VALUES (%s, %s, %s, NULL, %s)
        """,
        (airline_name, flight_num, customer_email, flight["price"]),
    )
    log_action("customer", customer_email, "purchase", "ticket", str(ticket_id), "")
    return ticket_id


def purchase_ticket_for_agent(agent_email, customer_email, airline_name, flight_num):
    """Purchase one ticket for a customer if the agent represents the airline."""
    return purchase_tickets_for_agent(agent_email, customer_email, airline_name, flight_num)[0]


def purchase_tickets_for_agent(agent_email, customer_emails, airline_name, flight_num):
    """Purchase one ticket per comma-separated customer email for this agent."""
    emails = _parse_customer_emails(customer_emails)
    _ensure_agent_authorized(agent_email, airline_name)
    _ensure_customers_exist(emails)
    flight = _ensure_can_purchase(airline_name, flight_num, len(emails))

    db = get_db()
    ticket_ids = []
    try:
        with db.cursor() as cursor:
            for customer_email in emails:
                cursor.execute(
                    """
                    INSERT INTO ticket
                        (airline_name, flight_num, customer_email, booking_agent_email, sold_price)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (airline_name, flight_num, customer_email, agent_email, flight["price"]),
                )
                ticket_ids.append(cursor.lastrowid)
        db.commit()
    except Exception:
        db.rollback()
        raise

    for ticket_id, customer_email in zip(ticket_ids, emails):
        log_action("agent", agent_email, "purchase", "ticket", str(ticket_id), customer_email)
    return ticket_ids


def get_customer_tickets(customer_email):
    """List all tickets for a customer with dynamic flight status."""
    return fetch_all(
        """
        SELECT t.*, f.departure_airport, f.departure_time, f.arrival_airport,
               f.arrival_time, f.departure_time_utc, f.status, f.current_status
        FROM ticket t
        JOIN flight_status_view f
          ON t.airline_name = f.airline_name AND t.flight_num = f.flight_num
        WHERE t.customer_email = %s
        ORDER BY f.departure_time DESC
        """,
        (customer_email,),
    )


def get_agent_tickets(agent_email):
    """List active tickets sold by a booking agent with dynamic flight status."""
    return fetch_all(
        """
        SELECT t.*, f.departure_airport, f.departure_time, f.arrival_airport,
               f.arrival_time, f.departure_time_utc, f.status, f.current_status
        FROM ticket t
        JOIN flight_status_view f
          ON t.airline_name = f.airline_name AND t.flight_num = f.flight_num
        WHERE t.booking_agent_email = %s
          AND t.ticket_status = 'active'
        ORDER BY t.purchase_date DESC
        """,
        (agent_email,),
    )
