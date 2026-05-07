from pymysql.err import IntegrityError

from db import execute, fetch_all, fetch_one, get_db
from services.audit_service import log_action
from services.flight_service import get_flight_by_id
from services.ticket_service import get_seats_left


def join_waitlist(customer_email, airline_name, flight_num):
    """Join a sold-out flight waitlist once per active customer-flight pair."""
    flight = get_flight_by_id(airline_name, flight_num)
    if not flight:
        raise ValueError("Flight was not found.")
    if flight["current_status"] != "upcoming":
        raise ValueError("Only upcoming flights can be waitlisted.")
    if get_seats_left(airline_name, flight_num) > 0:
        raise ValueError("This flight still has available seats.")

    existing = fetch_one(
        """
        SELECT waitlist_id
        FROM waitlist
        WHERE customer_email = %s
          AND airline_name = %s
          AND flight_num = %s
          AND status IN ('waiting', 'notified')
        """,
        (customer_email, airline_name, flight_num),
    )
    if existing:
        raise ValueError("You are already on the active waitlist for this flight.")

    try:
        waitlist_id = execute(
            """
            INSERT INTO waitlist (customer_email, airline_name, flight_num)
            VALUES (%s, %s, %s)
            """,
            (customer_email, airline_name, flight_num),
        )
    except IntegrityError as exc:
        raise ValueError("You are already on the waitlist for this flight.") from exc

    log_action("customer", customer_email, "waitlist_join", "flight", f"{airline_name}:{flight_num}", "")
    return waitlist_id


def notify_first_waiting_customer(airline_name, flight_num, cursor=None):
    """Mark the earliest waiting customer as notified after a cancellation."""
    if cursor is not None:
        cursor.execute(
            """
            UPDATE waitlist
            SET status = 'notified'
            WHERE airline_name = %s
              AND flight_num = %s
              AND status = 'waiting'
            ORDER BY request_time ASC
            LIMIT 1
            """,
            (airline_name, flight_num),
        )
        return

    db = get_db()
    with db.cursor() as owned_cursor:
        owned_cursor.execute(
            """
            UPDATE waitlist
            SET status = 'notified'
            WHERE airline_name = %s
              AND flight_num = %s
              AND status = 'waiting'
            ORDER BY request_time ASC
            LIMIT 1
            """,
            (airline_name, flight_num),
        )
    db.commit()


def get_customer_waitlist(customer_email):
    """List waitlist rows for the customer."""
    return fetch_all(
        """
        SELECT w.*, f.departure_airport, f.departure_time, f.arrival_airport,
               f.arrival_time, f.current_status
        FROM waitlist w
        JOIN flight_status_view f
          ON w.airline_name = f.airline_name AND w.flight_num = f.flight_num
        WHERE w.customer_email = %s
        ORDER BY w.request_time DESC
        """,
        (customer_email,),
    )
