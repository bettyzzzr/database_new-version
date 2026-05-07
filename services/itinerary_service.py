from decimal import Decimal

from db import get_db
from services.audit_service import log_action
from services.flight_service import search_upcoming_flights
from services.ticket_service import insert_direct_ticket, validate_customer_purchase

VALID_BOOKING_TYPES = {"one_way", "round_trip", "multi_city"}


def _is_complete_leg(leg):
    return bool(leg.get("origin") and leg.get("destination") and leg.get("date"))


def build_itinerary_legs(booking_type, raw_legs):
    """Validate and normalize itinerary leg inputs."""
    if booking_type not in VALID_BOOKING_TYPES:
        raise ValueError("Choose a valid booking type.")

    if booking_type == "one_way":
        required = raw_legs[:1]
    elif booking_type == "round_trip":
        required = raw_legs[:2]
    else:
        required = raw_legs[:2]
        if any(raw_legs[2].values()):
            required.append(raw_legs[2])

    if not all(_is_complete_leg(leg) for leg in required):
        raise ValueError("Please fill every required itinerary leg.")

    return [
        {
            "index": index,
            "origin": leg["origin"],
            "destination": leg["destination"],
            "date": leg["date"],
        }
        for index, leg in enumerate(required, start=1)
    ]


def search_itinerary_options(booking_type, raw_legs):
    """Search available flight options for each itinerary leg."""
    legs = build_itinerary_legs(booking_type, raw_legs)
    for leg in legs:
        leg["flights"] = search_upcoming_flights(
            leg["origin"],
            leg["destination"],
            leg["date"],
            available_only=True,
            sort_by="departure_early",
        )
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
