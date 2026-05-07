USE air_ticket_reservation;

CREATE TABLE IF NOT EXISTS airport_timezone (
    timezone_name VARCHAR(64) PRIMARY KEY,
    utc_offset_minutes INT NOT NULL,
    display_name VARCHAR(100) NOT NULL
);

INSERT INTO airport_timezone (timezone_name, utc_offset_minutes, display_name) VALUES
('America/New_York', -300, 'New York UTC-05:00'),
('Asia/Shanghai', 480, 'Shanghai UTC+08:00'),
('Asia/Tokyo', 540, 'Tokyo UTC+09:00')
ON DUPLICATE KEY UPDATE
    utc_offset_minutes = VALUES(utc_offset_minutes),
    display_name = VALUES(display_name);

ALTER TABLE airport
    ADD COLUMN IF NOT EXISTS timezone_name VARCHAR(64) NULL;

UPDATE airport
SET timezone_name = CASE
    WHEN airport_code IN ('JFK', 'LGA') THEN 'America/New_York'
    WHEN airport_code IN ('PVG', 'SHA') THEN 'Asia/Shanghai'
    WHEN airport_code IN ('HND', 'NRT') THEN 'Asia/Tokyo'
    ELSE 'Asia/Shanghai'
END
WHERE timezone_name IS NULL;

ALTER TABLE airport
    MODIFY timezone_name VARCHAR(64) NOT NULL;
