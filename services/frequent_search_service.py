from db import execute, fetch_all
from services.audit_service import log_action


def record_search(customer_email, origin_input, destination_input, search_date):
    """Record a logged-in customer's flight search inputs."""
    if not customer_email or not origin_input or not destination_input:
        return None

    search_id = execute(
        """
        INSERT INTO frequent_search
            (customer_email, origin_input, destination_input, search_date)
        VALUES (%s, %s, %s, %s)
        """,
        (customer_email, origin_input, destination_input, search_date or None),
    )
    log_action("customer", customer_email, "search", "frequent_search", str(search_id), "")
    return search_id


def get_recent_searches(customer_email, limit=5):
    """Return a customer's most recent saved searches."""
    return fetch_all(
        """
        SELECT *
        FROM frequent_search
        WHERE customer_email = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (customer_email, limit),
    )
