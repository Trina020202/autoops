import sqlite3
from pathlib import Path

from flask import current_app, g
from werkzeug.security import generate_password_hash


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
    db.commit()


def ensure_database():
    db_path = Path(current_app.config["DATABASE"])
    if current_app.config.get("TESTING"):
        return
    if not db_path.exists():
        init_db()


def init_app(app):
    app.teardown_appcontext(close_db)
