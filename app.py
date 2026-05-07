from flask import Flask, render_template

from config import Config
from db import close_db
from routes.auth_routes import auth_bp
from routes.public_routes import public_bp
from routes.customer_routes import customer_bp
from routes.agent_routes import agent_bp
from routes.staff_routes import staff_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.teardown_appcontext(close_db)

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(staff_bp)

    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html", message="Page not found."), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("error.html", message="Server error."), 500

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
