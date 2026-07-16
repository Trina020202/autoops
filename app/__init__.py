import os

from flask import Flask, redirect, url_for


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        DATABASE=os.environ.get(
            "AUTOOPS_DATABASE",
            os.path.join(app.instance_path, "autoops.sqlite"),
        ),
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    from . import db

    db.init_app(app)

    from .routes import auth, main

    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)

    @app.route("/")
    def index():
        return redirect(url_for("main.dashboard"))

    with app.app_context():
        db.ensure_database()

    return app
