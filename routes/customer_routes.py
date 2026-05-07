from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services.cart_service import (
    add_to_cart,
    confirm_cart_booking,
    get_cart_flights,
    remove_from_cart,
)
from services.analytics_service import get_customer_custom_spending, get_customer_default_spending
from services.customer_schema_service import ensure_customer_feature_schema
from services.flight_service import search_upcoming_flights
from services.frequent_search_service import get_recent_searches, record_search
from services.itinerary_service import confirm_itinerary_booking
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


@customer_bp.route("/dashboard", methods=["GET", "POST"])
@customer_required
def dashboard():
    flights = []
    spending_default = get_customer_default_spending(session["user_id"])
    spending_custom = None
    custom_start_date = request.args.get("spending_start_date", "")
    custom_end_date = request.args.get("spending_end_date", "")
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
    if custom_start_date or custom_end_date:
        try:
            if not custom_start_date or not custom_end_date:
                raise ValueError("Choose both a start date and end date for custom spending analytics.")
            spending_custom = get_customer_custom_spending(session["user_id"], custom_start_date, custom_end_date)
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
        spending_default=spending_default,
        spending_custom=spending_custom,
        custom_start_date=custom_start_date,
        custom_end_date=custom_end_date,
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


@customer_bp.route("/round-trip/confirm", methods=["POST"])
@customer_required
def round_trip_confirm():
    selected = [
        value for key, value in sorted(request.form.items())
        if key.startswith("leg_")
    ]
    try:
        order_id, total_price = confirm_itinerary_booking(
            session["user_id"],
            "round_trip",
            selected,
            2,
        )
        flash(f"Round trip booked. Order {order_id}, total ${total_price}.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("public.flight_search"))
