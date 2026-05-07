from db import fetch_one


def get_agent_commission_summary(agent_email):
    """Summarize a booking agent's commission for tickets sold in last 30 days."""
    summary = fetch_one(
        """
        SELECT
            COUNT(*) AS tickets_sold,
            COALESCE(SUM(sold_price * 0.10), 0) AS total_commission,
            COALESCE(AVG(sold_price * 0.10), 0) AS average_commission
        FROM ticket
        WHERE booking_agent_email = %s
          AND purchase_date >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL 30 DAY)
        """,
        (agent_email,),
    )
    return summary or {"tickets_sold": 0, "total_commission": 0, "average_commission": 0}


def get_staff_flight_summary(airline_name):
    """Count this airline's flights by dynamic current status."""
    return fetch_one(
        """
        SELECT
            SUM(current_status = 'upcoming') AS upcoming_count,
            SUM(current_status = 'in_progress') AS in_progress_count,
            SUM(current_status = 'completed') AS completed_count,
            SUM(current_status = 'delayed') AS delayed_count,
            SUM(current_status = 'cancelled') AS cancelled_count
        FROM flight_status_view
        WHERE airline_name = %s
        """,
        (airline_name,),
    )
