from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services.audit_service import log_action
from services.auth_service import (
    authenticate_user,
    register_agent,
    register_customer,
    register_staff,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        role = request.form.get("role", "")
        password = request.form.get("password", "")
        try:
            if role == "customer":
                register_customer(
                    request.form.get("email", ""),
                    request.form.get("name", ""),
                    password,
                    request.form.get("passport_number", ""),
                    request.form.get("passport_expiration", ""),
                    request.form.get("passport_country", ""),
                )
            elif role == "agent":
                register_agent(
                    request.form.get("email", ""),
                    request.form.get("name", ""),
                    password,
                )
            elif role == "staff":
                register_staff(
                    request.form.get("email", ""),
                    request.form.get("username", ""),
                    password,
                    request.form.get("first_name", ""),
                    request.form.get("last_name", ""),
                    request.form.get("airline_name", ""),
                )
            else:
                raise ValueError("Choose a valid account type.")
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("auth.login"))
        except ValueError as exc:
            flash(str(exc), "error")

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role", "")
        identifier = request.form.get("identifier", "")
        password = request.form.get("password", "")
        user = authenticate_user(role, identifier, password)
        if not user:
            flash("Invalid login credentials.", "error")
            return render_template("login.html")

        session.clear()
        session["role"] = role
        if role == "customer":
            session["user_id"] = user["email"]
            next_url = url_for("customer.dashboard")
        elif role == "agent":
            session["user_id"] = user["email"]
            session["booking_agent_id"] = user["booking_agent_id"]
            next_url = url_for("agent.dashboard")
        else:
            session["user_id"] = user["username"]
            session["airline_name"] = user["airline_name"]
            session["is_admin"] = bool(user["is_admin"])
            session["is_operator"] = bool(user["is_operator"])
            next_url = url_for("staff.dashboard")

        log_action(role, session["user_id"], "login", "session", session["user_id"], "")
        flash("Logged in successfully.", "success")
        return redirect(next_url)

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("public.index"))
