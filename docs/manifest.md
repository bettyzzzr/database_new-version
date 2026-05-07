# Project Manifest

## Root Files

- `app.py`: creates the Flask application, registers route blueprints, and registers database teardown.
- `config.py`: reads database and session settings from environment variables.
- `db.py`: opens MySQL connections and provides parameterized query helpers.
- `requirements.txt`: lists Flask, PyMySQL, dotenv, and Werkzeug.
- `README.md`: explains setup, running, demo accounts, and presentation guidance.
- `schema.sql`: rebuilds all tables, Round 2 customer tables, and `flight_status_view`.
- `seed.sql`: inserts demo cities, aliases, airports, airlines, airplanes, flights, users, authorizations, and tickets.
- `migrations/register_fields.sql`: upgrades a Round 1 database for role-specific registration fields.
- `migrations/round2_customer_features.sql`: upgrades a Round 1 database for Round 2 customer-facing tables.

## Routes

- `routes/auth_routes.py`: registration, login, logout, and session setup.
- `routes/public_routes.py`: home page, public flight search, and public flight status check.
- `routes/customer_routes.py`: customer dashboard, purchase, cart, itinerary, cancellation, waitlist, and wishlist actions.
- `routes/agent_routes.py`: booking agent dashboard, commission view, and agent purchase.
- `routes/staff_routes.py`: staff dashboard, passenger list, operator status update, and admin actions.
- `routes/__init__.py`: marks route package.

## Services

- `services/auth_service.py`: password hashing, password verification, and user registration/authentication.
- `services/location_service.py`: resolves airport code, airport name, city name, and city aliases to airport codes.
- `services/flight_service.py`: searches upcoming flights with sorting/filtering, seats-left, recommendation labels, and dynamic status from `flight_status_view`.
- `services/ticket_service.py`: enforces ticket purchase rules, active-ticket capacity checks, customer tickets, and agent tickets.
- `services/cart_service.py`: manages session cart items and cart booking validation.
- `services/itinerary_service.py`: searches one-way, round-trip, and multi-city itinerary legs and creates booking orders.
- `services/refund_service.py`: cancels eligible tickets, creates refund requests, and notifies waitlist customers.
- `services/waitlist_service.py`: manages sold-out flight waitlist records.
- `services/wishlist_service.py`: manages customer wishlist records.
- `services/frequent_search_service.py`: records and lists recent customer flight searches.
- `services/staff_service.py`: enforces staff admin/operator rules and performs staff operations.
- `services/analytics_service.py`: simple commission and staff flight summaries.
- `services/audit_service.py`: inserts basic audit log rows.
- `services/__init__.py`: marks service package.

## Templates and Static

- `templates/base.html`: shared layout, navigation, and flash messages.
- `templates/index.html`: home page.
- `templates/login.html`: login form.
- `templates/register.html`: registration form for three roles.
- `templates/flight_search.html`: flight search form, sorting/filtering controls, seats-left labels, cart, wishlist, and waitlist actions.
- `templates/flight_status.html`: public status lookup form and result.
- `templates/customer_dashboard.html`: customer tickets, search, purchase, cancellation, wishlist, waitlist, and recent searches.
- `templates/customer_cart.html`: trip cart view, remove, confirm booking, and clear actions.
- `templates/customer_itinerary.html`: one-way, round-trip, and multi-city itinerary search and booking.
- `templates/agent_dashboard.html`: agent commission, sold tickets, search, and customer purchase action.
- `templates/staff_dashboard.html`: staff flight table, passenger lookup, and operator status update.
- `templates/staff_admin.html`: admin forms for airport, airplane, flight, and agent association.
- `templates/error.html`: simple error page.
- `static/style.css`: minimal shared styling.

## Docs

- `docs/manifest.md`: this file.
- `docs/feature_query_map.md`: maps features to service functions and tables/views.
- `docs/contributions.md`: placeholder contribution split.
- `docs/demo_script.md`: step-by-step Round 1 and Round 2 demo.
