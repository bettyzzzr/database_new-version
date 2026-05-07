from pymysql.err import IntegrityError

from db import execute, fetch_all, fetch_one, get_db
from services.audit_service import log_action
from services.customer_schema_service import ensure_customer_feature_schema
from services.flight_service import get_flight_by_id
from services.ticket_service import get_seats_left


def join_waitlist(customer_email, airline_name, flight_num):
    """Join a sold-out flight waitlist once per active customer-flight pair."""
    ensure_customer_feature_schema()
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
    """Auto-book the earliest waiting customer when a seat is released."""
    ensure_customer_feature_schema()

    def _assign_next_waitlisted_customer(active_cursor):
        active_cursor.execute(
            """
            SELECT waitlist_id, customer_email
            FROM waitlist
            WHERE airline_name = %s
              AND flight_num = %s
              AND status = 'waiting'
            ORDER BY request_time ASC, waitlist_id ASC
            LIMIT 1
            FOR UPDATE
            """,
            (airline_name, flight_num),
        )
        next_customer = active_cursor.fetchone()
        if not next_customer:
            return None

        active_cursor.execute(
            """
            SELECT f.airline_name, f.flight_num, f.price, f.current_status
            FROM flight_status_view f
            WHERE f.airline_name = %s AND f.flight_num = %s
            """,
            (airline_name, flight_num),
        )
        flight = active_cursor.fetchone()
        if not flight or flight["current_status"] != "upcoming":
            return None

        active_cursor.execute(
            """
            SELECT a.seats, COUNT(t.ticket_id) AS sold
            FROM flight f
            JOIN airplane a
              ON f.airline_name = a.airline_name AND f.airplane_id = a.airplane_id
            LEFT JOIN ticket t
              ON f.airline_name = t.airline_name
             AND f.flight_num = t.flight_num
             AND t.ticket_status = 'active'
            WHERE f.airline_name = %s AND f.flight_num = %s
            GROUP BY a.seats
            """,
            (airline_name, flight_num),
        )
        capacity = active_cursor.fetchone()
        if not capacity or capacity["sold"] >= capacity["seats"]:
            return None

        active_cursor.execute(
            """
            INSERT INTO ticket
                (airline_name, flight_num, customer_email, booking_agent_email, sold_price)
            VALUES (%s, %s, %s, NULL, %s)
            """,
            (flight["airline_name"], flight["flight_num"], next_customer["customer_email"], flight["price"]),
        )
        ticket_id = active_cursor.lastrowid
        active_cursor.execute(
            """
            UPDATE waitlist
            SET status = 'converted'
            WHERE waitlist_id = %s
            """,
            (next_customer["waitlist_id"],),
        )
        return {
            "waitlist_id": next_customer["waitlist_id"],
            "customer_email": next_customer["customer_email"],
            "ticket_id": ticket_id,
        }

    if cursor is not None:
        return _assign_next_waitlisted_customer(cursor)

    db = get_db()
    try:
        with db.cursor() as owned_cursor:
            assigned = _assign_next_waitlisted_customer(owned_cursor)
        db.commit()
    except Exception:
        db.rollback()
        raise

    if assigned:
        log_action(
            "system",
            "waitlist_auto_assign",
            "waitlist_convert",
            "ticket",
            str(assigned["ticket_id"]),
            f"{airline_name}:{flight_num}:{assigned['customer_email']}",
        )
    return assigned


def get_customer_waitlist(customer_email):
    """List waitlist rows for the customer."""
    ensure_customer_feature_schema()
    return fetch_all(
        """
        SELECT w.*, f.departure_airport, f.departure_time, f.arrival_airport,
               f.arrival_time, f.current_status,
               CASE
                   WHEN w.status IN ('waiting', 'notified') THEN (
                       SELECT COUNT(*)
                       FROM waitlist w2
                       WHERE w2.airline_name = w.airline_name
                         AND w2.flight_num = w.flight_num
                         AND w2.status IN ('waiting', 'notified')
                         AND (
                             w2.request_time < w.request_time
                             OR (w2.request_time = w.request_time AND w2.waitlist_id <= w.waitlist_id)
                         )
                   )
                   ELSE NULL
               END AS waitlist_position
        FROM waitlist w
        JOIN flight_status_view f
          ON w.airline_name = f.airline_name AND w.flight_num = f.flight_num
        WHERE w.customer_email = %s
        ORDER BY w.request_time DESC
        """,
        (customer_email,),
    )
