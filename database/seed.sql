INSERT INTO vehicles (vin, brand, model, year, price, color, mileage, status, acquired_at) VALUES
('XP7G620250001', 'XPeng', 'G6 580 Max', 2025, 31200, 'Arctic White', 1200, 'available', '2026-04-11'),
('XP7P720250002', 'XPeng', 'P7i 702 Max', 2025, 38400, 'Graphite Gray', 850, 'reserved', '2026-05-03'),
('BYDATTO300003', 'BYD', 'Atto 3 Extended', 2024, 28600, 'Surf Blue', 4200, 'available', '2026-03-18'),
('TESM3RWD00004', 'Tesla', 'Model 3 RWD', 2024, 36500, 'Pearl White', 5100, 'sold', '2026-01-21'),
('NIOES60000005', 'NIO', 'ES6 75kWh', 2024, 42100, 'Deep Black', 3100, 'available', '2026-02-14'),
('LI24L7000006', 'Li Auto', 'L7 Pro', 2024, 39700, 'Silver', 2600, 'sold', '2026-02-28'),
('XP9X920250007', 'XPeng', 'X9 Ultra', 2025, 50200, 'Starship Gray', 760, 'available', '2026-06-19'),
('BYDSEAL000008', 'BYD', 'Seal Performance', 2024, 33800, 'Atlantis Gray', 7300, 'available', '2026-04-27'),
('AITO7UL000009', 'AITO', 'M7 Ultra', 2025, 44200, 'Warm White', 1400, 'reserved', '2026-05-30'),
('ZEEKR70000010', 'Zeekr', '007 Long Range', 2025, 35800, 'Dawn Blue', 980, 'available', '2026-06-02');

INSERT INTO customers (name, phone, email, city) VALUES
('Mia Chen', '+61 400 102 301', 'mia.chen@example.com', 'Sydney'),
('Leo Wang', '+61 411 223 344', 'leo.wang@example.com', 'Melbourne'),
('Ava Liu', '+61 422 987 654', 'ava.liu@example.com', 'Brisbane'),
('Noah Zhang', '+61 433 555 212', 'noah.zhang@example.com', 'Sydney'),
('Grace Xu', '+61 444 876 909', 'grace.xu@example.com', 'Adelaide'),
('Ethan Li', '+61 455 341 778', 'ethan.li@example.com', 'Perth');

INSERT INTO sales (vehicle_id, customer_id, sales_rep, sale_price, status, sold_at, notes) VALUES
(4, 1, 'Cindy Zhou', 35800, 'completed', '2026-02-09', 'Finance approved in two days.'),
(6, 2, 'Alex Tan', 38900, 'completed', '2026-03-22', 'Trade-in customer.'),
(2, 3, 'Cindy Zhou', 37900, 'pending', '2026-07-10', 'Waiting for delivery slot.'),
(9, 4, 'Daniel Wu', 43800, 'pending', '2026-07-12', 'Customer requested ceramic coating.'),
(1, 5, 'Alex Tan', 30500, 'completed', '2026-07-03', 'Corporate employee discount.'),
(8, 6, 'Cindy Zhou', 32900, 'completed', '2026-06-18', 'Online lead converted after test drive.');
