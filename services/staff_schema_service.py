from functools import lru_cache

from db import get_db


@lru_cache(maxsize=1)
def ensure_staff_timezone_schema():
    """Create missing airport timezone metadata and staff permission columns."""
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS airport_timezone (
                timezone_name VARCHAR(64) PRIMARY KEY,
                utc_offset_minutes INT NOT NULL,
                display_name VARCHAR(100) NOT NULL
            )
            """
        )
        cursor.executemany(
            """
            INSERT INTO airport_timezone (timezone_name, utc_offset_minutes, display_name)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                utc_offset_minutes = VALUES(utc_offset_minutes),
                display_name = VALUES(display_name)
            """,
            (
                ("America/New_York", -300, "New York UTC-05:00"),
                ("Asia/Shanghai", 480, "Shanghai UTC+08:00"),
                ("Asia/Tokyo", 540, "Tokyo UTC+09:00"),
            ),
        )
        cursor.execute("SHOW COLUMNS FROM airport LIKE 'timezone_name'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE airport ADD COLUMN timezone_name VARCHAR(64) NULL")
        cursor.execute(
            """
            UPDATE airport
            SET timezone_name = CASE
                WHEN airport_code IN ('JFK', 'LGA') THEN 'America/New_York'
                WHEN airport_code IN ('PVG', 'SHA') THEN 'Asia/Shanghai'
                WHEN airport_code IN ('HND', 'NRT') THEN 'Asia/Tokyo'
                ELSE 'Asia/Shanghai'
            END
            WHERE timezone_name IS NULL
            """
        )
        cursor.execute("ALTER TABLE airport MODIFY timezone_name VARCHAR(64) NOT NULL")
        cursor.execute("SHOW COLUMNS FROM airline_staff LIKE 'can_delete'")
        if cursor.fetchone() is None:
            cursor.execute(
                """
                ALTER TABLE airline_staff
                ADD COLUMN can_delete BOOLEAN NOT NULL DEFAULT FALSE AFTER is_operator
                """
            )
    db.commit()
