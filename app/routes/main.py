from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.analyst import run_sales_analyst
from app.db import get_db
from app.routes.auth import login_required

bp = Blueprint("main", __name__)


def money(value):
    return f"${float(value or 0):,.0f}"


@bp.app_template_filter("money")
def money_filter(value):
    return money(value)


@bp.app_template_filter("status_label")
def status_label(value):
    labels = {
        "available": "Available",
        "reserved": "Reserved",
        "sold": "Sold",
        "pending": "Pending",
        "completed": "Completed",
        "cancelled": "Cancelled",
    }
    return labels.get(value, value)


@bp.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    metrics = db.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM vehicles WHERE status != 'sold') AS active_inventory,
            (SELECT COUNT(*) FROM sales WHERE status = 'completed'
                AND strftime('%Y-%m', sold_at) = strftime('%Y-%m', 'now')) AS month_units,
            (SELECT COALESCE(SUM(sale_price), 0) FROM sales WHERE status = 'completed'
                AND strftime('%Y-%m', sold_at) = strftime('%Y-%m', 'now')) AS month_revenue,
            (SELECT COALESCE(AVG(sale_price), 0) FROM sales WHERE status = 'completed') AS avg_deal
        """
    ).fetchone()

    monthly = db.execute(
        """
        SELECT strftime('%Y-%m', sold_at) AS month,
               COUNT(*) AS units,
               COALESCE(SUM(sale_price), 0) AS revenue
        FROM sales
        WHERE status = 'completed'
        GROUP BY month
        ORDER BY month DESC
        LIMIT 6
        """
    ).fetchall()
    monthly = list(reversed(monthly))
    max_revenue = max([row["revenue"] for row in monthly] or [1])

    top_reps = db.execute(
        """
        SELECT sales_rep, COUNT(*) AS units, COALESCE(SUM(sale_price), 0) AS revenue
        FROM sales
        WHERE status = 'completed'
        GROUP BY sales_rep
        ORDER BY revenue DESC
        LIMIT 5
        """
    ).fetchall()
    max_rep_revenue = max([row["revenue"] for row in top_reps] or [1])

    recent_sales = db.execute(
        """
        SELECT s.*, v.brand, v.model, c.name AS customer_name
        FROM sales s
        JOIN vehicles v ON v.id = s.vehicle_id
        JOIN customers c ON c.id = s.customer_id
        ORDER BY s.created_at DESC
        LIMIT 6
        """
    ).fetchall()

    stock_alerts = db.execute(
        """
        SELECT id, brand, model, year, price, status,
               CAST(julianday('now') - julianday(acquired_at) AS INTEGER) AS days_in_stock
        FROM vehicles
        WHERE status != 'sold'
        ORDER BY days_in_stock DESC
        LIMIT 5
        """
    ).fetchall()

    return render_template(
        "dashboard.html",
        metrics=metrics,
        monthly=monthly,
        max_revenue=max_revenue,
        top_reps=top_reps,
        max_rep_revenue=max_rep_revenue,
        recent_sales=recent_sales,
        stock_alerts=stock_alerts,
    )


@bp.route("/copilot", methods=("GET", "POST"))
@login_required
def copilot():
    examples = [
        "查询过去三个月销量最高的三个品牌",
        "Compare XPeng and BYD sales performance this year",
        "Analyze why sales decreased in Q2 and suggest actions",
        "本月销售额最高的销售人员",
        "库存最多的五个品牌",
        "查看月度销售额趋势",
    ]
    question = request.form.get("question", request.args.get("q", "")).strip()
    result = run_sales_analyst(get_db(), question) if question else None
    return render_template(
        "copilot.html",
        examples=examples,
        question=question,
        result=result,
    )


@bp.route("/vehicles")
@login_required
def vehicles():
    db = get_db()
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    brand = request.args.get("brand", "").strip()

    filters = []
    params = []
    if q:
        filters.append("(vin LIKE ? OR brand LIKE ? OR model LIKE ? OR color LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like, like, like])
    if status:
        filters.append("status = ?")
        params.append(status)
    if brand:
        filters.append("brand = ?")
        params.append(brand)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows = db.execute(
        f"""
        SELECT *
        FROM vehicles
        {where_clause}
        ORDER BY
            CASE status WHEN 'available' THEN 1 WHEN 'reserved' THEN 2 ELSE 3 END,
            created_at DESC
        """,
        params,
    ).fetchall()
    brands = db.execute("SELECT DISTINCT brand FROM vehicles ORDER BY brand").fetchall()
    return render_template("vehicles.html", vehicles=rows, brands=brands, q=q, status=status, brand=brand)


@bp.route("/vehicles/new", methods=("GET", "POST"))
@login_required
def vehicle_new():
    if request.method == "POST":
        return save_vehicle()
    return render_template("vehicle_form.html", vehicle=None)


@bp.route("/vehicles/<int:vehicle_id>/edit", methods=("GET", "POST"))
@login_required
def vehicle_edit(vehicle_id):
    db = get_db()
    vehicle = db.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)).fetchone()
    if vehicle is None:
        flash("Vehicle not found.", "error")
        return redirect(url_for("main.vehicles"))
    if request.method == "POST":
        return save_vehicle(vehicle_id)
    return render_template("vehicle_form.html", vehicle=vehicle)


def save_vehicle(vehicle_id=None):
    db = get_db()
    form = request.form
    errors = []
    vin = form.get("vin", "").strip().upper()
    brand = form.get("brand", "").strip()
    model = form.get("model", "").strip()
    color = form.get("color", "").strip()
    status = form.get("status", "available")

    try:
        year = int(form.get("year", "0"))
    except ValueError:
        year = 0
    try:
        price = float(form.get("price", "0"))
    except ValueError:
        price = -1
    try:
        mileage = int(form.get("mileage", "0"))
    except ValueError:
        mileage = -1

    acquired_at = form.get("acquired_at") or date.today().isoformat()

    if not vin:
        errors.append("VIN is required.")
    if not brand or not model:
        errors.append("Brand and model are required.")
    if year < 2000 or year > date.today().year + 1:
        errors.append("Year must be realistic.")
    if price <= 0:
        errors.append("Price must be greater than zero.")
    if mileage < 0:
        errors.append("Mileage cannot be negative.")

    existing = db.execute(
        "SELECT id FROM vehicles WHERE vin = ? AND (? IS NULL OR id != ?)",
        (vin, vehicle_id, vehicle_id),
    ).fetchone()
    if existing:
        errors.append("VIN already exists.")

    if errors:
        for error in errors:
            flash(error, "error")
        vehicle = dict(form)
        vehicle["id"] = vehicle_id
        return render_template("vehicle_form.html", vehicle=vehicle), 400

    if vehicle_id:
        db.execute(
            """
            UPDATE vehicles
            SET vin = ?, brand = ?, model = ?, year = ?, price = ?, color = ?,
                mileage = ?, status = ?, acquired_at = ?
            WHERE id = ?
            """,
            (vin, brand, model, year, price, color, mileage, status, acquired_at, vehicle_id),
        )
        flash("Vehicle updated.", "success")
    else:
        db.execute(
            """
            INSERT INTO vehicles (vin, brand, model, year, price, color, mileage, status, acquired_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (vin, brand, model, year, price, color, mileage, status, acquired_at),
        )
        flash("Vehicle added.", "success")

    db.commit()
    return redirect(url_for("main.vehicles"))


