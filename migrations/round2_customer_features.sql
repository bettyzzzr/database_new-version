USE air_ticket_reservation;

ALTER TABLE ticket
    ADD COLUMN ticket_status ENUM('active', 'cancelled') NOT NULL DEFAULT 'active' AFTER sold_price;

CREATE TABLE IF NOT EXISTS booking_order (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_email VARCHAR(255) NOT NULL,
    booking_type ENUM('one_way', 'round_trip') NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    order_status ENUM('confirmed', 'cancelled') NOT NULL DEFAULT 'confirmed',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_email) REFERENCES customer(email)
);

CREATE TABLE IF NOT EXISTS booking_order_segment (
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

CREATE TABLE IF NOT EXISTS refund (
    refund_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id INT NOT NULL,
    refund_amount DECIMAL(10, 2) NOT NULL,
    refund_status ENUM('requested', 'approved', 'rejected') NOT NULL DEFAULT 'requested',
    requested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES ticket(ticket_id)
);

CREATE TABLE IF NOT EXISTS waitlist (
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

CREATE TABLE IF NOT EXISTS wishlist (
    wishlist_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_email VARCHAR(255) NOT NULL,
    airline_name VARCHAR(100) NOT NULL,
    flight_num VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_wishlist_customer_flight (customer_email, airline_name, flight_num),
    FOREIGN KEY (customer_email) REFERENCES customer(email),
    FOREIGN KEY (airline_name, flight_num) REFERENCES flight(airline_name, flight_num)
);

CREATE TABLE IF NOT EXISTS frequent_search (
    search_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_email VARCHAR(255) NOT NULL,
    origin_input VARCHAR(255) NOT NULL,
    destination_input VARCHAR(255) NOT NULL,
    search_date DATE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_email) REFERENCES customer(email)
);
