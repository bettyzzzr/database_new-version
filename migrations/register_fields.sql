USE air_ticket_reservation;

ALTER TABLE customer
    ADD COLUMN passport_number VARCHAR(50) NULL,
    ADD COLUMN passport_expiration DATE NULL,
    ADD COLUMN passport_country VARCHAR(100) NULL;

UPDATE customer
SET
    passport_number = CONCAT('LEGACY-', LEFT(MD5(email), 12)),
    passport_expiration = '2030-12-31',
    passport_country = 'Unknown'
WHERE passport_number IS NULL;

ALTER TABLE customer
    MODIFY passport_number VARCHAR(50) NOT NULL,
    MODIFY passport_expiration DATE NOT NULL,
    MODIFY passport_country VARCHAR(100) NOT NULL,
    ADD UNIQUE KEY uq_customer_passport_number (passport_number);

ALTER TABLE booking_agent
    ADD COLUMN name VARCHAR(100) NULL AFTER email;

UPDATE booking_agent
SET name = SUBSTRING_INDEX(email, '@', 1)
WHERE name IS NULL;

ALTER TABLE booking_agent
    MODIFY name VARCHAR(100) NOT NULL;

ALTER TABLE airline_staff
    ADD COLUMN email VARCHAR(255) NULL AFTER username;

UPDATE airline_staff
SET email = CONCAT(username, '@example.com')
WHERE email IS NULL;

ALTER TABLE airline_staff
    MODIFY email VARCHAR(255) NOT NULL,
    ADD UNIQUE KEY uq_airline_staff_email (email);