@bp.route("/customers")
@login_required
def customers():
    db = get_db()
    q = request.args.get("q", "").strip()
    if q:
        like = f"%{q}%"
        rows = db.execute(
            """
            SELECT c.*,
                   COUNT(s.id) AS purchases,
                   COALESCE(SUM(CASE WHEN s.status = 'completed' THEN s.sale_price ELSE 0 END), 0) AS lifetime_value
            FROM customers c
            LEFT JOIN sales s ON s.customer_id = c.id
            WHERE c.name LIKE ? OR c.phone LIKE ? OR c.email LIKE ? OR c.city LIKE ?
            GROUP BY c.id
            ORDER BY c.created_at DESC
            """,
            (like, like, like, like),
        ).fetchall()
    else:
        rows = db.execute(
            """
            SELECT c.*,
                   COUNT(s.id) AS purchases,
                   COALESCE(SUM(CASE WHEN s.status = 'completed' THEN s.sale_price ELSE 0 END), 0) AS lifetime_value
            FROM customers c
            LEFT JOIN sales s ON s.customer_id = c.id
            GROUP BY c.id
            ORDER BY c.created_at DESC
            """
        ).fetchall()
    return render_template("customers.html", customers=rows, q=q)


@bp.route("/customers/new", methods=("GET", "POST"))
@login_required
def customer_new():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        city = request.form.get("city", "").strip()
        if not name or not phone:
            flash("Name and phone are required.", "error")
            return render_template("customer_form.html"), 400
        get_db().execute(
            "INSERT INTO customers (name, phone, email, city) VALUES (?, ?, ?, ?)",
            (name, phone, email, city),
        )
        get_db().commit()
        flash("Customer added.", "success")
        return redirect(url_for("main.customers"))
    return render_template("customer_form.html")


