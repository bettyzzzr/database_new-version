# Project Manifest

## Root Files

- `app.py`: Flask application factory. Registers the public, auth, customer, agent, and staff blueprints; closes database connections at app teardown; renders `error.html` for 404 and 500 errors.
- `config.py`: reads Flask secret key and MySQL connection settings from environment variables.
- `db.py`: opens per-request PyMySQL connections and provides parameterized query helpers.
- `requirements.txt`: Python dependencies for Flask, PyMySQL, python-dotenv, and Werkzeug.
- `README.md`: setup, run instructions, demo accounts, scope, and presentation file list.
- `schema.sql`: full database rebuild script. Creates city/airport/timezone, airline, airplane, flight, user, ticket, itinerary, refund, waitlist, wishlist, frequent-search, audit-log tables, plus `flight_status_view`.
- `seed.sql`: demo data for cities, aliases, airports, airlines, airplanes, flights, accounts, staff permissions, agent associations, tickets, and customer feature records.

## Migrations

- `migrations/register_fields.sql`: adds registration-related fields to an older Round 1 database.
- `migrations/round2_customer_features.sql`: adds cart-adjacent customer feature tables such as booking orders, refunds, waitlist, wishlist, frequent search, and audit log.
- `migrations/airport_timezones.sql`: adds airport timezone metadata used when staff create flights from local times.

## Routes

- `routes/public_routes.py`: public home page, upcoming flight search, lowest-price calendar, round-trip search, and flight status lookup.
- `routes/auth_routes.py`: registration for customers, agents, and staff; login; logout; customer password reset.
- `routes/customer_routes.py`: customer dashboard, direct purchase, cart add/remove/clear/confirm, waitlist join/claim, wishlist add/remove, ticket cancellation/refund request, and round-trip confirmation.
- `routes/agent_routes.py`: booking agent dashboard, search, sold-ticket list, commission/CRM analytics, and purchases for one or more customers.
- `routes/staff_routes.py`: staff dashboard, staff analytics, passenger lookup, operator status update, admin management actions, available-airplane API, city analysis, city-pair analysis, audit log, and disruption assistant.
- `routes/__init__.py`: route package marker.

## Services

- `services/auth_service.py`: password hashing/checking, user registration, airline list lookup, login authentication, and customer password reset.
- `services/location_service.py`: resolves airport code, airport name, city name, or city alias into airport codes.
- `services/flight_service.py`: upcoming flight search, recommendation labels, seats-left calculations, lowest-price calendar, status search, and flight lookup through `flight_status_view`.
- `services/ticket_service.py`: direct customer purchase, agent purchase, multi-customer agent purchase, purchase validation, active-ticket capacity checks, seats-left lookup, and ticket list queries.
- `services/cart_service.py`: session cart normalization, add/remove behavior, cart flight lookup, and cart booking confirmation.
- `services/itinerary_service.py`: one-way/round-trip leg validation, selected segment parsing, booking order creation, booking order segment creation, and ticket insertion for itinerary bookings.
- `services/refund_service.py`: ticket cancellation, refund record creation, and waitlist notification handoff.
- `services/waitlist_service.py`: sold-out waitlist joins, first-waiting-customer notification, waitlist claim, and customer waitlist list.
- `services/wishlist_service.py`: wishlist add, remove, and list.
- `services/frequent_search_service.py`: records customer searches and lists recent searches.
- `services/staff_service.py`: staff permission enforcement, city/alias/airport/airplane management, timezone normalization, local-to-UTC flight creation, available-airplane lookup, staff permission grants, agent-airline association, operator status updates, passenger lookup, mapping lookup, and staff flight list.
- `services/analytics_service.py`: customer spending analytics, agent commission/CRM analytics, staff flight summaries, admin reports, load/revenue dashboards, agent performance summaries, city/city-pair market analysis, route alerts, and disruption assistant data.
- `services/audit_service.py`: inserts audit events and lists recent audit log rows.
- `services/customer_schema_service.py`: ensures optional customer feature tables/columns exist before customer and agent workflows run.
- `services/staff_schema_service.py`: ensures staff timezone/supporting schema exists before staff workflows run.
- `services/__init__.py`: service package marker.

## Templates

- `templates/base.html`: shared layout, navigation, and flash messages; extended by page templates.
- `templates/index.html`: public home page rendered by `public.index`.
- `templates/login.html`: login form rendered by `auth.login`.
- `templates/register.html`: role-specific registration form rendered by `auth.register`.
- `templates/forgot_password.html`: customer password reset form rendered by `auth.forgot_password`.
- `templates/flight_search.html`: public flight search, lowest-price calendar, one-way results, round-trip results, cart/wishlist/waitlist actions, and round-trip booking form rendered by `public.flight_search`.
- `templates/flight_status.html`: public flight status lookup rendered by `public.flight_status`.
- `templates/customer_dashboard.html`: customer tickets, search, purchase, cancellation, wishlist, waitlist, recent searches, and spending analytics rendered by `customer.dashboard`.
- `templates/customer_cart.html`: customer cart view with remove, confirm, and clear actions rendered by `customer.cart`.
- `templates/agent_dashboard.html`: agent tickets, flight search, customer purchase form, commission summary, CRM, and top-customer analytics rendered by `agent.dashboard`.
- `templates/staff_dashboard.html`: staff flight list, passenger lookup, status update, load/revenue dashboard, agent summary, route alerts, and admin analytics rendered by `staff.dashboard`.
- `templates/staff_admin.html`: staff admin forms for city, alias, airport/timezone, airplane, flight creation, agent association, staff permission grants, and mapping display rendered by `staff.admin`.
- `templates/staff_city_analysis.html`: staff city/alias market analysis rendered by `staff.city_analysis`.
- `templates/staff_city_pair_analysis.html`: staff city-pair market analysis rendered by `staff.city_pair_analysis`.
- `templates/staff_audit_log.html`: recent audit log table rendered by `staff.audit_log`.
- `templates/staff_disruption.html`: disrupted-flight passenger list and alternative same-city-market flights rendered by `staff.disruption`.
- `templates/error.html`: shared 404/500 error page rendered by app error handlers.
- `templates/_flight_table.html`: partial flight-table template currently present but not directly rendered by a route.

## Static

- `static/style.css`: shared CSS for layout, navigation, tables, forms, cards, alerts, and dashboard sections.

## Docs

- `docs/manifest.md`: this implementation manifest.
- `docs/feature_query_map.md`: maps user-facing features to Flask endpoints, service functions, and database tables/views.
- `docs/contributions.md`: contribution split placeholder.
- `docs/demo_script.md`: demo walkthrough for the implemented reservation workflows.
