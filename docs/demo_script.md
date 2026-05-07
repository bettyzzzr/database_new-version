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
