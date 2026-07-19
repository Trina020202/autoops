import sqlite3
from pathlib import Path

from flask import current_app, g
from werkzeug.security import generate_password_hash


DEMO_DATA_VERSION = "2026-07-19-agent-analytics"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    base = Path(current_app.root_path).parent

    schema_sql = (base / "database" / "schema.sql").read_text()
    seed_sql = (base / "database" / "seed.sql").read_text()

    db.executescript(schema_sql)
    db.execute(
        """
        INSERT INTO users (name, email, password_hash, role)
        VALUES (?, ?, ?, ?)
        """,
        (
            "Demo Admin",
            "demo@autoops.local",
            generate_password_hash("autoops123"),
            "Operations Manager",
        ),
    )
    db.executescript(seed_sql)
    db.execute(
        """
        INSERT INTO app_metadata (key, value)
        VALUES ('demo_data_version', ?)
        """,
        (DEMO_DATA_VERSION,),
    )
    db.commit()


def ensure_database():
    db_path = Path(current_app.config["DATABASE"])
    if current_app.config.get("TESTING"):
        return
    if not db_path.exists():
        init_db()
    else:
        ensure_runtime_schema()
        if current_app.config.get("AUTOOPS_RESET_DEMO_DATA"):
            init_db()
        elif get_demo_data_version() != DEMO_DATA_VERSION:
            init_db()


def ensure_runtime_schema():
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS app_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS agent_runs (
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

        CREATE INDEX IF NOT EXISTS idx_agent_runs_created_at ON agent_runs(created_at);
        CREATE INDEX IF NOT EXISTS idx_agent_runs_intent ON agent_runs(intent);
        """
    )
    db.commit()


def get_demo_data_version():
    db = get_db()
    row = db.execute(
        """
        SELECT value
        FROM app_metadata
        WHERE key = 'demo_data_version'
        """
    ).fetchone()
    return row["value"] if row else None


def init_app(app):
    app.teardown_appcontext(close_db)
