# Feature Query Map

| Feature | Route | Service Function | Main Tables or Views |
| --- | --- | --- | --- |
| Public home page | `public.index` | none | none |
| Register customer | `auth.register` | `auth_service.register_customer()` | `customer` |
| Register booking agent | `auth.register` | `auth_service.register_agent()` | `booking_agent` |
| Register staff | `auth.register` | `auth_service.register_staff()` | `airline_staff`, `airline` |
| Login | `auth.login` | `auth_service.authenticate_user()`, `audit_service.log_action()` | `customer`, `booking_agent`, `airline_staff`, `audit_log` |
| Public upcoming flight search with sorting/filtering | `public.flight_search` | `flight_service.search_upcoming_flights()`, `location_service.resolve_location_to_airports()` | `flight_status_view`, `airplane`, `ticket`, `airport`, `city`, `city_alias` |
| Public status check | `public.flight_status` | `flight_service.get_flight_status()` | `flight_status_view` |
| Customer ticket list | `customer.dashboard` | `ticket_service.get_customer_tickets()` | `ticket`, `flight_status_view` |
| Customer purchase | `customer.purchase` | `ticket_service.purchase_ticket()` | `ticket`, `customer`, `flight_status_view`, `flight`, `airplane`, `audit_log` |
| Customer cart view | `customer.cart` | `cart_service.get_cart_flights()` | `flight_status_view`, `airplane`, `ticket` |
| Customer cart add/remove | `customer.cart_add`, `customer.cart_remove`, `customer.cart_clear` | `cart_service.add_to_cart()`, `cart_service.remove_from_cart()` | Flask session, `flight_status_view` |
| Customer cart booking | `customer.cart_confirm` | `cart_service.confirm_cart_booking()`, `ticket_service.purchase_ticket()` | `ticket`, `flight_status_view`, `airplane`, `audit_log` |
| Itinerary search | `customer.itinerary` | `itinerary_service.search_itinerary_options()` | `flight_status_view`, `airplane`, `ticket`, `airport`, `city`, `city_alias` |
| Itinerary booking | `customer.itinerary_confirm` | `itinerary_service.confirm_itinerary_booking()` | `booking_order`, `booking_order_segment`, `ticket`, `flight_status_view`, `audit_log` |
| Cancellation and refund | `customer.ticket_cancel` | `refund_service.cancel_ticket_for_refund()` | `ticket`, `refund`, `flight_status_view`, `waitlist`, `audit_log` |
| Waitlist join | `customer.waitlist_join` | `waitlist_service.join_waitlist()` | `waitlist`, `flight_status_view`, `ticket`, `airplane`, `audit_log` |
| Wishlist add/remove/list | `customer.wishlist_add`, `customer.wishlist_remove`, `customer.dashboard` | `wishlist_service.add_wishlist_item()`, `wishlist_service.remove_wishlist_item()`, `wishlist_service.get_wishlist_items()` | `wishlist`, `flight_status_view`, `audit_log` |
| Frequent searches | `public.flight_search`, `customer.dashboard` | `frequent_search_service.record_search()`, `frequent_search_service.get_recent_searches()` | `frequent_search`, `audit_log` |
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

## Round 2 Capacity Rule

Seats left is calculated as airplane capacity minus active tickets. Cancelled tickets do not consume seats.

Round 2 intentionally does not use `SELECT ... FOR UPDATE` or row-level locking; concurrency-safe purchasing is reserved for Round 4.
