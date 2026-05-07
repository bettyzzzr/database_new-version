# Demo Script

## 1. Public Search by NYC

1. Open the home page.
2. Go to Search Flights.
3. Search origin `NYC` and destination `Shanghai`.
4. Explain that `NYC` resolves to both `JFK` and `LGA`.
5. Show BlueSky flights from both New York airports when dates match or when date is left empty.

## 2. Public Search by Shanghai or SH

1. Search origin `SH` and destination `Tokyo`.
2. Explain that `SH` is a city alias for Shanghai.
3. Show that results can include both `PVG` and `SHA`.

## 3. Public Dynamic Flight Status

1. Go to Flight Status.
2. Check `BlueSky Airlines` flight `BS201`.
3. Show `current_status` as `In Progress`.
4. Check `BlueSky Airlines` flight `BS301`.
5. Show `current_status` as `Completed`.
6. Open `schema.sql` and point to `flight_status_view`.

## 4. Customer Login and Purchase

1. Log in as `alice@example.com` with password `customer123`.
2. Search from `NYC` to `Shanghai`.
3. Purchase an upcoming flight.
4. Show the ticket in Purchased Flights.
5. Explain that capacity and upcoming status are checked in `ticket_service.py`.

## 5. Booking Agent Authorization Check

1. Log in as `agent@example.com` with password `agent123`.
2. Search from `NYC` to `Shanghai`.
3. Purchase a BlueSky Airlines ticket for `bob@example.com`.
4. Search from `Shanghai` to `Tokyo` and try purchasing a Dragon Air flight.
5. Show the rejection because the agent is authorized only for BlueSky Airlines.
6. Show the commission summary.

## 6. Staff Admin Creates Flight

1. Log in as `admin_blue` with password `admin123`.
2. Open Staff Admin.
3. Create a BlueSky flight using an existing BlueSky airplane id such as `1002`.
4. Return to Staff Dashboard and show the flight.

## 7. Staff Operator Sets Delayed or Cancelled

1. Log in as `operator_blue` with password `operator123`.
2. Open Staff Dashboard.
3. Set a flight status to `delayed` or `cancelled`.
4. Explain that the form allows only `scheduled`, `delayed`, and `cancelled`.
5. Explain that server-side validation in `staff_service.update_flight_status()` also rejects `upcoming`, `in_progress`, and `completed`.

## 8. Computed In Progress and Completed Status

1. Open `schema.sql`.
2. Show that `flight.status` is an enum with only `scheduled`, `delayed`, and `cancelled`.
3. Show that `flight_status_view` computes `upcoming`, `in_progress`, and `completed`.
4. Open `flight_service.py`, `ticket_service.py`, and `staff_service.py`.
5. Point out that user-facing reads use `flight_status_view`, not raw status computation in Python.

## 9. Round 2 Customer Search Sorting and Filtering

1. Log in as `alice@example.com` with password `customer123`.
2. Go to Search Flights.
3. Search origin `NYC` and destination `Shanghai`.
4. Choose `Price low to high` in the sort dropdown and search again.
5. Add a max price and search again.
6. Show `Seats Left` and `Recommendation` in the result table.
7. Point out that `BS102` is sold out in the seed data and shows `Join Waitlist`.

## 10. Round 2 Wishlist, Cart, and Waitlist

1. From the search results, add an available flight to the wishlist.
2. Open Customer Dashboard and show the Wishlist section.
3. Add an available flight to the cart.
4. Open Cart.
5. Confirm cart booking.
6. Return to Customer Dashboard and show the new ticket.
7. Join the waitlist for the sold-out `BS102` flight.
8. Show the Waitlist section on Customer Dashboard.

## 11. Round 2 Itinerary Booking

1. Open Itinerary from the customer navigation.
2. Choose `Round trip`.
3. Enter Leg 1 as `NYC` to `Shanghai`.
4. Enter Leg 2 as `Shanghai` to `NYC`.
5. Search itinerary options.
6. Select one flight for each leg.
7. Confirm itinerary booking.
8. Show that one booking order creates one ticket per selected leg.

## 12. Round 2 Cancellation and Refund

1. Open Customer Dashboard.
2. Find an active upcoming ticket with departure more than 24 hours away.
3. Click Cancel.
4. Show that the ticket status becomes `Cancelled`.
5. Show that the refund request amount is 80% of `sold_price`.
6. If a waiting customer exists for that flight, show that the first waiting row becomes `notified`.

## 13. Round 3 Staff Business Dashboard

1. Log in as `admin_blue` with password `admin123`.
2. Open Staff Dashboard.
3. Show the Load Factor / Revenue Dashboard.
4. Point out capacity, active tickets sold, seats left, load factor, revenue, and business signal.
5. Show the Agent Performance Summary.
6. Show Route Opportunity Alerts.

## 14. Round 3 City and City-Pair Analysis

1. Open City Analysis.
2. Enter `NYC`.
3. Show that `NYC` resolves to New York market airports such as `JFK` and `LGA`.
4. Show total flights, tickets sold, revenue, average load factor, most popular destination, delay rate, and airport comparison.
5. Open City-Pair Analysis.
6. Enter origin `NYC` and destination `Shanghai`.
7. Show origin airports, destination airports, cheapest airport pair, most popular airport pair, and comparison rows.

## 15. Round 3 Admin Data Management

1. Open Staff Admin as `admin_blue`.
2. Add a city.
3. Add a city alias for that city.
4. Add an airport associated with that city and choose its timezone.
5. Show the City-Airport-Alias Mapping table.
6. Explain that aliases are stored in `city_alias` and do not require Python if-statements.
7. Create a flight by entering only airport local display times.
8. Explain that the UTC fields are calculated by `staff_service.create_flight()` from `airport_timezone`.

## 16. Round 3 Audit Log

1. Open Audit Log.
2. Show recent customer, agent, and staff actions.
3. Point out actions such as purchase, cart booking, itinerary booking, refund request, waitlist join, wishlist add/remove, flight creation, status update, city add, alias add, airport add, and agent association.

## 17. Round 3 Agent CRM

1. Log in as `agent@example.com` with password `agent123`.
2. Open Agent Dashboard.
3. Show the Agent CRM section.
4. Point out customer email, tickets bought through this agent, total revenue, commission, last purchase date, and customer label.

## 18. Round 3 Disruption Assistant

1. Log in as `operator_blue` with password `operator123`.
2. Open Staff Dashboard.
3. Set a BlueSky flight status to `delayed`.
4. Open the Disruption Assistant link for that delayed flight.
5. Show disrupted flight information.
6. Show affected active passengers.
7. Show alternative upcoming flights in the same city markets.
8. Explain that if `JFK -> PVG` is disrupted, the system may suggest `LGA -> SHA` because both airport pairs belong to the same city markets.

## Bonus Feature Explanation

Our bonus features turn the project from a basic reservation system into a commercial airline/OTA prototype:

- Customers can compare and book realistic trips.
- Staff can analyze city-level and route-level market performance.
- City aliases are stored as structured data.
- Audit logs provide operational accountability.
- The disruption assistant uses the multi-airport city logic to suggest realistic alternatives.
