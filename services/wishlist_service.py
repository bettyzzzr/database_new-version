from pymysql.err import IntegrityError

from db import execute, execute_affected, fetch_all
from services.audit_service import log_action
from services.flight_service import get_flight_by_id


def add_wishlist_item(customer_email, airline_name, flight_num):
    """Add an upcoming flight to the customer's wishlist."""
    flight = get_flight_by_id(airline_name, flight_num)
    if not flight:
        raise ValueError("Flight was not found.")
    if flight["current_status"] != "upcoming":
        raise ValueError("Only upcoming flights can be added to wishlist.")

    try:
        wishlist_id = execute(
            """
            INSERT INTO wishlist (customer_email, airline_name, flight_num)
            VALUES (%s, %s, %s)
            """,
            (customer_email, airline_name, flight_num),
        )
    except IntegrityError as exc:
        raise ValueError("This flight is already on your wishlist.") from exc

    log_action("customer", customer_email, "wishlist_add", "flight", f"{airline_name}:{flight_num}", "")
    return wishlist_id


def remove_wishlist_item(customer_email, wishlist_id):
    """Remove a wishlist item owned by the customer."""
    affected = execute_affected(
        """
        DELETE FROM wishlist
        WHERE wishlist_id = %s AND customer_email = %s
        """,
        (wishlist_id, customer_email),
    )
    if not affected:
        raise ValueError("Wishlist item was not found.")
    log_action("customer", customer_email, "wishlist_remove", "wishlist", str(wishlist_id), "")


def get_wishlist_items(customer_email):
    """List the customer's wishlist with current flight status."""
    return fetch_all(
        """
        SELECT w.*, f.departure_airport, f.departure_time, f.arrival_airport,
               f.arrival_time, f.price, f.current_status
        FROM wishlist w
        JOIN flight_status_view f
          ON w.airline_name = f.airline_name AND w.flight_num = f.flight_num
        WHERE w.customer_email = %s
        ORDER BY w.created_at DESC
        """,
        (customer_email,),
    )
