DROP DATABASE IF EXISTS air_ticket_reservation;
CREATE DATABASE air_ticket_reservation CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE air_ticket_reservation;

CREATE TABLE city (
    city_id INT AUTO_INCREMENT PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE city_alias (
    alias_id INT AUTO_INCREMENT PRIMARY KEY,
    city_id INT NOT NULL,
    alias_name VARCHAR(100) NOT NULL UNIQUE,
    FOREIGN KEY (city_id) REFERENCES city(city_id)
        ON DELETE CASCADE
);

CREATE TABLE airport_timezone (
    timezone_name VARCHAR(64) PRIMARY KEY,
    utc_offset_minutes INT NOT NULL,
    display_name VARCHAR(100) NOT NULL
);

CREATE TABLE airport (
    airport_code CHAR(3) PRIMARY KEY,
    airport_name VARCHAR(100) NOT NULL,
    city_id INT NOT NULL,
    timezone_name VARCHAR(64) NOT NULL,
    FOREIGN KEY (city_id) REFERENCES city(city_id),
    FOREIGN KEY (timezone_name) REFERENCES airport_timezone(timezone_name)
);

CREATE TABLE airline (
    airline_name VARCHAR(100) PRIMARY KEY
);

CREATE TABLE airplane (
    airplane_id INT PRIMARY KEY,
    airline_name VARCHAR(100) NOT NULL,
    seats INT NOT NULL CHECK (seats > 0),
    FOREIGN KEY (airline_name) REFERENCES airline(airline_name)
        ON DELETE CASCADE
);

CREATE TABLE flight (
    airline_name VARCHAR(100) NOT NULL,
    flight_num VARCHAR(20) NOT NULL,
    departure_airport CHAR(3) NOT NULL,
    departure_time DATETIME NOT NULL,
    departure_time_utc DATETIME NOT NULL,
    arrival_airport CHAR(3) NOT NULL,
    arrival_time DATETIME NOT NULL,
    arrival_time_utc DATETIME NOT NULL,
    price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
    status ENUM('scheduled', 'delayed', 'cancelled') NOT NULL DEFAULT 'scheduled',
    airplane_id INT NOT NULL,
    PRIMARY KEY (airline_name, flight_num),
    FOREIGN KEY (airline_name) REFERENCES airline(airline_name)
        ON DELETE CASCADE,
    FOREIGN KEY (departure_airport) REFERENCES airport(airport_code),
    FOREIGN KEY (arrival_airport) REFERENCES airport(airport_code),
    FOREIGN KEY (airplane_id) REFERENCES airplane(airplane_id)
);

CREATE TABLE customer (
    email VARCHAR(255) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    passport_number VARCHAR(50) NOT NULL UNIQUE,
    passport_expiration DATE NOT NULL,
    passport_country VARCHAR(100) NOT NULL
);

CREATE TABLE booking_agent (
    email VARCHAR(255) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    booking_agent_id INT NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE airline_staff (
    username VARCHAR(100) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    airline_name VARCHAR(100) NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    is_operator BOOLEAN NOT NULL DEFAULT FALSE,
    can_delete BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (airline_name) REFERENCES airline(airline_name)
);

CREATE TABLE booking_agent_work_for (
    email VARCHAR(255) NOT NULL,
    airline_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (email, airline_name),
    FOREIGN KEY (email) REFERENCES booking_agent(email)
        ON DELETE CASCADE,
    FOREIGN KEY (airline_name) REFERENCES airline(airline_name)
        ON DELETE CASCADE
);

CREATE TABLE ticket (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    airline_name VARCHAR(100) NOT NULL,
    flight_num VARCHAR(20) NOT NULL,
    customer_email VARCHAR(255) NOT NULL,
    booking_agent_email VARCHAR(255),
    sold_price DECIMAL(10, 2) NOT NULL,
    ticket_status ENUM('active', 'cancelled') NOT NULL DEFAULT 'active',
    purchase_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (airline_name, flight_num) REFERENCES flight(airline_name, flight_num),
    FOREIGN KEY (customer_email) REFERENCES customer(email),
    FOREIGN KEY (booking_agent_email) REFERENCES booking_agent(email)
);

CREATE TABLE booking_order (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_email VARCHAR(255) NOT NULL,
    booking_type ENUM('one_way', 'round_trip') NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    order_status ENUM('confirmed', 'cancelled') NOT NULL DEFAULT 'confirmed',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_email) REFERENCES customer(email)
);

CREATE TABLE booking_order_segment (
    segment_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    segment_index INT NOT NULL,
    ticket_id INT NOT NULL,
    airline_name VARCHAR(100) NOT NULL,
    flight_num VARCHAR(20) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES booking_order(order_id)
        ON DELETE CASCADE,
    FOREIGN KEY (ticket_id) REFERENCES ticket(ticket_id),
    FOREIGN KEY (airline_name, flight_num) REFERENCES flight(airline_name, flight_num)
);

CREATE TABLE refund (
    refund_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    refund_amount DECIMAL(10, 2) NOT NULL,
    refund_status ENUM('requested', 'approved', 'rejected') NOT NULL DEFAULT 'requested',
    requested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES ticket(ticket_id)
);

CREATE TABLE waitlist (
    waitlist_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_email VARCHAR(255) NOT NULL,
    airline_name VARCHAR(100) NOT NULL,
    flight_num VARCHAR(20) NOT NULL,
    request_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status ENUM('waiting', 'notified', 'converted') NOT NULL DEFAULT 'waiting',
    UNIQUE KEY uq_waitlist_customer_flight_status (customer_email, airline_name, flight_num, status),
    FOREIGN KEY (customer_email) REFERENCES customer(email),
    FOREIGN KEY (airline_name, flight_num) REFERENCES flight(airline_name, flight_num)
);

CREATE TABLE wishlist (
    wishlist_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_email VARCHAR(255) NOT NULL,
    airline_name VARCHAR(100) NOT NULL,
    flight_num VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_wishlist_customer_flight (customer_email, airline_name, flight_num),
    FOREIGN KEY (customer_email) REFERENCES customer(email),
    FOREIGN KEY (airline_name, flight_num) REFERENCES flight(airline_name, flight_num)
);

CREATE TABLE frequent_search (
    search_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_email VARCHAR(255) NOT NULL,
    origin_input VARCHAR(255) NOT NULL,
    destination_input VARCHAR(255) NOT NULL,
    search_date DATE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_email) REFERENCES customer(email)
);

CREATE TABLE audit_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actor_role VARCHAR(50) NOT NULL,
    actor_id VARCHAR(255) NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    target_type VARCHAR(100) NOT NULL,
    target_id VARCHAR(255) NOT NULL,
    details TEXT
);

CREATE VIEW flight_status_view AS
SELECT
    f.airline_name,
    f.flight_num,
    f.departure_airport,
    f.departure_time,
    f.departure_time_utc,
    f.arrival_airport,
    f.arrival_time,
    f.arrival_time_utc,
    f.price,
    f.status,
    f.airplane_id,
    CASE
        WHEN f.status IN ('delayed', 'cancelled') THEN f.status
        WHEN UTC_TIMESTAMP() < f.departure_time_utc THEN 'upcoming'
        WHEN UTC_TIMESTAMP() < f.arrival_time_utc THEN 'in_progress'
        ELSE 'completed'
    END AS current_status
FROM flight f;
