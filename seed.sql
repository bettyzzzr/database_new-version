USE air_ticket_reservation;

INSERT INTO city (city_name) VALUES
('New York'),
('Shanghai'),
('Tokyo');

INSERT INTO city_alias (city_id, alias_name)
SELECT city_id, 'NYC' FROM city WHERE city_name = 'New York';
INSERT INTO city_alias (city_id, alias_name)
SELECT city_id, 'New York City' FROM city WHERE city_name = 'New York';
INSERT INTO city_alias (city_id, alias_name)
SELECT city_id, 'SH' FROM city WHERE city_name = 'Shanghai';
INSERT INTO city_alias (city_id, alias_name)
SELECT city_id, '上海' FROM city WHERE city_name = 'Shanghai';
INSERT INTO city_alias (city_id, alias_name)
SELECT city_id, 'TYO' FROM city WHERE city_name = 'Tokyo';

INSERT INTO airport (airport_code, airport_name, city_id)
SELECT 'JFK', 'John F. Kennedy International Airport', city_id FROM city WHERE city_name = 'New York';
INSERT INTO airport (airport_code, airport_name, city_id)
SELECT 'LGA', 'LaGuardia Airport', city_id FROM city WHERE city_name = 'New York';
INSERT INTO airport (airport_code, airport_name, city_id)
SELECT 'PVG', 'Shanghai Pudong International Airport', city_id FROM city WHERE city_name = 'Shanghai';
INSERT INTO airport (airport_code, airport_name, city_id)
SELECT 'SHA', 'Shanghai Hongqiao International Airport', city_id FROM city WHERE city_name = 'Shanghai';
INSERT INTO airport (airport_code, airport_name, city_id)
SELECT 'HND', 'Tokyo Haneda Airport', city_id FROM city WHERE city_name = 'Tokyo';
INSERT INTO airport (airport_code, airport_name, city_id)
SELECT 'NRT', 'Narita International Airport', city_id FROM city WHERE city_name = 'Tokyo';

INSERT INTO airline (airline_name) VALUES
('BlueSky Airlines'),
('Dragon Air');

INSERT INTO airplane (airplane_id, airline_name, seats) VALUES
(1001, 'BlueSky Airlines', 2),
(1002, 'BlueSky Airlines', 120),
(1003, 'BlueSky Airlines', 1),
(2001, 'Dragon Air', 2),
(2002, 'Dragon Air', 180);

INSERT INTO flight (
    airline_name, flight_num, departure_airport, departure_time, departure_time_utc,
    arrival_airport, arrival_time, arrival_time_utc, price, status, airplane_id
) VALUES
('BlueSky Airlines', 'BS101', 'JFK', DATE_ADD(UTC_TIMESTAMP(), INTERVAL 1 DAY), DATE_ADD(UTC_TIMESTAMP(), INTERVAL 1 DAY),
 'PVG', DATE_ADD(UTC_TIMESTAMP(), INTERVAL 39 HOUR), DATE_ADD(UTC_TIMESTAMP(), INTERVAL 39 HOUR), 850.00, 'scheduled', 1002),
('BlueSky Airlines', 'BS102', 'LGA', DATE_ADD(UTC_TIMESTAMP(), INTERVAL 2 DAY), DATE_ADD(UTC_TIMESTAMP(), INTERVAL 2 DAY),
 'SHA', DATE_ADD(UTC_TIMESTAMP(), INTERVAL 63 HOUR), DATE_ADD(UTC_TIMESTAMP(), INTERVAL 63 HOUR), 790.00, 'scheduled', 1003),
('BlueSky Airlines', 'BS201', 'JFK', DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 HOUR), DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 HOUR),
 'HND', DATE_ADD(UTC_TIMESTAMP(), INTERVAL 8 HOUR), DATE_ADD(UTC_TIMESTAMP(), INTERVAL 8 HOUR), 920.00, 'scheduled', 1002),
('BlueSky Airlines', 'BS301', 'PVG', DATE_SUB(UTC_TIMESTAMP(), INTERVAL 2 DAY), DATE_SUB(UTC_TIMESTAMP(), INTERVAL 2 DAY),
 'JFK', DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 DAY), DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 DAY), 870.00, 'scheduled', 1002),
('BlueSky Airlines', 'BS401', 'SHA', DATE_ADD(UTC_TIMESTAMP(), INTERVAL 3 DAY), DATE_ADD(UTC_TIMESTAMP(), INTERVAL 3 DAY),
 'NRT', DATE_ADD(UTC_TIMESTAMP(), INTERVAL 75 HOUR), DATE_ADD(UTC_TIMESTAMP(), INTERVAL 75 HOUR), 420.00, 'delayed', 1001),
