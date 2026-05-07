from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services.flight_service import search_upcoming_flights
from services.ticket_service import get_customer_tickets, purchase_ticket

customer_bp = Blueprint("customer", __name__, url_prefix="/customer")


def customer_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "customer":
            flash("Customer login is required.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


@customer_bp.route("/dashboard", methods=["GET", "POST"])
@customer_required
def dashboard():
    flights = []
    if request.method == "POST":
        flights = search_upcoming_flights(
            request.form.get("origin", ""),
            request.form.get("destination", ""),
            request.form.get("departure_date") or None,
        )
        if not flights:
            flash("No upcoming flights matched that search.", "error")

    tickets = get_customer_tickets(session["user_id"])
    return render_template("customer_dashboard.html", tickets=tickets, flights=flights)


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
