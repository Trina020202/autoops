from dataclasses import dataclass
from datetime import date
import re


CHINESE_NUMBERS = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}


@dataclass
class CopilotQuery:
    intent: str
    summary: str
    sql: str
    params: tuple
    columns: list
    chart_label: str | None
    chart_value: str | None
    entities: dict


def month_delta(value, months):
    month = value.month - months
    year = value.year
    while month <= 0:
        month += 12
        year -= 1
    day = min(value.day, 28)
    return date(year, month, day)


def latest_data_date(db):
    row = db.execute(
        """
        SELECT COALESCE(MAX(sold_at), date('now')) AS anchor_date
        FROM sales
        WHERE status = 'completed'
        """
    ).fetchone()
    return date.fromisoformat(row["anchor_date"])


def known_entities(db):
    brands = [
        row["brand"]
        for row in db.execute("SELECT DISTINCT brand FROM vehicles ORDER BY brand").fetchall()
    ]
    reps = [
        row["sales_rep"]
        for row in db.execute("SELECT DISTINCT sales_rep FROM sales ORDER BY sales_rep").fetchall()
    ]
    return brands, reps


def normalize(question):
    return re.sub(r"\s+", " ", question.strip().lower())


def extract_limit(text):
    number_match = re.search(r"(?:top|前|最高的?|最多的?|limit)\s*(\d+)", text)
    if number_match:
        return min(max(int(number_match.group(1)), 1), 10)

    loose_number = re.search(r"(\d+)\s*(?:个|名|条|brands?|reps?)", text)
    if loose_number:
        return min(max(int(loose_number.group(1)), 1), 10)

    for word, value in CHINESE_NUMBERS.items():
        if f"{word}个" in text or f"{word}名" in text or f"前{word}" in text:
            return value
    return 5


def extract_date_window(text, anchor):
    month_match = re.search(r"(?:过去|近|最近|last|past)\s*(\d+|一|二|两|三|四|五|六)\s*(?:个)?(?:月|months?)", text)
    if month_match:
        raw = month_match.group(1)
        months = int(raw) if raw.isdigit() else CHINESE_NUMBERS.get(raw, 3)
        start = month_delta(anchor, months)
        return start.isoformat(), f"past {months} months"

    if "过去三个月" in text or "近三个月" in text or "最近三个月" in text:
        return month_delta(anchor, 3).isoformat(), "past 3 months"
    if "过去一个月" in text or "近一个月" in text or "最近一个月" in text:
        return month_delta(anchor, 1).isoformat(), "past 1 month"
    if "本月" in text or "this month" in text:
        return anchor.replace(day=1).isoformat(), "this month"
    if "今年" in text or "this year" in text:
        return date(anchor.year, 1, 1).isoformat(), "this year"
    return None, "all time"


def extract_named_value(text, candidates):
    text_lower = text.lower()
    for value in candidates:
        if value.lower() in text_lower:
            return value
    return None


def wants_revenue(text):
    return any(token in text for token in ["销售额", "收入", "营收", "revenue", "amount", "金额"])


def wants_units(text):
    return any(token in text for token in ["销量", "成交量", "卖出", "sold", "units", "count"])


def sql_with_date(base_where, params, start_date):
    if start_date:
        return f"{base_where} AND s.sold_at >= ?", (*params, start_date)
    return base_where, params


