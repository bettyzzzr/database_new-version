# Feature Query Map

| Feature | Route / Endpoint | Service Function(s) | Main Tables or Views |
| --- | --- | --- | --- |
| Public home page | `public.index` | none | none |
| Register customer | `auth.register` | `auth_service.register_customer()` | `customer` |
| Register booking agent | `auth.register` | `auth_service.register_agent()` | `booking_agent` |
| Register staff | `auth.register` | `auth_service.register_staff()`, `auth_service.get_airlines()` | `airline_staff`, `airline` |
| Login and session setup | `auth.login` | `auth_service.authenticate_user()`, `audit_service.log_action()` | `customer`, `booking_agent`, `airline_staff`, `audit_log` |
| Logout | `auth.logout` | none | Flask session |
| Customer password reset | `auth.forgot_password` | `auth_service.reset_customer_password()`, `audit_service.log_action()` | `customer`, `audit_log` |
| Public upcoming flight search | `public.flight_search` | `flight_service.search_upcoming_flights()`, `location_service.resolve_location_to_airports()` | `flight_status_view`, `airplane`, `ticket`, `airport`, `city`, `city_alias` |
| Lowest-price calendar | `public.flight_search` | `flight_service.get_lowest_price_calendar()`, `location_service.resolve_location_to_airports()` | `flight_status_view`, `airplane`, `ticket`, `airport`, `city`, `city_alias` |
| Round-trip search | `public.flight_search` | `itinerary_service.build_itinerary_legs()`, `flight_service.search_upcoming_flights()` | `flight_status_view`, `airplane`, `ticket`, `airport`, `city`, `city_alias` |
| Public flight status lookup | `public.flight_status` | `flight_service.search_flight_statuses()` | `flight_status_view` |
| Customer dashboard data | `customer.dashboard` | `ticket_service.get_customer_tickets()`, `wishlist_service.get_wishlist_items()`, `waitlist_service.get_customer_waitlist()`, `frequent_search_service.get_recent_searches()`, `analytics_service.get_customer_default_spending()`, `analytics_service.get_customer_custom_spending()` | `ticket`, `flight_status_view`, `wishlist`, `waitlist`, `frequent_search` |
| Customer dashboard search | `customer.dashboard` | `flight_service.search_upcoming_flights()`, `frequent_search_service.record_search()` | `flight_status_view`, `airplane`, `ticket`, `airport`, `city`, `city_alias`, `frequent_search` |
| Customer direct purchase | `customer.purchase` | `ticket_service.purchase_ticket()` | `ticket`, `customer`, `flight_status_view`, `flight`, `airplane`, `audit_log` |
| Customer cart view | `customer.cart` | `cart_service.get_cart_flights()` | Flask session, `flight_status_view`, `airplane`, `ticket` |
| Customer cart add/remove/clear | `customer.cart_add`, `customer.cart_remove`, `customer.cart_clear` | `cart_service.add_to_cart()`, `cart_service.remove_from_cart()` | Flask session, `flight_status_view` |
| Customer cart booking | `customer.cart_confirm` | `cart_service.confirm_cart_booking()`, `ticket_service.purchase_ticket()` | Flask session, `ticket`, `flight_status_view`, `airplane`, `audit_log` |
| Round-trip booking | `customer.round_trip_confirm` | `itinerary_service.confirm_itinerary_booking()`, `itinerary_service.parse_selected_segments()` | `booking_order`, `booking_order_segment`, `ticket`, `flight_status_view`, `audit_log` |
| Ticket cancellation and refund request | `customer.ticket_cancel` | `refund_service.cancel_ticket_for_refund()`, `waitlist_service.notify_first_waiting_customer()` | `ticket`, `refund`, `flight_status_view`, `waitlist`, `audit_log` |
| Waitlist join | `customer.waitlist_join` | `waitlist_service.join_waitlist()` | `waitlist`, `flight_status_view`, `ticket`, `airplane`, `audit_log` |
| Waitlist claim | `customer.waitlist_claim` | `waitlist_service.claim_waitlist_ticket()` | `waitlist`, `ticket`, `flight_status_view`, `audit_log` |
| Wishlist add/remove/list | `customer.wishlist_add`, `customer.wishlist_remove`, `customer.dashboard` | `wishlist_service.add_wishlist_item()`, `wishlist_service.remove_wishlist_item()`, `wishlist_service.get_wishlist_items()` | `wishlist`, `flight_status_view`, `audit_log` |
| Frequent searches | `public.flight_search`, `customer.dashboard` | `frequent_search_service.record_search()`, `frequent_search_service.get_recent_searches()` | `frequent_search` |
| Agent dashboard data | `agent.dashboard` | `ticket_service.get_agent_tickets()`, `analytics_service.get_agent_commission_summary()`, `analytics_service.get_agent_customer_crm()`, `analytics_service.get_agent_top_customers_by_tickets()`, `analytics_service.get_agent_top_customers_by_commission()` | `ticket`, `flight_status_view`, `booking_agent`, `customer` |
| Agent flight search | `agent.dashboard` | `flight_service.search_upcoming_flights()` | `flight_status_view`, `airplane`, `ticket`, `airport`, `city`, `city_alias` |
| Agent purchase for customer(s) | `agent.purchase` | `ticket_service.purchase_tickets_for_agent()`, `ticket_service.purchase_ticket_for_agent()` | `booking_agent_work_for`, `booking_agent`, `customer`, `ticket`, `flight_status_view`, `flight`, `airplane`, `audit_log` |
| Staff airline flight list | `staff.dashboard` | `staff_service.get_staff_flights()` | `flight_status_view` |
| Staff passenger lookup | `staff.dashboard` | `staff_service.get_passenger_list()` | `ticket`, `customer` |
| Staff flight summary | `staff.dashboard` | `analytics_service.get_staff_flight_summary()` | `flight_status_view` |
| Staff load factor and revenue dashboard | `staff.dashboard` | `analytics_service.get_flight_revenue_dashboard()` | `flight_status_view`, `airplane`, `ticket` |
| Staff agent performance summary | `staff.dashboard` | `analytics_service.get_agent_performance_summary()` | `booking_agent_work_for`, `booking_agent`, `ticket` |
| Staff route opportunity alerts | `staff.dashboard` | `analytics_service.get_route_opportunity_alerts()` | `flight_status_view`, `airplane`, `ticket` |
| Staff admin top agents by tickets | `staff.dashboard` | `analytics_service.get_admin_top_agents_by_tickets()` | `booking_agent_work_for`, `booking_agent`, `ticket` |
| Staff admin top agents by commission | `staff.dashboard` | `analytics_service.get_admin_top_agents_by_commission()` | `booking_agent_work_for`, `booking_agent`, `ticket` |
| Staff admin most frequent customer | `staff.dashboard` | `analytics_service.get_admin_most_frequent_customer()` | `customer`, `ticket` |
| Staff admin tickets-sold chart | `staff.dashboard` | `analytics_service.get_admin_tickets_sold_per_month()` | `ticket` |
| Staff admin delay/on-time stats | `staff.dashboard` | `analytics_service.get_admin_delay_vs_on_time_stats()` | `flight_status_view` |
| Staff admin top destinations | `staff.dashboard` | `analytics_service.get_admin_top_destinations()` | `flight_status_view`, `ticket`, `airport`, `city` |
| Operator status update | `staff.status_update` | `staff_service.update_flight_status()` | `flight`, `audit_log` |
| Staff admin page reference data | `staff.admin` | `staff_service.get_city_airport_alias_mapping()`, `staff_service.get_timezones()`, `staff_service.get_airline_airplanes()`, `staff_service.get_city_names()`, `staff_service.get_airline_staff_accounts()` | `city`, `city_alias`, `airport`, `airport_timezone`, `airplane`, `airline_staff` |
| Add city | `staff.admin` | `staff_service.add_city()` | `city`, `audit_log` |
| Add city alias | `staff.admin` | `staff_service.add_city_alias()` | `city`, `city_alias`, `audit_log` |
| Add airport with timezone | `staff.admin` | `staff_service.add_airport()` | `city`, `airport`, `airport_timezone`, `audit_log` |
| Add airplane | `staff.admin` | `staff_service.add_airplane()` | `airplane`, `audit_log` |
| Create flight with automatic UTC times | `staff.admin` | `staff_service.create_flight()` | `flight`, `airplane`, `airport`, `airport_timezone`, `audit_log` |
| Available airplane lookup | `staff.available_airplanes` | `staff_service.get_available_airplanes()` | `airplane`, `flight`, `airport_timezone` |
| Associate booking agent with airline | `staff.admin` | `staff_service.associate_agent_with_airline()` | `booking_agent_work_for`, `booking_agent`, `airline`, `audit_log` |
| Grant staff permissions | `staff.admin` | `staff_service.grant_staff_permissions()` | `airline_staff`, `audit_log` |
| Staff city market analysis | `staff.city_analysis` | `analytics_service.get_city_market_analysis()`, `location_service.resolve_location_to_airports()` | `flight_status_view`, `airplane`, `ticket`, `airport`, `city`, `city_alias` |
| Staff city-pair market analysis | `staff.city_pair_analysis` | `analytics_service.get_city_pair_market_analysis()`, `location_service.resolve_location_to_airports()` | `flight_status_view`, `airplane`, `ticket`, `airport`, `city`, `city_alias` |
| Staff disruption assistant | `staff.disruption` | `analytics_service.get_disruption_assistant()` | `flight_status_view`, `ticket`, `customer`, `airport`, `city` |
| Staff audit log | `staff.audit_log` | `audit_service.get_recent_audit_logs()` | `audit_log` |
| Error pages | app error handlers | none | none |

## Status Rule

`flight.status` stores staff-controlled operational values: `scheduled`, `delayed`, and `cancelled`.

`flight_status_view.current_status` derives time-based statuses for scheduled flights: `upcoming`, `in_progress`, or `completed`. Manually delayed and cancelled flights keep their manual status.

## Capacity Rule

Seats left is calculated as airplane capacity minus active tickets. Cancelled tickets do not consume seats.

The current implementation does not use row-level locking for purchase concurrency.

## Permission Rule

Staff permissions are stored on `airline_staff`:

- `is_admin`: can use staff admin management pages.
- `is_operator`: can update flight status.
- `can_delete`: stored and exposed in session context for delete-capable staff behavior.

Some admin actions, such as granting staff permissions, require both admin and operator privileges.

## Prototype Scope

The implemented system is a Flask/MySQL airline reservation prototype with:

- Multi-role authentication for customers, booking agents, and airline staff.
- Multi-airport city and alias search.
- One-way, round-trip, cart, wishlist, waitlist, refund, and recent-search customer workflows.
- Agent purchasing and commission/customer analytics.
- Staff operational dashboards, admin management, route analytics, audit logging, and disruption support.
