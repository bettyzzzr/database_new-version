from db import execute, fetch_all


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


def get_recent_audit_logs(limit=100):
    """Return recent audit log events for staff review."""
    return fetch_all(
        """
        SELECT log_id, actor_role, actor_id, action_type, target_type,
               target_id, details, created_at
        FROM audit_log
        ORDER BY created_at DESC, log_id DESC
        LIMIT %s
        """,
        (limit,),
    )