('BlueSky Airlines', 'BS999', 'JFK', DATE_ADD(UTC_TIMESTAMP(), INTERVAL 4 DAY), DATE_ADD(UTC_TIMESTAMP(), INTERVAL 4 DAY),
 'LGA', DATE_ADD(UTC_TIMESTAMP(), INTERVAL 97 HOUR), DATE_ADD(UTC_TIMESTAMP(), INTERVAL 97 HOUR), 99.00, 'scheduled', 1001),
('Dragon Air', 'DA100', 'PVG', DATE_ADD(UTC_TIMESTAMP(), INTERVAL 1 DAY), DATE_ADD(UTC_TIMESTAMP(), INTERVAL 1 DAY),
 'HND', DATE_ADD(UTC_TIMESTAMP(), INTERVAL 27 HOUR), DATE_ADD(UTC_TIMESTAMP(), INTERVAL 27 HOUR), 360.00, 'scheduled', 2002),
('Dragon Air', 'DA101', 'SHA', DATE_ADD(UTC_TIMESTAMP(), INTERVAL 3 DAY), DATE_ADD(UTC_TIMESTAMP(), INTERVAL 3 DAY),
 'NRT', DATE_ADD(UTC_TIMESTAMP(), INTERVAL 75 HOUR), DATE_ADD(UTC_TIMESTAMP(), INTERVAL 75 HOUR), 365.00, 'scheduled', 2002),
('Dragon Air', 'DA200', 'SHA', DATE_ADD(UTC_TIMESTAMP(), INTERVAL 2 DAY), DATE_ADD(UTC_TIMESTAMP(), INTERVAL 2 DAY),
 'NRT', DATE_ADD(UTC_TIMESTAMP(), INTERVAL 51 HOUR), DATE_ADD(UTC_TIMESTAMP(), INTERVAL 51 HOUR), 380.00, 'cancelled', 2002),
('Dragon Air', 'DA300', 'PVG', DATE_ADD(UTC_TIMESTAMP(), INTERVAL 5 DAY), DATE_ADD(UTC_TIMESTAMP(), INTERVAL 5 DAY),
 'JFK', DATE_ADD(UTC_TIMESTAMP(), INTERVAL 135 HOUR), DATE_ADD(UTC_TIMESTAMP(), INTERVAL 135 HOUR), 900.00, 'scheduled', 2001);

INSERT INTO customer (email, name, password_hash, passport_number, passport_expiration, passport_country) VALUES
('alice@example.com', 'Alice Customer', 'pbkdf2:sha256:600000$custosalt$45b7fffdd25be62e5b52738e0617b4690366b390866edc5f6d0aa1284eda38a7', 'P1000001', '2031-12-31', 'United States'),
('bob@example.com', 'Bob Customer', 'pbkdf2:sha256:600000$custosalt$45b7fffdd25be62e5b52738e0617b4690366b390866edc5f6d0aa1284eda38a7', 'P1000002', '2030-06-30', 'United States');

INSERT INTO booking_agent (email, name, booking_agent_id, password_hash) VALUES
('agent@example.com', 'Demo Agent', 501, 'pbkdf2:sha256:600000$agentsalt$91e7cf1a2c71778e0b5a3fb5d70fc7fd0ae128fc976045f3dd42b94854618138');

INSERT INTO airline_staff (username, email, password_hash, first_name, last_name, airline_name, is_admin, is_operator) VALUES
('admin_blue', 'admin_blue@example.com', 'pbkdf2:sha256:600000$adminsalt$2823d26f83e838fe557e6c03352e212d01d00f773f558db620afec38cd313295', 'Ada', 'Admin', 'BlueSky Airlines', TRUE, FALSE),
('operator_blue', 'operator_blue@example.com', 'pbkdf2:sha256:600000$operasalt$1657db469791d6443782a839f771efb245a1a54a15acd096ae4ce2a260e33661', 'Oscar', 'Operator', 'BlueSky Airlines', FALSE, TRUE),
('staff_both', 'staff_both@example.com', 'pbkdf2:sha256:600000$staffsalt$f2f4ae6e6bcab02a9b91229cf92ccd4c7fac6a3c4e56cf86ce46797c018a3231', 'Sam', 'Staff', 'BlueSky Airlines', TRUE, TRUE);

INSERT INTO booking_agent_work_for (email, airline_name) VALUES
('agent@example.com', 'BlueSky Airlines');

INSERT INTO ticket (airline_name, flight_num, customer_email, booking_agent_email, sold_price, purchase_date) VALUES
('BlueSky Airlines', 'BS101', 'alice@example.com', NULL, 850.00, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 2 DAY)),
('BlueSky Airlines', 'BS301', 'alice@example.com', NULL, 870.00, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 10 DAY)),
('BlueSky Airlines', 'BS102', 'bob@example.com', 'agent@example.com', 790.00, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 3 DAY)),
('BlueSky Airlines', 'BS999', 'alice@example.com', NULL, 99.00, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 DAY)),
('BlueSky Airlines', 'BS999', 'bob@example.com', 'agent@example.com', 99.00, DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 DAY));
