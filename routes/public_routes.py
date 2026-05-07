from flask import Blueprint, flash, render_template, request, session

from services.flight_service import (
    get_lowest_price_calendar,
    search_flight_statuses,
    search_upcoming_flights,
)
from services.frequent_search_service import record_search
from services.itinerary_service import build_itinerary_legs

public_bp = Blueprint("public", __name__)


def _selected_booking_type():
    booking_type = request.form.get("booking_type", "one_way")
    if booking_type not in {"one_way", "round_trip"}:
        raise ValueError("Choose one way or round trip.")
    return booking_type


def _round_trip_legs(origin, destination, departure_date, return_date):
    return build_itinerary_legs(
        "round_trip",
        [
            {"origin": origin, "destination": destination, "date": departure_date or ""},
            {"origin": destination, "destination": origin, "date": return_date or ""},
        ],
    )


@public_bp.route("/")
def index():
    return render_template("index.html")


@public_bp.route("/flights/search", methods=["GET", "POST"])
def flight_search():
    flights = []
    price_calendar = []
    trip_legs = []
    searched = False
    search_action = request.form.get("action", "search")
    booking_type = request.form.get("booking_type", "one_way")
    calendar_days = request.form.get("calendar_days", "30")
    if request.method == "POST":
        searched = True
        origin = request.form.get("origin", "")
        destination = request.form.get("destination", "")
        departure_date = request.form.get("departure_date") or None
        return_date = request.form.get("return_date") or None
        airline = request.form.get("airline", "")
        max_price = request.form.get("max_price", "")
        available_only = bool(request.form.get("available_only"))
        sort_by = request.form.get("sort_by", "departure_early")
        try:
            booking_type = _selected_booking_type()
            if search_action == "price_calendar":
                price_calendar = get_lowest_price_calendar(
                    origin,
                    destination,
                    departure_date,
                    calendar_days,
                    airline,
                    max_price,
                    True,
                )
                if not price_calendar:
                    flash("Origin or destination was not found.", "error")
                elif not any(day["lowest_price"] is not None for day in price_calendar):
                    flash("No available upcoming flights were found for that calendar range.", "error")
            elif booking_type == "round_trip":
                trip_legs = _round_trip_legs(origin, destination, departure_date, return_date)
                for leg in trip_legs:
                    leg["flights"] = search_upcoming_flights(
                        leg["origin"],
                        leg["destination"],
                        leg["date"],
                        airline,
                        max_price,
                        True,
                        sort_by,
                    )
                if any(not leg["flights"] for leg in trip_legs):
                    flash("One or more round-trip legs have no available flights.", "error")
            else:
                flights = search_upcoming_flights(
                    origin,
                    destination,
                    departure_date,
                    airline,
                    max_price,
                    available_only,
                    sort_by,
                )
                if not flights:
                    flash("No upcoming flights matched that search.", "error")
            if session.get("role") == "customer":
                record_search(session["user_id"], origin, destination, departure_date)
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template(
        "flight_search.html",
        flights=flights,
        price_calendar=price_calendar,
        trip_legs=trip_legs,
        searched=searched,
        search_action=search_action,
        booking_type=booking_type,
        calendar_days=calendar_days,
    )


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
