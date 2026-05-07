from functools import wraps

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from services.analytics_service import (
    get_agent_performance_summary,
    get_city_market_analysis,
    get_city_pair_market_analysis,
    get_disruption_assistant,
    get_flight_revenue_dashboard,
    get_route_opportunity_alerts,
    get_staff_flight_summary,
)
from services.audit_service import get_recent_audit_logs
from services.customer_schema_service import ensure_customer_feature_schema
from services.staff_schema_service import ensure_staff_timezone_schema
from services.staff_service import (
    add_city,
    add_city_alias,
    add_airplane,
    add_airport,
    associate_agent_with_airline,
    create_flight,
    get_available_airplanes,
    get_city_airport_alias_mapping,
    get_airline_airplanes,
    get_airline_staff_accounts,
    get_city_names,
    get_passenger_list,
    get_staff_flights,
    get_timezones,
    grant_staff_permissions,
    update_flight_status,
)

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


def staff_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "staff":
            flash("Airline staff login is required.", "error")
            return redirect(url_for("auth.login"))
        ensure_customer_feature_schema()
        ensure_staff_timezone_schema()
        return view(*args, **kwargs)

    return wrapped


def _staff_context():
    return {
        "username": session["user_id"],
        "airline_name": session["airline_name"],
        "is_admin": session.get("is_admin", False),
        "is_operator": session.get("is_operator", False),
        "can_delete": session.get("can_delete", False),
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
    load_dashboard = get_flight_revenue_dashboard(session["airline_name"])
    agent_summary = get_agent_performance_summary(session["airline_name"])
    alerts = get_route_opportunity_alerts(session["airline_name"])
    return render_template(
        "staff_dashboard.html",
        flights=flights,
        summary=summary,
        load_dashboard=load_dashboard,
        agent_summary=agent_summary,
        alerts=alerts,
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
    if not session.get("is_admin"):
        flash("Admin staff permission is required.", "error")
        return redirect(url_for("staff.dashboard"))

    if request.method == "POST":
        action = request.form.get("action", "")
        staff = _staff_context()
        try:
            if action == "add_city":
                add_city(staff, request.form.get("city_name", ""))
            elif action == "add_alias":
                add_city_alias(
                    staff,
                    request.form.get("city_name", ""),
                    request.form.get("alias_name", ""),
                )
            elif action == "add_airport":
                add_airport(
                    staff,
                    request.form.get("airport_code", ""),
                    request.form.get("airport_name", ""),
                    request.form.get("city_name", ""),
                    request.form.get("timezone_offset", ""),
                )
            elif action == "add_airplane":
                add_airplane(staff, request.form.get("airplane_id", ""), request.form.get("seats", ""))
            elif action == "create_flight":
                created_flight_num = create_flight(
                    staff,
                    request.form.get("departure_airport", ""),
                    request.form.get("departure_time", ""),
                    request.form.get("arrival_airport", ""),
                    request.form.get("arrival_time", ""),
                    request.form.get("price", ""),
                    request.form.get("airplane_id", ""),
                )
                flash(f"Flight created as {created_flight_num}.", "success")
                return redirect(url_for("staff.admin"))
            elif action == "associate_agent":
                associate_agent_with_airline(staff, request.form.get("agent_email", ""))
            elif action == "grant_permissions":
                grant_staff_permissions(
                    staff,
                    request.form.get("staff_identifier", ""),
                    bool(request.form.get("grant_admin")),
                    bool(request.form.get("grant_operator")),
                    bool(request.form.get("grant_delete")),
                )
            else:
                raise ValueError("Unknown admin action.")
            flash("Admin action completed.", "success")
        except (PermissionError, ValueError) as exc:
            flash(str(exc), "error")
        return redirect(url_for("staff.admin"))

    mapping = get_city_airport_alias_mapping()
    timezones = get_timezones()
    airplanes = get_airline_airplanes(session["airline_name"])
    cities = get_city_names()
    staff_accounts = get_airline_staff_accounts(session["airline_name"])
    return render_template(
        "staff_admin.html",
        mapping=mapping,
        timezones=timezones,
        airplanes=airplanes,
        cities=cities,
        staff_accounts=staff_accounts,
        can_grant_permissions=session.get("is_admin") and session.get("is_operator"),
        flight_prefix_hint=session["airline_name"],
    )


@staff_bp.route("/admin/available-airplanes")
@staff_required
def available_airplanes():
    if not session.get("is_admin"):
        return jsonify({"message": "Admin staff permission is required.", "airplanes": []}), 403

    try:
        airplanes = get_available_airplanes(
            _staff_context(),
            request.args.get("departure_airport", ""),
            request.args.get("departure_time", ""),
            request.args.get("arrival_airport", ""),
            request.args.get("arrival_time", ""),
        )
        return jsonify({"message": "", "airplanes": airplanes})
    except ValueError as exc:
        return jsonify({"message": str(exc), "airplanes": []}), 400


@staff_bp.route("/city-analysis", methods=["GET", "POST"])
@staff_required
def city_analysis():
    analysis = None
    if request.method == "POST":
        try:
            analysis = get_city_market_analysis(
                session["airline_name"],
                request.form.get("city_input", ""),
            )
            if not analysis["airports"]:
                flash("City or alias was not found.", "error")
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template("staff_city_analysis.html", analysis=analysis)


@staff_bp.route("/city-pair-analysis", methods=["GET", "POST"])
@staff_required
def city_pair_analysis():
    analysis = None
    if request.method == "POST":
        analysis = get_city_pair_market_analysis(
            session["airline_name"],
            request.form.get("origin_city_input", ""),
            request.form.get("destination_city_input", ""),
        )
        if not analysis["origin_airports"] or not analysis["destination_airports"]:
            flash("Origin or destination city/alias was not found.", "error")
    return render_template("staff_city_pair_analysis.html", analysis=analysis)


@staff_bp.route("/audit-log")
@staff_required
def audit_log():
    logs = get_recent_audit_logs()
    return render_template("staff_audit_log.html", logs=logs)


@staff_bp.route("/disruption/<path:airline_name>/<flight_num>")
@staff_required
def disruption(airline_name, flight_num):
    if airline_name != session["airline_name"]:
        flash("You can only view disruptions for your airline.", "error")
        return redirect(url_for("staff.dashboard"))
    try:
        assistant = get_disruption_assistant(airline_name, flight_num)
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("staff.dashboard"))
    return render_template("staff_disruption.html", assistant=assistant)
