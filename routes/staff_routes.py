from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services.analytics_service import get_staff_flight_summary
from services.staff_service import (
    add_airplane,
    add_airport,
    associate_agent_with_airline,
    create_flight,
    get_passenger_list,
    get_staff_flights,
    update_flight_status,
)

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


def staff_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "staff":
            flash("Airline staff login is required.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def _staff_context():
    return {
        "username": session["user_id"],
        "airline_name": session["airline_name"],
        "is_admin": session.get("is_admin", False),
        "is_operator": session.get("is_operator", False),
    }


@staff_bp.route("/dashboard", methods=["GET", "POST"])
@staff_required
def dashboard():
    passengers = []
    passenger_flight_num = ""
    if request.method == "POST" and request.form.get("action") == "passengers":
        passenger_flight_num = request.form.get("flight_num", "")
        passengers = get_passenger_list(_staff_context(), passenger_flight_num)

    flights = get_staff_flights(session["airline_name"])
    summary = get_staff_flight_summary(session["airline_name"])
    return render_template(
        "staff_dashboard.html",
        flights=flights,
        summary=summary,
        passengers=passengers,
        passenger_flight_num=passenger_flight_num,
    )


@staff_bp.route("/status", methods=["POST"])
@staff_required
def status_update():
    try:
        update_flight_status(
            _staff_context(),
            request.form.get("flight_num", ""),
            request.form.get("status", ""),
        )
        flash("Flight status updated.", "success")
    except (PermissionError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("staff.dashboard"))


@staff_bp.route("/admin", methods=["GET", "POST"])
@staff_required
def admin():
    if request.method == "POST":
        action = request.form.get("action", "")
        staff = _staff_context()
        try:
            if action == "add_airport":
                add_airport(
                    staff,
                    request.form.get("airport_code", ""),
                    request.form.get("airport_name", ""),
                    request.form.get("city_name", ""),
                )
            elif action == "add_airplane":
                add_airplane(staff, request.form.get("airplane_id", ""), request.form.get("seats", ""))
            elif action == "create_flight":
                create_flight(
                    staff,
                    request.form.get("flight_num", ""),
                    request.form.get("departure_airport", ""),
                    request.form.get("departure_time", ""),
                    request.form.get("departure_time_utc", ""),
                    request.form.get("arrival_airport", ""),
                    request.form.get("arrival_time", ""),
                    request.form.get("arrival_time_utc", ""),
                    request.form.get("price", ""),
                    request.form.get("airplane_id", ""),
                )
            elif action == "associate_agent":
                associate_agent_with_airline(staff, request.form.get("agent_email", ""))
            else:
                raise ValueError("Unknown admin action.")
            flash("Admin action completed.", "success")
        except (PermissionError, ValueError) as exc:
            flash(str(exc), "error")
        return redirect(url_for("staff.admin"))

    return render_template("staff_admin.html")
