from db import execute, fetch_all, fetch_one
from services.audit_service import log_action
from services.flight_service import get_flight_by_id


def _flight_capacity(airline_name, flight_num):
    """Return seats sold and airplane capacity for a flight."""
    return fetch_one(
        """
        SELECT a.seats, COUNT(t.ticket_id) AS sold
        FROM flight f
        JOIN airplane a ON f.airplane_id = a.airplane_id
        LEFT JOIN ticket t
          ON f.airline_name = t.airline_name AND f.flight_num = t.flight_num
        WHERE f.airline_name = %s AND f.flight_num = %s
        GROUP BY a.seats
        """,
        (airline_name, flight_num),
    )


def _ensure_can_purchase(airline_name, flight_num):
    """Enforce upcoming status and capacity before a ticket purchase."""
    flight = get_flight_by_id(airline_name, flight_num)
    if not flight:
        raise ValueError("Flight was not found.")
    if flight["current_status"] != "upcoming":
        raise ValueError("Only upcoming flights can be purchased.")

    capacity = _flight_capacity(airline_name, flight_num)
    if not capacity or capacity["sold"] >= capacity["seats"]:
        raise ValueError("This flight is full.")
    return flight


def purchase_ticket(customer_email, airline_name, flight_num):
    """Purchase one direct customer ticket after server-side checks."""
    customer = fetch_one("SELECT email FROM customer WHERE email = %s", (customer_email,))
    if not customer:
        raise ValueError("Customer account was not found.")

    flight = _ensure_can_purchase(airline_name, flight_num)
    ticket_id = execute(
        """
        INSERT INTO ticket
            (airline_name, flight_num, customer_email, booking_agent_email, sold_price)
        VALUES (%s, %s, %s, NULL, %s)
        """,
        (airline_name, flight_num, customer_email, flight["price"]),
    )
    log_action("customer", customer_email, "purchase", "ticket", str(ticket_id), "")
    return ticket_id


def purchase_ticket_for_agent(agent_email, customer_email, airline_name, flight_num):
    """Purchase one ticket for a customer if the agent represents the airline."""
    authorized = fetch_one(
        """
        SELECT 1
        FROM booking_agent_work_for
        WHERE email = %s AND airline_name = %s
        """,
        (agent_email, airline_name),
    )
    if not authorized:
        raise ValueError("This agent is not authorized to sell for that airline.")

    customer = fetch_one("SELECT email FROM customer WHERE email = %s", (customer_email,))
    if not customer:
        raise ValueError("Customer account was not found.")

    flight = _ensure_can_purchase(airline_name, flight_num)
    ticket_id = execute(
        """
        INSERT INTO ticket
            (airline_name, flight_num, customer_email, booking_agent_email, sold_price)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (airline_name, flight_num, customer_email, agent_email, flight["price"]),
    )
    log_action("agent", agent_email, "purchase", "ticket", str(ticket_id), customer_email)
    return ticket_id


def get_customer_tickets(customer_email):
    """List all tickets for a customer with dynamic flight status."""
    return fetch_all(
        """
        SELECT t.*, f.departure_airport, f.departure_time, f.arrival_airport,
               f.arrival_time, f.status, f.current_status
        FROM ticket t
        JOIN flight_status_view f
          ON t.airline_name = f.airline_name AND t.flight_num = f.flight_num
        WHERE t.customer_email = %s
        ORDER BY f.departure_time DESC
        """,
        (customer_email,),
    )


def get_agent_tickets(agent_email):
    """List tickets sold by a booking agent with dynamic flight status."""
    return fetch_all(
        """
        SELECT t.*, f.departure_airport, f.departure_time, f.arrival_airport,
               f.arrival_time, f.status, f.current_status
        FROM ticket t
        JOIN flight_status_view f
          ON t.airline_name = f.airline_name AND t.flight_num = f.flight_num
        WHERE t.booking_agent_email = %s
        ORDER BY t.purchase_date DESC
        """,
        (agent_email,),
    )
