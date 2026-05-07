from decimal import Decimal
from datetime import date

from db import get_db
from services.audit_service import log_action
from services.ticket_service import insert_direct_ticket, validate_customer_purchase

VALID_BOOKING_TYPES = {"one_way", "round_trip"}


def _is_complete_leg(leg):
    return bool(leg.get("origin") and leg.get("destination") and leg.get("date"))


def _parse_iso_date(value, message):
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(message) from exc


def itinerary_leg_count(booking_type):
    """Return the allowed number of itinerary legs for the selected booking type."""
    if booking_type not in VALID_BOOKING_TYPES:
        raise ValueError("Choose a valid booking type.")

    if booking_type == "one_way":
        return 1
    return 2


def build_itinerary_legs(booking_type, raw_legs):
    """Validate and normalize itinerary leg inputs."""
    required = raw_legs[:itinerary_leg_count(booking_type)]

    if not all(_is_complete_leg(leg) for leg in required):
        raise ValueError("Please fill every required itinerary leg.")

    legs = [
        {
            "index": index,
            "origin": leg["origin"].strip(),
            "destination": leg["destination"].strip(),
            "date": leg["date"],
        }
        for index, leg in enumerate(required, start=1)
    ]
    if booking_type == "round_trip":
        outbound_date = _parse_iso_date(legs[0]["date"], "Enter a valid date for leg 1.")
        return_date = _parse_iso_date(legs[1]["date"], "Enter a valid date for leg 2.")
        if return_date < outbound_date:
            raise ValueError("Round-trip leg 2 date cannot be earlier than leg 1.")
    return legs


def parse_selected_segments(selected_values):
    """Parse selected radio values into airline-flight identifiers."""
    segments = []
    for value in selected_values:
        parts = (value or "").split("|||", 1)
        if len(parts) != 2:
            raise ValueError("Please select one valid flight for each leg.")
        segments.append({"airline_name": parts[0], "flight_num": parts[1]})
    return segments


def confirm_itinerary_booking(customer_email, booking_type, selected_values, expected_segments=None):
    """Create one booking order and one ticket for every selected itinerary leg."""
    if booking_type not in VALID_BOOKING_TYPES:
        raise ValueError("Choose a valid booking type.")

    segments = parse_selected_segments(selected_values)
    if not segments:
        raise ValueError("Please select at least one itinerary flight.")
    if expected_segments and len(segments) != expected_segments:
        raise ValueError("Please select one flight for each itinerary leg.")

    flights = [
        validate_customer_purchase(customer_email, segment["airline_name"], segment["flight_num"])
        for segment in segments
    ]
    total_price = sum((flight["price"] for flight in flights), Decimal("0.00"))

    db = get_db()
    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO booking_order (customer_email, booking_type, total_price)
                VALUES (%s, %s, %s)
                """,
                (customer_email, booking_type, total_price),
            )
            order_id = cursor.lastrowid
            ticket_ids = []
            for index, flight in enumerate(flights, start=1):
                ticket_id = insert_direct_ticket(cursor, customer_email, flight)
                ticket_ids.append(ticket_id)
                cursor.execute(
                    """
                    INSERT INTO booking_order_segment
                        (order_id, segment_index, ticket_id, airline_name, flight_num)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (order_id, index, ticket_id, flight["airline_name"], flight["flight_num"]),
                )
        db.commit()
    except Exception:
        db.rollback()
        raise

    log_action("customer", customer_email, "itinerary_booking", "booking_order", str(order_id), ",".join(map(str, ticket_ids)))
    return order_id, total_price
