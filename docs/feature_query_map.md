# Feature Query Map

| Feature | Route | Service Function | Main Tables or Views |
| --- | --- | --- | --- |
| Public home page | `public.index` | none | none |
| Register customer | `auth.register` | `auth_service.register_customer()` | `customer` |
| Register booking agent | `auth.register` | `auth_service.register_agent()` | `booking_agent` |
| Register staff | `auth.register` | `auth_service.register_staff()` | `airline_staff`, `airline` |
| Login | `auth.login` | `auth_service.authenticate_user()`, `audit_service.log_action()` | `customer`, `booking_agent`, `airline_staff`, `audit_log` |
| Public upcoming flight search | `public.flight_search` | `flight_service.search_upcoming_flights()`, `location_service.resolve_location_to_airports()` | `flight_status_view`, `airport`, `city`, `city_alias` |
| Public status check | `public.flight_status` | `flight_service.get_flight_status()` | `flight_status_view` |
| Customer ticket list | `customer.dashboard` | `ticket_service.get_customer_tickets()` | `ticket`, `flight_status_view` |
| Customer purchase | `customer.purchase` | `ticket_service.purchase_ticket()` | `ticket`, `customer`, `flight_status_view`, `flight`, `airplane`, `audit_log` |
| Agent ticket list | `agent.dashboard` | `ticket_service.get_agent_tickets()` | `ticket`, `flight_status_view` |
| Agent commission summary | `agent.dashboard` | `analytics_service.get_agent_commission_summary()` | `ticket` |
| Agent purchase for customer | `agent.purchase` | `ticket_service.purchase_ticket_for_agent()` | `booking_agent_work_for`, `customer`, `ticket`, `flight_status_view`, `flight`, `airplane`, `audit_log` |
| Staff airline flight list | `staff.dashboard` | `staff_service.get_staff_flights()` | `flight_status_view` |
| Staff flight summary | `staff.dashboard` | `analytics_service.get_staff_flight_summary()` | `flight_status_view` |
| Passenger list | `staff.dashboard` | `staff_service.get_passenger_list()` | `ticket`, `customer` |
| Add airport | `staff.admin` | `staff_service.add_airport()` | `city`, `airport`, `audit_log` |
| Add airplane | `staff.admin` | `staff_service.add_airplane()` | `airplane`, `audit_log` |
| Create flight | `staff.admin` | `staff_service.create_flight()` | `flight`, `airplane`, `airport`, `audit_log` |
| Associate booking agent | `staff.admin` | `staff_service.associate_agent_with_airline()` | `booking_agent_work_for`, `booking_agent`, `airline`, `audit_log` |
| Operator status update | `staff.status_update` | `staff_service.update_flight_status()` | `flight`, `audit_log` |

## Status Rule

`flight.status` stores only staff-controlled operational values: `scheduled`, `delayed`, and `cancelled`.

`flight_status_view.current_status` dynamically returns `upcoming`, `in_progress`, or `completed` for scheduled flights, while preserving manually set `delayed` and `cancelled` statuses.