@bp.route("/sales")
@login_required
def sales():
    db = get_db()
    status = request.args.get("status", "").strip()
    rep = request.args.get("rep", "").strip()
    filters = []
    params = []
    if status:
        filters.append("s.status = ?")
        params.append(status)
    if rep:
        filters.append("s.sales_rep = ?")
        params.append(rep)
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows = db.execute(
        f"""
        SELECT s.*, v.brand, v.model, v.vin, c.name AS customer_name
        FROM sales s
        JOIN vehicles v ON v.id = s.vehicle_id
        JOIN customers c ON c.id = s.customer_id
        {where_clause}
        ORDER BY s.created_at DESC
        """,
        params,
    ).fetchall()
    reps = db.execute("SELECT DISTINCT sales_rep FROM sales ORDER BY sales_rep").fetchall()
    return render_template("sales.html", sales=rows, reps=reps, status=status, rep=rep)


@bp.route("/sales/new", methods=("GET", "POST"))
@login_required
def sale_new():
    db = get_db()
    if request.method == "POST":
        vehicle_id = request.form.get("vehicle_id")
        customer_id = request.form.get("customer_id")
        sales_rep = request.form.get("sales_rep", "").strip()
        status = request.form.get("status", "pending")
        sold_at = request.form.get("sold_at") or date.today().isoformat()
        notes = request.form.get("notes", "").strip()

        try:
            sale_price = float(request.form.get("sale_price", "0"))
        except ValueError:
            sale_price = -1

        vehicle = db.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)).fetchone()
        customer = db.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()

        errors = []
        if vehicle is None:
            errors.append("Select a valid vehicle.")
        elif vehicle["status"] == "sold":
            errors.append("Sold vehicles cannot be sold again.")
        if customer is None:
            errors.append("Select a valid customer.")
        if not sales_rep:
            errors.append("Sales representative is required.")
        if sale_price <= 0:
            errors.append("Sale price must be greater than zero.")
        if vehicle is not None and sold_at < vehicle["acquired_at"]:
            errors.append("Sold date cannot be earlier than acquired date.")

        if errors:
            for error in errors:
                flash(error, "error")
            return sale_form_response(db), 400

        db.execute(
            """
            INSERT INTO sales (vehicle_id, customer_id, sales_rep, sale_price, status, sold_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (vehicle_id, customer_id, sales_rep, sale_price, status, sold_at, notes),
        )
        if status == "completed":
            db.execute("UPDATE vehicles SET status = 'sold' WHERE id = ?", (vehicle_id,))
        elif status == "pending":
            db.execute("UPDATE vehicles SET status = 'reserved' WHERE id = ?", (vehicle_id,))
        db.commit()
        flash("Sale record created.", "success")
        return redirect(url_for("main.sales"))
    return sale_form_response(db)


def sale_form_response(db):
    vehicles = db.execute(
        """
        SELECT id, vin, brand, model, year, price
        FROM vehicles
        WHERE status != 'sold'
        ORDER BY brand, model
        """
    ).fetchall()
    customers = db.execute("SELECT id, name, phone FROM customers ORDER BY name").fetchall()
    return render_template("sale_form.html", vehicles=vehicles, customers=customers)


@bp.route("/sales/<int:sale_id>/complete", methods=("POST",))
@login_required
def sale_complete(sale_id):
    db = get_db()
    sale = db.execute("SELECT * FROM sales WHERE id = ?", (sale_id,)).fetchone()
    if sale is None:
        flash("Sale record not found.", "error")
    elif sale["status"] == "completed":
        flash("Sale was already completed.", "error")
    else:
        vehicle = db.execute("SELECT * FROM vehicles WHERE id = ?", (sale["vehicle_id"],)).fetchone()
        if vehicle and vehicle["status"] == "sold":
            flash("Vehicle is already marked as sold.", "error")
        else:
            db.execute(
                "UPDATE sales SET status = 'completed', sold_at = COALESCE(sold_at, date('now')) WHERE id = ?",
                (sale_id,),
            )
            db.execute("UPDATE vehicles SET status = 'sold' WHERE id = ?", (sale["vehicle_id"],))
            db.commit()
            flash("Sale completed and inventory updated.", "success")
    return redirect(url_for("main.sales"))
