from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services.audit_service import log_action
from services.auth_service import (
    authenticate_user,
    get_airlines,
    register_agent,
    register_customer,
    register_staff,
    reset_customer_password,
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

    return render_template("register.html", airlines=get_airlines())


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role", "")
        identifier = request.form.get("identifier", "")
        password = request.form.get("password", "")
        try:
            user = authenticate_user(role, identifier, password)
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("login.html")
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
            session["can_delete"] = bool(user.get("can_delete"))
            next_url = url_for("staff.dashboard")

        log_action(role, session["user_id"], "login", "session", session["user_id"], "")
        flash("Logged in successfully.", "success")
        return redirect(next_url)

    return render_template("login.html")


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        try:
            if new_password != confirm_password:
                raise ValueError("New password and confirmation do not match.")
            reset_customer_password(
                request.form.get("email", ""),
                request.form.get("passport_number", ""),
                new_password,
            )
            log_action(
                "customer",
                request.form.get("email", ""),
                "password_reset",
                "customer",
                request.form.get("email", ""),
                "",
            )
            flash("Password reset successful. Please log in with your new password.", "success")
            return redirect(url_for("auth.login"))
        except ValueError as exc:
            flash(str(exc), "error")

    return render_template("forgot_password.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("public.index"))
