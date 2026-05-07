from decimal import Decimal

from db import fetch_one, get_db
from services.audit_service import log_action
from services.customer_schema_service import ensure_customer_feature_schema
from services.waitlist_service import notify_first_waiting_customer


def cancel_ticket_for_refund(customer_email, ticket_id):
    """Cancel an eligible customer ticket and create an 80 percent refund request."""
    ensure_customer_feature_schema()
    ticket = fetch_one(
        """
        SELECT t.*, f.departure_time_utc,
               TIMESTAMPDIFF(HOUR, UTC_TIMESTAMP(), f.departure_time_utc) AS hours_until_departure
        FROM ticket t
        JOIN flight_status_view f
          ON t.airline_name = f.airline_name AND t.flight_num = f.flight_num
        WHERE t.ticket_id = %s AND t.customer_email = %s
        """,
        (ticket_id, customer_email),
    )
    if not ticket:
        raise ValueError("Ticket was not found for this customer.")
    if ticket["ticket_status"] == "cancelled":
        raise ValueError("This ticket is already cancelled.")
    if ticket["hours_until_departure"] is None or ticket["hours_until_departure"] <= 24:
        raise ValueError("Tickets can only be cancelled more than 24 hours before departure.")

    refund_amount = (ticket["sold_price"] * Decimal("0.80")).quantize(Decimal("0.01"))
    db = get_db()
    auto_assigned = None
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "UPDATE ticket SET ticket_status = 'cancelled' WHERE ticket_id = %s",
                (ticket_id,),
            )
            cursor.execute(
                """
                INSERT INTO refund (ticket_id, refund_amount, refund_status)
                VALUES (%s, %s, 'requested')
                """,
                (ticket_id, refund_amount),
            )
            refund_id = cursor.lastrowid
            auto_assigned = notify_first_waiting_customer(ticket["airline_name"], ticket["flight_num"], cursor)
        db.commit()
    except Exception:
        db.rollback()
        raise

    log_action("customer", customer_email, "refund_request", "ticket", str(ticket_id), str(refund_amount))
    if auto_assigned:
        log_action(
            "system",
            "waitlist_auto_assign",
            "waitlist_convert",
            "ticket",
            str(auto_assigned["ticket_id"]),
            f"{ticket['airline_name']}:{ticket['flight_num']}:{auto_assigned['customer_email']}",
        )
    return refund_id, refund_amount