def build_query(db, question):
    text = normalize(question)
    if not text:
        return None

    blocked = ["drop ", "delete ", "update ", "insert ", "alter ", "truncate ", "pragma"]
    if any(token in text for token in blocked):
        return {
            "unsupported": True,
            "summary": "For safety, Copilot only supports read-only operational questions.",
        }

    brands, reps = known_entities(db)
    brand = extract_named_value(text, brands)
    rep = extract_named_value(text, reps)
    limit = extract_limit(text)
    start_date, date_window = extract_date_window(text, latest_data_date(db))

    params = ()
    where, params = sql_with_date("WHERE s.status = 'completed'", params, start_date)
    if brand:
        where += " AND v.brand = ?"
        params = (*params, brand)
    if rep:
        where += " AND s.sales_rep = ?"
        params = (*params, rep)

    entities = {
        "date_window": date_window,
        "start_date": start_date or "N/A",
        "brand": brand or "N/A",
        "sales_rep": rep or "N/A",
        "limit": limit,
    }

    if "库存" in text or "inventory" in text or "stock" in text:
        inventory_where = "WHERE status != 'sold'"
        inventory_params = ()
        if brand:
            inventory_where += " AND brand = ?"
            inventory_params = (brand,)
        sql = f"""
            SELECT brand,
                   COUNT(*) AS active_inventory,
                   ROUND(AVG(price), 0) AS avg_price
            FROM vehicles
            {inventory_where}
            GROUP BY brand
            ORDER BY active_inventory DESC, avg_price DESC
            LIMIT ?
        """
        return CopilotQuery(
            intent="inventory_by_brand",
            summary="Inventory grouped by brand.",
            sql=sql,
            params=(*inventory_params, limit),
            columns=["brand", "active_inventory", "avg_price"],
            chart_label="brand",
            chart_value="active_inventory",
            entities=entities,
        )

    if "销售人员" in text or "销售代表" in text or "sales rep" in text or "rep" in text or "业绩" in text:
        order_metric = "revenue" if wants_revenue(text) or not wants_units(text) else "units_sold"
        sql = f"""
            SELECT s.sales_rep,
                   COUNT(*) AS units_sold,
                   ROUND(SUM(s.sale_price), 0) AS revenue
            FROM sales s
            JOIN vehicles v ON v.id = s.vehicle_id
            {where}
            GROUP BY s.sales_rep
            ORDER BY {order_metric} DESC, revenue DESC
            LIMIT ?
        """
        return CopilotQuery(
            intent=f"top_reps_by_{order_metric}",
            summary=f"Sales representatives ranked by {order_metric.replace('_', ' ')}.",
            sql=sql,
            params=(*params, limit),
            columns=["sales_rep", "units_sold", "revenue"],
            chart_label="sales_rep",
            chart_value=order_metric,
            entities=entities,
        )

    if "趋势" in text or "trend" in text or "月度" in text or "monthly" in text:
        sql = f"""
            SELECT strftime('%Y-%m', s.sold_at) AS month,
                   COUNT(*) AS units_sold,
                   ROUND(SUM(s.sale_price), 0) AS revenue
            FROM sales s
            JOIN vehicles v ON v.id = s.vehicle_id
            {where}
            GROUP BY month
            ORDER BY month
        """
        return CopilotQuery(
            intent="monthly_sales_trend",
            summary="Monthly completed sales trend.",
            sql=sql,
            params=params,
            columns=["month", "units_sold", "revenue"],
            chart_label="month",
            chart_value="revenue" if wants_revenue(text) else "units_sold",
            entities=entities,
        )

    if "客户" in text or "customer" in text:
        sql = f"""
            SELECT c.name AS customer,
                   COUNT(*) AS purchases,
                   ROUND(SUM(s.sale_price), 0) AS revenue
            FROM sales s
            JOIN vehicles v ON v.id = s.vehicle_id
            JOIN customers c ON c.id = s.customer_id
            {where}
            GROUP BY c.id, c.name
            ORDER BY revenue DESC, purchases DESC
            LIMIT ?
        """
        return CopilotQuery(
            intent="top_customers",
            summary="Customers ranked by completed sales value.",
            sql=sql,
            params=(*params, limit),
            columns=["customer", "purchases", "revenue"],
            chart_label="customer",
            chart_value="revenue",
            entities=entities,
        )

    # Default to brand performance because it is the most common operating question.
    order_metric = "revenue" if wants_revenue(text) else "units_sold"
    sql = f"""
        SELECT v.brand,
               COUNT(*) AS units_sold,
               ROUND(SUM(s.sale_price), 0) AS revenue
        FROM sales s
        JOIN vehicles v ON v.id = s.vehicle_id
        {where}
        GROUP BY v.brand
        ORDER BY {order_metric} DESC, revenue DESC
        LIMIT ?
    """
    return CopilotQuery(
        intent=f"top_brands_by_{order_metric}",
        summary=f"Brands ranked by {order_metric.replace('_', ' ')}.",
        sql=sql,
        params=(*params, limit),
        columns=["brand", "units_sold", "revenue"],
        chart_label="brand",
        chart_value=order_metric,
        entities=entities,
    )


def run_copilot_query(db, question):
    query = build_query(db, question)
    if query is None:
        return None
    if isinstance(query, dict):
        return query

    rows = [dict(row) for row in db.execute(query.sql, query.params).fetchall()]
    max_value = max([float(row.get(query.chart_value) or 0) for row in rows] or [1])
    return {
        "unsupported": False,
        "intent": query.intent,
        "summary": query.summary,
        "sql": clean_sql(query.sql),
        "params": query.params,
        "columns": query.columns,
        "rows": rows,
        "chart_label": query.chart_label,
        "chart_value": query.chart_value,
        "max_value": max_value,
        "entities": query.entities,
    }


def clean_sql(sql):
    return "\n".join(line.rstrip() for line in sql.strip().splitlines())
