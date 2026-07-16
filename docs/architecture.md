# AutoOps Architecture

## System diagram

```text
Browser
  |
  v
Flask routes
  |
  v
AI Sales Analyst
  |
  +--> RAG-style knowledge retriever
  |      |
  |      v
  |   database_docs/
  |
  +--> Intent parser + SQL templates
  |
  +--> Tool-calling workflow
         |
         +--> query_database()
         +--> calculate_metric()
         +--> generate_chart()
         +--> generate_report()
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
| `/copilot` | RAG-style AI Sales Analyst and natural-language analytics assistant |
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
- AI Sales Analyst only runs predefined read-only SELECT templates.
- The knowledge retriever reads local database documentation from `database_docs/`.
- Tool-call traces are displayed in the UI for transparency.
- Multi-step diagnosis questions can run multiple read-only queries before generating an insight report.
- Questions containing write-operation keywords such as DROP, DELETE, UPDATE, INSERT, ALTER, or TRUNCATE are blocked.

## AI Sales Analyst design

```text
User question
  |
  v
retrieve_knowledge()
  |
  v
Plan intent or diagnosis workflow
  |
  v
query_database() -----> SQLite
  |
  v
calculate_metric()
  |
  v
generate_chart()
  |
  v
generate_report()
```

The current implementation is deterministic and does not require an LLM API key. This keeps the public demo stable. The module boundary in `app/analyst.py` is designed so an LLM planner, LangChain tools, and FAISS/Chroma retrieval can be added later without rewriting the Flask product surface.
