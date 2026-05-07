from flask import Blueprint, flash, render_template, request, session

from services.flight_service import search_flight_statuses, search_upcoming_flights
from services.frequent_search_service import record_search

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def index():
    return render_template("index.html")


@public_bp.route("/flights/search", methods=["GET", "POST"])
def flight_search():
    flights = []
    searched = False
    if request.method == "POST":
        searched = True
        origin = request.form.get("origin", "")
        destination = request.form.get("destination", "")
        departure_date = request.form.get("departure_date") or None
        try:
            flights = search_upcoming_flights(
                origin,
                destination,
                departure_date,
                request.form.get("airline", ""),
                request.form.get("max_price", ""),
                bool(request.form.get("available_only")),
                request.form.get("sort_by", "departure_early"),
            )
            if session.get("role") == "customer":
                record_search(session["user_id"], origin, destination, departure_date)
            if not flights:
                flash("No upcoming flights matched that search.", "error")
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template("flight_search.html", flights=flights, searched=searched)


@public_bp.route("/flights/status", methods=["GET", "POST"])
def flight_status():
    flights = []
    searched = False
    if request.method == "POST":
        searched = True
        try:
            flights = search_flight_statuses(
                request.form.get("airline_name", ""),
                request.form.get("flight_num", ""),
            )
            if not flights:
                flash("Flight was not found.", "error")
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template("flight_status.html", flights=flights, searched=searched)
