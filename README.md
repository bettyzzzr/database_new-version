# Air Ticket Reservation System

CSCI-SHU 213 Database Final Project rebuilt with Flask and MySQL.

## Architecture

- `app.py` creates the Flask app and registers blueprints only.
- `routes/` handles form input, session checks, redirects, flashes, and rendering.
- `services/` contains SQL queries and business rules.
- `schema.sql` rebuilds the database structure, Round 2 tables, timezone metadata, and `flight_status_view`.
- `seed.sql` loads demo data for the presentation workflow.
- `templates/` contains simple forms, tables, navigation, and messages.

## Database Setup

Log in to MySQL and run:

```bash
mysql -u root -p < schema.sql
mysql -u root -p air_ticket_reservation < seed.sql
```

For an existing Round 1 database, apply the migration files in `migrations/` instead of rebuilding from scratch.

If your MySQL user or database settings differ, set environment variables before running Flask:

```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DB=air_ticket_reservation
export SECRET_KEY=dev-secret
```

## Run the App

Create a virtual environment, install dependencies, and start Flask:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run --debug
```

Open `http://127.0.0.1:5000`.

## Demo Accounts

All demo passwords are intentionally simple for presentation.

| Role | Login | Password | Notes |
| --- | --- | --- | --- |
| Customer | `alice@example.com` | `customer123` | Has direct tickets |
| Customer | `bob@example.com` | `customer123` | Has an agent-purchased ticket |
| Booking agent | `agent@example.com` | `agent123` | Authorized for BlueSky Airlines only |
| Admin staff | `admin_blue` | `admin123` | Can add airport, airplane, flight, and associate agents |
| Operator staff | `operator_blue` | `operator123` | Can set scheduled, delayed, or cancelled |
| Admin + operator | `staff_both` | `staff123` | Can perform both admin and operator tasks |

## Presentation Files to Open

1. `app.py` to show app creation and blueprint registration.
2. `routes/customer_routes.py`, `routes/agent_routes.py`, and `routes/staff_routes.py` to show session and permission checks.
3. `services/location_service.py` to show multi-airport city and alias resolution.
4. `services/flight_service.py` to show `flight_status_view` usage.
5. `services/ticket_service.py` to show capacity and purchase rules.
6. `services/staff_service.py` to show admin/operator enforcement.
7. `schema.sql` to show normalized tables and dynamic status view.
8. `seed.sql` to show demo data.

## Project Scope

Implemented:

- Public registration, login, logout
- Public flight search by airport, airport name, city name, or alias
- Public flight status check
- Customer dashboard, ticket list, flight search, and purchase
- Round-trip booking from Search Flights
- Trip cart booking
- Refund request flow
- Waitlist and wishlist flows
- Recent customer search history
- Customer spending analytics
- Booking agent dashboard, authorized purchase, sold-ticket list, and commission summary
- Staff dashboard, airline flight list, passenger list, admin actions, and operator status updates
- Staff city/city-pair analysis, route opportunity alerts, audit log, and disruption assistant
- Audit logging for login, purchases, flight creation, airport/airplane changes, agent association, and status updates

Future extensions:

- Multi-city itineraries beyond one-way and round-trip
- Automated refund approval/rejection
- Waitlist notification delivery outside the app
