from flask import Blueprint, flash, render_template, request

from services.flight_service import get_flight_status, search_upcoming_flights

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
        flights = search_upcoming_flights(origin, destination, departure_date)
        if not flights:
            flash("No upcoming flights matched that search.", "error")
    return render_template("flight_search.html", flights=flights, searched=searched)


@public_bp.route("/flights/status", methods=["GET", "POST"])
def flight_status():
    flight = None
    if request.method == "POST":
        flight = get_flight_status(
            request.form.get("airline_name", ""),
            request.form.get("flight_num", ""),
        )
        if not flight:
            flash("Flight was not found.", "error")
    return render_template("flight_status.html", flight=flight)
