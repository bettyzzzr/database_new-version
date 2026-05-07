from db import execute


def log_action(actor_role, actor_id, action_type, target_type, target_id, details=""):
    """Record a basic audit event for important Round 1 actions."""
    execute(
        """
        INSERT INTO audit_log
            (actor_role, actor_id, action_type, target_type, target_id, details)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (actor_role, actor_id, action_type, target_type, target_id, details),
    )
