from db import fetch_all, fetch_one


def resolve_location_to_airports(location_input):
    """Resolve airport code/name, city name, or city alias to airport codes."""
    value = (location_input or "").strip()
    if not value:
        return []

    airport = fetch_one(
        """
        SELECT airport_code
        FROM airport
        WHERE LOWER(airport_code) = LOWER(%s)
           OR LOWER(airport_name) = LOWER(%s)
        """,
        (value, value),
    )
    if airport:
        return [airport["airport_code"]]

    rows = fetch_all(
        """
        SELECT a.airport_code
        FROM airport a
        JOIN city c ON a.city_id = c.city_id
        WHERE LOWER(c.city_name) = LOWER(%s)
        UNION
        SELECT a.airport_code
        FROM airport a
        JOIN city_alias ca ON a.city_id = ca.city_id
        WHERE LOWER(ca.alias_name) = LOWER(%s)
        ORDER BY airport_code
        """,
        (value, value),
    )
    return [row["airport_code"] for row in rows]
