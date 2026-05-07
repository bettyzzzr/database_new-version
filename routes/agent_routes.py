from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services.analytics_service import get_agent_commission_summary
from services.customer_schema_service import ensure_customer_feature_schema
from services.flight_service import search_upcoming_flights
from services.ticket_service import get_agent_tickets, purchase_ticket_for_agent

agent_bp = Blueprint("agent", __name__, url_prefix="/agent")


def agent_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "agent":
            flash("Booking agent login is required.", "error")
            return redirect(url_for("auth.login"))
        ensure_customer_feature_schema()
        return view(*args, **kwargs)

    return wrapped


@agent_bp.route("/dashboard", methods=["GET", "POST"])
@agent_required
def dashboard():
    flights = []
    if request.method == "POST":
        try:
            flights = search_upcoming_flights(
                request.form.get("origin", ""),
                request.form.get("destination", ""),
                request.form.get("departure_date") or None,
            )
            if not flights:
                flash("No upcoming flights matched that search.", "error")
        except ValueError as exc:
            flash(str(exc), "error")

    tickets = get_agent_tickets(session["user_id"])
    summary = get_agent_commission_summary(session["user_id"])
    return render_template("agent_dashboard.html", tickets=tickets, flights=flights, summary=summary)


@agent_bp.route("/purchase", methods=["POST"])
@agent_required
def purchase():
    try:
        purchase_ticket_for_agent(
            session["user_id"],
            request.form.get("customer_email", ""),
            request.form.get("airline_name", ""),
            request.form.get("flight_num", ""),
        )
        flash("Agent ticket purchase completed.", "success")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("agent.dashboard"))
