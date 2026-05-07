from services.audit_service import log_action
from services.flight_service import get_flight_by_id
from services.ticket_service import get_seats_left, purchase_ticket


def normalize_cart(cart):
    """Return a clean cart list of unique flight identifiers."""
    clean = []
    seen = set()
    for item in cart or []:
        key = (item.get("airline_name"), item.get("flight_num"))
        if all(key) and key not in seen:
            clean.append({"airline_name": key[0], "flight_num": key[1]})
            seen.add(key)
    return clean


def add_to_cart(cart, airline_name, flight_num):
    """Add one flight identifier to the customer session cart."""
    flight = get_flight_by_id(airline_name, flight_num)
    if not flight:
        raise ValueError("Flight was not found.")
    if flight["current_status"] != "upcoming":
        raise ValueError("Only upcoming flights can be added to cart.")

    cart = normalize_cart(cart)
    item = {"airline_name": airline_name, "flight_num": flight_num}
    if item not in cart:
        cart.append(item)
    return cart


def remove_from_cart(cart, airline_name, flight_num):
    """Remove one flight identifier from the customer session cart."""
    return [
        item for item in normalize_cart(cart)
        if item["airline_name"] != airline_name or item["flight_num"] != flight_num
    ]


def get_cart_flights(cart):
    """Fetch current flight details for cart items."""
    flights = []
    for item in normalize_cart(cart):
        flight = get_flight_by_id(item["airline_name"], item["flight_num"])
        if flight:
            flights.append(flight)
    return flights


def confirm_cart_booking(customer_email, cart):
    """Purchase every valid cart flight after a preflight availability check."""
    flights = get_cart_flights(cart)
    if not flights:
        raise ValueError("Your cart is empty.")

    for flight in flights:
        if flight["current_status"] != "upcoming":
            raise ValueError(f"{flight['airline_name']} {flight['flight_num']} is no longer upcoming.")
        if get_seats_left(flight["airline_name"], flight["flight_num"]) <= 0:
            raise ValueError(f"{flight['airline_name']} {flight['flight_num']} is no longer available.")

    ticket_ids = [
        purchase_ticket(customer_email, flight["airline_name"], flight["flight_num"])
        for flight in flights
    ]
    log_action("customer", customer_email, "cart_booking", "ticket", ",".join(map(str, ticket_ids)), "")
    return ticket_ids
