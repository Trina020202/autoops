# AutoOps Architecture

## System diagram

```text
Browser
  |
  v
Flask routes
  |
  v
Copilot intent parser + SQL templates
  |
  v
Jinja templates + CSS
  |
  v
sqlite3 data access
  |
  v
SQLite database
```

## Route map

| Route | Purpose |
| --- | --- |
| `/login` | Sign in with demo account |
| `/logout` | Clear session |
| `/dashboard` | Metrics, recent sales, stock watch |
| `/copilot` | Natural-language analytics assistant |
| `/vehicles` | Search/filter inventory |
| `/vehicles/new` | Add vehicle |
| `/vehicles/<id>/edit` | Edit vehicle |
| `/customers` | Search customer records |
| `/customers/new` | Add customer |
| `/sales` | View sales records |
| `/sales/new` | Create pending or completed sale |
| `/sales/<id>/complete` | Complete pending sale and update inventory |

## Data model

```text
users
  id
  name
  email
  password_hash
  role

vehicles
  id
  vin
  brand
  model
  year
  price
  color
  mileage
  status
  acquired_at

customers
  id
  name
  phone
  email
  city

sales
  id
  vehicle_id -> vehicles.id
  customer_id -> customers.id
  sales_rep
  sale_price
  status
  sold_at
  notes
```

## Business rules

- Vehicle price must be greater than zero.
- Vehicle mileage cannot be negative.
- VIN must be unique.
- Sold vehicles cannot be sold again.
- Sale date cannot be earlier than the vehicle acquired date.
- Completed sale updates vehicle status to `sold`.
- Pending sale updates vehicle status to `reserved`.
- Copilot only runs predefined read-only SELECT templates.
- Questions containing write-operation keywords such as DROP, DELETE, UPDATE, INSERT, ALTER, or TRUNCATE are blocked.
