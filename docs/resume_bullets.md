# Resume Bullets

Use only the claims that are true at the time you submit the resume.

## AI product or technical product version

AutoOps AI Sales Analyst | Full-stack personal productization project

- Independently built and deployed a full-stack dealership operations dashboard covering product scope, data model design, Flask backend development, server-rendered UI, and live demo delivery.
- Implemented login, vehicle search/filtering, vehicle creation/editing, customer records, sales creation, pending-to-completed deal workflow, and automatic inventory status updates.
- Built SQL-backed dashboard metrics and an AI Sales Analyst with RAG-style database knowledge retrieval, safe NL2SQL generation, tool-calling workflow, result tables, bar charts, and business insight reports.
- Added a multi-step diagnosis flow for sales decline questions, combining retrieved business rules, revenue trend queries, inventory analysis, pending pipeline analysis, metric calculation, and action recommendations.
- Prepared GitHub-ready documentation including README, PRD, architecture notes, database schema, seed data, test account, screenshots, local run instructions, and Render live demo.

## Software engineering version

AutoOps Car Sales Operations Dashboard | Flask, SQLite, HTML/CSS

- Developed a Flask web application with protected routes, session-based login, sqlite3 data access, Jinja templates, and responsive CSS for dealership inventory and sales operations.
- Designed relational tables for users, vehicles, customers, and sales, adding validation for unique VINs, positive prices, non-negative mileage, sale date consistency, and sold-vehicle constraints.
- Implemented sales workflow logic that reserves vehicles for pending deals and marks vehicles as sold after completed sales, keeping inventory and dashboard data synchronized.
- Added a safe NL2SQL and agent layer with intent detection, entity extraction, RAG-style documentation retrieval, read-only SQL execution, tool-call traces, result tables, and bar chart output.
- Added unit tests for login, dashboard access, inventory search, vehicle validation, completed-sale inventory updates, AI Sales Analyst query generation, brand comparison, sales decline diagnosis, and write-query blocking.

## Conservative resume version

Use this if the application reviewers may question the term AI Agent:

- Built a RAG-style database assistant that retrieves schema documentation, business rules, metric definitions, and SQL examples to improve NL2SQL query grounding for dealership operations analysis.
- Implemented a tool-calling style workflow that executes read-only SQL, calculates operating metrics, generates chart data, and produces short business insight reports for natural-language sales questions.

## After GitHub is public

Add this only after pushing the repository:

- Published the project on GitHub with setup instructions, seed data, test account, product documentation, and screenshots for recruiter review.

## After cloud deployment works

Add this only after the app is live:

- Deployed the Flask application with Gunicorn and environment-based configuration, enabling recruiters to access a live demo.

Live demo link:

- https://autoops-xzto.onrender.com
