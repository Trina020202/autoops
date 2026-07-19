# AutoOps PRD

## 1. Product overview

AutoOps is an internal web console for a car dealership team. It helps sales and operations staff keep vehicle inventory, customer records, sales status, and business metrics in one place. It also includes an AI Sales Analyst that turns natural-language business questions into grounded database analysis.

## 2. Target users

- Sales representative: searches inventory, creates sales records, updates deal progress.
- Operations manager: monitors active inventory, monthly units, revenue, stock aging, and sales rep performance.
- Product or data analyst: asks natural-language questions about brands, revenue, inventory, sales representatives, trends, and customers.
- Sales manager: asks diagnosis questions such as why sales decreased and receives trend, inventory, pipeline, and action analysis.
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
  -> Review retrieved database knowledge, agent plan, generated SQL, result table, chart, tool calls, and analyst report
  -> Review Evaluation Console for safety status, latency, success rate, and tool-call metrics
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
- AutoOps AI Sales Analyst for RAG-style database knowledge retrieval and template-based natural-language analytics
- Tool-call traces for database querying, metric calculation, chart generation, and report generation
- Multi-step sales decline diagnosis using completed revenue trend, active inventory, pending pipeline, and Q2 brand mix
- SQL Sandbox that blocks write-operation intent, validates SELECT-only execution, and caps result size
- Evaluation Console with reference cases, run logs, intent success rate, latency, retrieved chunks, tool count, and estimated token usage
- Local seed data

### Not included yet

- Cloud PostgreSQL database
- Role-based permissions
- File upload
- Payment and finance approval integration
- Live large language model integration requiring an external API key
- Vector database such as FAISS or Chroma
- Mobile app or mini program

## 6. Success metrics

- User can complete the core workflow in under two minutes.
- Vehicle status changes automatically after a completed sale.
- Dashboard shows updated units and revenue without manual spreadsheet work.
- AI Sales Analyst can answer common analytics questions such as top brands, revenue ranking, inventory by brand, sales rep performance, monthly trends, and customer value.
- AI Sales Analyst can show the retrieved schema/business-rule context and the tool calls used to produce the answer.
- AI Sales Analyst can run at least one multi-step diagnosis workflow and produce a business recommendation report.
- Evaluation Console shows recent agent runs, intent success rate, latency, tool count, row count, and guardrail status.
- The project can be run locally by another person using README instructions.

## 7. Risks and tradeoffs

- SQLite is suitable for local demo speed but should be replaced with PostgreSQL for production deployment.
- The current dashboard uses server-rendered HTML and CSS bars to avoid front-end dependency complexity.
- AI Sales Analyst uses deterministic local retrieval and safe SQL templates rather than arbitrary SQL execution, trading flexibility for demo reliability and security.
- The current RAG-style retrieval is keyword-based over local documentation, so it demonstrates the product workflow without requiring a live LLM or vector database.
- Agent observability metrics are approximate for demo purposes; token usage is estimated from prompt, retrieved context, SQL, and report length.
- Authentication is intentionally simple for MVP; production should add password reset, stronger secrets, and roles.
