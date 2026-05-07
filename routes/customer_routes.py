from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services.cart_service import (
    add_to_cart,
    confirm_cart_booking,
    get_cart_flights,
    remove_from_cart,
)
from services.customer_schema_service import ensure_customer_feature_schema
from services.flight_service import search_upcoming_flights
from services.frequent_search_service import get_recent_searches, record_search
from services.itinerary_service import (
    MAX_MULTI_CITY_LEGS,
    confirm_itinerary_booking,
    itinerary_leg_count,
    search_itinerary_options,
)
from services.refund_service import cancel_ticket_for_refund
from services.ticket_service import get_customer_tickets, purchase_ticket
from services.waitlist_service import get_customer_waitlist, join_waitlist
from services.wishlist_service import add_wishlist_item, get_wishlist_items, remove_wishlist_item

customer_bp = Blueprint("customer", __name__, url_prefix="/customer")


def customer_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "customer":
            flash("Customer login is required.", "error")
            return redirect(url_for("auth.login"))
        ensure_customer_feature_schema()
        return view(*args, **kwargs)

    return wrapped


def _flight_search_form():
    return {
        "origin_input": request.form.get("origin", ""),
        "destination_input": request.form.get("destination", ""),
        "departure_date": request.form.get("departure_date") or None,
        "airline": request.form.get("airline", ""),
        "max_price": request.form.get("max_price", ""),
        "available_only": bool(request.form.get("available_only")),
        "sort_by": request.form.get("sort_by", "departure_early"),
    }


def _raw_itinerary_legs(total_legs):
    return [
        {
            "origin": request.form.get(f"leg{index}_origin", ""),
            "destination": request.form.get(f"leg{index}_destination", ""),
            "date": request.form.get(f"leg{index}_date", ""),
        }
        for index in range(1, total_legs + 1)
    ]


@customer_bp.route("/dashboard", methods=["GET", "POST"])
@customer_required
def dashboard():
    flights = []
    if request.method == "POST":
        search = _flight_search_form()
        try:
            flights = search_upcoming_flights(**search)
            record_search(
                session["user_id"],
                search["origin_input"],
                search["destination_input"],
                search["departure_date"],
            )
            if not flights:
                flash("No upcoming flights matched that search.", "error")
        except ValueError as exc:
            flash(str(exc), "error")

    tickets = get_customer_tickets(session["user_id"])
    wishlist = get_wishlist_items(session["user_id"])
    waitlist = get_customer_waitlist(session["user_id"])
    recent_searches = get_recent_searches(session["user_id"])
    return render_template(
        "customer_dashboard.html",
        tickets=tickets,
        flights=flights,
        wishlist=wishlist,
        waitlist=waitlist,
        recent_searches=recent_searches,
    )


@customer_bp.route("/purchase", methods=["POST"])
@customer_required
def purchase():
    try:
        purchase_ticket(
            session["user_id"],
            request.form.get("airline_name", ""),
            request.form.get("flight_num", ""),
        )
        flash("Ticket purchased.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("customer.dashboard"))


@customer_bp.route("/cart")
@customer_required
def cart():
    flights = get_cart_flights(session.get("cart", []))
    return render_template("customer_cart.html", flights=flights)


@customer_bp.route("/cart/add", methods=["POST"])
@customer_required
def cart_add():
    try:
        session["cart"] = add_to_cart(
            session.get("cart", []),
            request.form.get("airline_name", ""),
            request.form.get("flight_num", ""),
        )
        session.modified = True
        flash("Flight added to cart.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(request.referrer or url_for("customer.cart"))


@customer_bp.route("/cart/remove", methods=["POST"])
@customer_required
def cart_remove():
    session["cart"] = remove_from_cart(
        session.get("cart", []),
        request.form.get("airline_name", ""),
        request.form.get("flight_num", ""),
    )
    session.modified = True
    flash("Flight removed from cart.", "success")
    return redirect(url_for("customer.cart"))


@customer_bp.route("/cart/confirm", methods=["POST"])
@customer_required
def cart_confirm():
    try:
        ticket_ids = confirm_cart_booking(session["user_id"], session.get("cart", []))
        session["cart"] = []
        session.modified = True
        flash(f"Cart booked. Ticket ids: {', '.join(map(str, ticket_ids))}.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("customer.cart"))


@customer_bp.route("/cart/clear", methods=["POST"])
@customer_required
def cart_clear():
    session["cart"] = []
    session.modified = True
    flash("Cart cleared.", "success")
    return redirect(url_for("customer.cart"))


@customer_bp.route("/waitlist/join", methods=["POST"])
@customer_required
def waitlist_join():
    try:
        join_waitlist(
            session["user_id"],
            request.form.get("airline_name", ""),
            request.form.get("flight_num", ""),
        )
        flash("You joined the waitlist.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(request.referrer or url_for("customer.dashboard"))


@customer_bp.route("/wishlist/add", methods=["POST"])
@customer_required
def wishlist_add():
    try:
        add_wishlist_item(
            session["user_id"],
            request.form.get("airline_name", ""),
            request.form.get("flight_num", ""),
        )
        flash("Flight added to wishlist.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(request.referrer or url_for("customer.dashboard"))


@customer_bp.route("/wishlist/remove", methods=["POST"])
@customer_required
def wishlist_remove():
    try:
        remove_wishlist_item(session["user_id"], request.form.get("wishlist_id", ""))
        flash("Wishlist item removed.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("customer.dashboard"))


@customer_bp.route("/ticket/cancel", methods=["POST"])
@customer_required
def ticket_cancel():
    try:
        _, refund_amount = cancel_ticket_for_refund(session["user_id"], request.form.get("ticket_id", ""))
        flash(f"Ticket cancelled. Refund requested for ${refund_amount}.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("customer.dashboard"))


@customer_bp.route("/itinerary", methods=["GET", "POST"])
@customer_required
def itinerary():
    legs = []
    booking_type = request.form.get("booking_type", "one_way")
    leg_count = 1
    if request.method == "POST":
        try:
            leg_count = itinerary_leg_count(booking_type, request.form.get("leg_count"))
            legs = search_itinerary_options(booking_type, _raw_itinerary_legs(MAX_MULTI_CITY_LEGS), leg_count)
            if any(not leg["flights"] for leg in legs):
                flash("One or more itinerary legs have no available flights.", "error")
        except ValueError as exc:
            flash(str(exc), "error")
    else:
        leg_count = itinerary_leg_count(booking_type)
    return render_template(
        "customer_itinerary.html",
        legs=legs,
        booking_type=booking_type,
        leg_count=leg_count,
        max_multi_city_legs=MAX_MULTI_CITY_LEGS,
    )


@customer_bp.route("/itinerary/confirm", methods=["POST"])
@customer_required
def itinerary_confirm():
    booking_type = request.form.get("booking_type", "one_way")
    selected = [
        value for key, value in sorted(request.form.items())
        if key.startswith("leg_") and key != "leg_count"
    ]
    try:
        expected_segments = int(request.form.get("leg_count", "0") or 0)
        order_id, total_price = confirm_itinerary_booking(
            session["user_id"],
            booking_type,
            selected,
            expected_segments,
        )
        flash(f"Itinerary booked. Order {order_id}, total ${total_price}.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("customer.itinerary"))
