DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS agent_runs;
DROP TABLE IF EXISTS vehicles;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS app_metadata;

CREATE TABLE app_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'Staff',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vin TEXT NOT NULL UNIQUE,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    year INTEGER NOT NULL,
    price REAL NOT NULL CHECK (price > 0),
    color TEXT NOT NULL DEFAULT '',
    mileage INTEGER NOT NULL DEFAULT 0 CHECK (mileage >= 0),
    status TEXT NOT NULL DEFAULT 'available'
        CHECK (status IN ('available', 'reserved', 'sold')),
    acquired_at TEXT NOT NULL DEFAULT CURRENT_DATE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    city TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    sales_rep TEXT NOT NULL,
    sale_price REAL NOT NULL CHECK (sale_price > 0),
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'completed', 'cancelled')),
    sold_at TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles (id),
    FOREIGN KEY (customer_id) REFERENCES customers (id)
);

CREATE TABLE agent_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    intent TEXT NOT NULL,
    success INTEGER NOT NULL DEFAULT 1,
    safety_status TEXT NOT NULL DEFAULT 'passed',
    latency_ms INTEGER NOT NULL DEFAULT 0,
    retrieved_chunks INTEGER NOT NULL DEFAULT 0,
    tool_count INTEGER NOT NULL DEFAULT 0,
    row_count INTEGER NOT NULL DEFAULT 0,
    estimated_tokens INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vehicles_status ON vehicles(status);
CREATE INDEX idx_vehicles_brand_model ON vehicles(brand, model);
CREATE INDEX idx_sales_status ON sales(status);
CREATE INDEX idx_sales_sold_at ON sales(sold_at);
CREATE INDEX idx_agent_runs_created_at ON agent_runs(created_at);
CREATE INDEX idx_agent_runs_intent ON agent_runs(intent);
