# AutoOps PRD

## 1. Product overview

AutoOps is an internal web console for a car dealership team. It helps sales and operations staff keep vehicle inventory, customer records, sales status, and business metrics in one place.

## 2. Target users

- Sales representative: searches inventory, creates sales records, updates deal progress.
- Operations manager: monitors active inventory, monthly units, revenue, stock aging, and sales rep performance.
- Product or data analyst: asks natural-language questions about brands, revenue, inventory, sales representatives, trends, and customers.
- Customer support staff: checks customer information and purchase history.

## 3. Problems

- Inventory status is easy to lose across spreadsheets and chat messages.
- Sales records are updated manually, so dashboards lag behind real operations.
- Managers need quick visibility into revenue, slow-moving stock, and rep performance.
- Non-technical users need a faster way to ask operating questions without writing SQL.

## 4. Core workflow

```text
Login
  -> Dashboard
  -> Vehicle search
  -> Create sale
  -> Mark sale completed
  -> Vehicle becomes sold
  -> Metrics update automatically
  -> Ask Copilot a natural-language analytics question
  -> Review generated SQL, result table, and chart
```

## 5. MVP scope

### Included

- Login
- Vehicle CRUD for create, read, update
- Inventory search and filters
- Customer creation and search
- Sales creation
- Pending-to-completed sale transition
- Dashboard metrics and simple visual bars
- AutoOps Copilot for template-based natural-language analytics
- Local seed data

### Not included yet

- Cloud PostgreSQL database
- Role-based permissions
- File upload
- Payment and finance approval integration
- Large language model integration
- Mobile app or mini program

## 6. Success metrics

- User can complete the core workflow in under two minutes.
- Vehicle status changes automatically after a completed sale.
- Dashboard shows updated units and revenue without manual spreadsheet work.
- Copilot can answer common analytics questions such as top brands, revenue ranking, inventory by brand, sales rep performance, monthly trends, and customer value.
- The project can be run locally by another person using README instructions.

## 7. Risks and tradeoffs

- SQLite is suitable for local demo speed but should be replaced with PostgreSQL for production deployment.
- The current dashboard uses server-rendered HTML and CSS bars to avoid front-end dependency complexity.
- Copilot uses safe SQL templates rather than arbitrary SQL execution, trading flexibility for demo reliability and security.
- Authentication is intentionally simple for MVP; production should add password reset, stronger secrets, and roles.
