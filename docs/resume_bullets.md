# Resume Bullets

Use only the claims that are true at the time you submit the resume.

## Product or technical product version

AutoOps Car Sales Operations Dashboard | Full-stack personal project

- Independently built and deployed a full-stack dealership operations dashboard covering product scope, data model design, Flask backend development, server-rendered UI, and live demo delivery.
- Implemented login, vehicle search/filtering, vehicle creation/editing, customer records, sales creation, pending-to-completed deal workflow, and automatic inventory status updates.
- Built SQL-backed dashboard metrics and a template-based NL2SQL Copilot, enabling users to ask natural-language questions about brand sales, revenue ranking, inventory, sales reps, monthly trends, and customer value.
- Prepared GitHub-ready documentation including README, PRD, architecture notes, database schema, seed data, test account, screenshots, local run instructions, and Render live demo.

## Software engineering version

AutoOps Car Sales Operations Dashboard | Flask, SQLite, HTML/CSS

- Developed a Flask web application with protected routes, session-based login, sqlite3 data access, Jinja templates, and responsive CSS for dealership inventory and sales operations.
- Designed relational tables for users, vehicles, customers, and sales, adding validation for unique VINs, positive prices, non-negative mileage, sale date consistency, and sold-vehicle constraints.
- Implemented sales workflow logic that reserves vehicles for pending deals and marks vehicles as sold after completed sales, keeping inventory and dashboard data synchronized.
- Added a safe rule-based NL2SQL layer with intent detection, entity extraction, read-only SQL templates, result tables, and bar chart output.
- Added unit tests for login, dashboard access, inventory search, vehicle validation, completed-sale inventory updates, Copilot query generation, and write-query blocking.

## After GitHub is public

Add this only after pushing the repository:

- Published the project on GitHub with setup instructions, seed data, test account, product documentation, and screenshots for recruiter review.

## After cloud deployment works

Add this only after the app is live:

- Deployed the Flask application with Gunicorn and environment-based configuration, enabling recruiters to access a live demo.

Live demo link:

- https://autoops-xzto.onrender.com
