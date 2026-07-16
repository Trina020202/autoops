from dataclasses import dataclass
from pathlib import Path
import re

from app.copilot import (
    CopilotQuery,
    build_query,
    clean_sql,
    extract_date_window,
    known_entities,
    latest_data_date,
    normalize,
)


WRITE_BLOCKLIST = [
    "drop ",
    "delete ",
    "update ",
    "insert ",
    "alter ",
    "truncate ",
    "pragma",
    "create ",
]

QUERY_EXPANSIONS = {
    "sales": "revenue sale_price completed units sold sales_rep sold_at vehicles brand",
    "revenue": "revenue sale_price sum completed sales",
    "inventory": "inventory vehicles status available reserved sold active stock acquired_at",
    "customer": "customers customer value purchases revenue",
    "trend": "monthly trend sold_at strftime revenue units",
    "compare": "compare brand performance revenue units avg_deal",
    "decline": "decrease decline trend inventory pending pipeline diagnosis",
    "销售额": "revenue sale_price sum completed sales",
    "营收": "revenue sale_price sum completed sales",
    "收入": "revenue sale_price sum completed sales",
    "销量": "units sold count completed sales",
    "成交": "completed sales sold_at sale_price",
    "库存": "inventory vehicles status available reserved active stock",
    "客户": "customers customer value purchases revenue",
    "销售人员": "sales_rep salesperson performance revenue units",
    "业绩": "sales_rep performance revenue units",
    "趋势": "monthly trend sold_at revenue units",
    "对比": "compare brand performance revenue units avg_deal",
    "比较": "compare brand performance revenue units avg_deal",
    "下降": "decrease decline trend inventory pending pipeline diagnosis",
    "原因": "diagnosis trend inventory pending pipeline",
    "建议": "action report recommendation insight",
}


@dataclass
class KnowledgeChunk:
    source: str
    title: str
    text: str
    score: int = 0


def is_unsafe_question(text):
    return any(token in text for token in WRITE_BLOCKLIST)


def knowledge_dir():
    return Path(__file__).resolve().parents[1] / "database_docs"


def tokenize(text):
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


def expand_question(question):
    expanded = question.lower()
    for key, value in QUERY_EXPANSIONS.items():
        if key.lower() in expanded:
            expanded = f"{expanded} {value}"
    return expanded


def load_knowledge_chunks():
    chunks = []
    for path in sorted(knowledge_dir().glob("*.md")):
        title = path.stem.replace("_", " ").title()
        current_title = title
        buffer = []
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line.startswith("#"):
                if buffer:
                    chunks.append(
                        KnowledgeChunk(path.name, current_title, "\n".join(buffer).strip())
                    )
                    buffer = []
                current_title = line.lstrip("#").strip() or title
            elif line:
                buffer.append(line)
        if buffer:
            chunks.append(KnowledgeChunk(path.name, current_title, "\n".join(buffer).strip()))
    return chunks


def retrieve_knowledge(question, top_k=4):
    query_text = expand_question(question)
    query_tokens = tokenize(query_text)
    scored = []
    for chunk in load_knowledge_chunks():
        haystack = f"{chunk.title} {chunk.text}".lower()
        chunk_tokens = tokenize(haystack)
        score = len(query_tokens & chunk_tokens)
        for token in query_tokens:
            if len(token) > 3 and token in haystack:
                score += 1
        if score > 0:
            scored.append(
                KnowledgeChunk(chunk.source, chunk.title, chunk.text, score=score)
            )
    scored.sort(key=lambda item: item.score, reverse=True)
    return [
        {
            "source": item.source,
            "title": item.title,
            "text": item.text,
            "score": item.score,
        }
        for item in scored[:top_k]
    ]


def execute_read_query(db, sql, params=()):
    cleaned = clean_sql(sql)
    lowered = cleaned.lower()
    if not lowered.startswith("select"):
        raise ValueError("Only read-only SELECT statements are allowed.")
    if is_unsafe_question(lowered):
        raise ValueError("Only read-only operational questions are allowed.")
    return [dict(row) for row in db.execute(cleaned, params).fetchall()]


def max_for_chart(rows, chart_value):
    return max([float(row.get(chart_value) or 0) for row in rows] or [1])


def summarize_tool_output(rows, columns):
    if not rows:
        return "0 rows returned."
    preview = rows[0]
    parts = []
    for column in columns[:3]:
        if column in preview:
            parts.append(f"{column}={preview[column]}")
    return f"{len(rows)} rows returned; top row: {', '.join(parts)}."


def make_tool_call(name, purpose, input_summary, output_summary):
    return {
        "name": name,
        "purpose": purpose,
        "input": input_summary,
        "output": output_summary,
    }


def build_chart(rows, label, value, title):
    return {
        "title": title,
        "label": label,
        "value": value,
        "max_value": max_for_chart(rows, value),
    }


def template_report(intent, rows, chart_value):
    if not rows:
        return [
            "No matching completed records were found for this question.",
            "The agent used the business rules to keep pending and cancelled deals out of revenue metrics.",
        ]

    top = rows[0]
    if "brand" in top:
        metric = "revenue" if chart_value == "revenue" else "units sold"
        value = top.get("revenue") if chart_value == "revenue" else top.get("units_sold")
        return [
            f"Top brand is {top['brand']} by {metric}, with {value}.",
            "The query uses completed sales only, so pending deals are excluded from revenue and units.",
            "A manager can use this result to prioritize inventory allocation and sales follow-up by brand.",
        ]
    if "sales_rep" in top:
        return [
            f"Top salesperson is {top['sales_rep']} with revenue {top.get('revenue')} and {top.get('units_sold')} completed units.",
            "The ranking uses completed sales records, which makes the result suitable for performance review.",
        ]
    if "customer" in top:
        return [
            f"Highest-value customer is {top['customer']} with revenue {top.get('revenue')}.",
            "The customer value view can support retention and follow-up prioritization.",
        ]
    if "month" in top:
        return [
            "The chart shows completed sales trend by month.",
            "Revenue movement should be read together with pending pipeline and inventory availability.",
        ]
    return [
        f"Agent completed {intent} and returned {len(rows)} rows.",
        "The result is based on retrieved schema knowledge and read-only SQL execution.",
    ]


def result_payload(
    *,
    intent,
    summary,
    sql,
    params,
    columns,
    rows,
    chart,
    entities,
    retrieved_context,
    plan_steps,
    tool_calls,
    report,
    supporting_tables=None,
):
    return {
        "unsupported": False,
        "intent": intent,
        "summary": summary,
        "sql": clean_sql(sql),
        "params": params,
        "columns": columns,
        "rows": rows,
        "chart_label": chart["label"],
        "chart_value": chart["value"],
        "max_value": chart["max_value"],
        "chart_title": chart["title"],
        "entities": entities,
        "retrieved_context": retrieved_context,
        "plan_steps": plan_steps,
        "tool_calls": tool_calls,
        "report": report,
        "supporting_tables": supporting_tables or [],
    }


def run_template_agent(db, question, retrieved_context):
    query = build_query(db, question)
    if query is None:
        return None
    if isinstance(query, dict):
        query["retrieved_context"] = retrieved_context
        query["plan_steps"] = []
        query["tool_calls"] = []
        query["report"] = []
        return query

    rows = execute_read_query(db, query.sql, query.params)
    chart = build_chart(rows, query.chart_label, query.chart_value, query.summary)
    plan_steps = [
        {
            "step": "Retrieve database knowledge",
            "detail": "Find schema, metric definitions, and business rules related to the question.",
        },
        {
            "step": "Select SQL template",
            "detail": f"Map the question to intent `{query.intent}` and fill date/entity parameters.",
        },
        {
            "step": "Call database tool",
            "detail": "Execute a read-only SELECT query against the operations database.",
        },
        {
            "step": "Generate chart and report",
            "detail": "Convert rows into a bar chart and explain the operating result.",
        },
    ]
    tool_calls = [
        make_tool_call(
            "retrieve_knowledge",
            "Ground NL2SQL generation in schema docs and business rules.",
            question,
            f"{len(retrieved_context)} knowledge chunks retrieved.",
        ),
        make_tool_call(
            "query_database",
            "Run the generated SQL safely.",
            clean_sql(query.sql),
            summarize_tool_output(rows, query.columns),
        ),
        make_tool_call(
            "generate_chart",
            "Prepare chart data for the result panel.",
            f"label={query.chart_label}, value={query.chart_value}",
            f"max_value={chart['max_value']}",
        ),
        make_tool_call(
            "generate_report",
            "Explain result and recommended follow-up.",
            query.intent,
            "Short business insight generated.",
        ),
    ]
    return result_payload(
        intent=f"rag_{query.intent}",
        summary=query.summary,
        sql=query.sql,
        params=query.params,
        columns=query.columns,
        rows=rows,
        chart=chart,
        entities=query.entities,
        retrieved_context=retrieved_context,
        plan_steps=plan_steps,
        tool_calls=tool_calls,
        report=template_report(query.intent, rows, query.chart_value),
    )


def detect_brands(db, text):
    brands, _ = known_entities(db)
    text_lower = text.lower()
    return [brand for brand in brands if brand.lower() in text_lower]


def run_compare_agent(db, question, retrieved_context, brands):
    anchor = latest_data_date(db)
    start_date, date_window = extract_date_window(normalize(question), anchor)
    if not start_date:
        start_date = f"{anchor.year}-01-01"
        date_window = "this year"

    placeholders = ", ".join(["?"] * len(brands))
    sql = f"""
        SELECT v.brand,
               COUNT(*) AS units_sold,
               ROUND(SUM(s.sale_price), 0) AS revenue,
               ROUND(AVG(s.sale_price), 0) AS avg_deal
        FROM sales s
        JOIN vehicles v ON v.id = s.vehicle_id
        WHERE s.status = 'completed'
          AND s.sold_at >= ?
          AND v.brand IN ({placeholders})
        GROUP BY v.brand
        ORDER BY revenue DESC, units_sold DESC
    """
    params = (start_date, *brands)
    columns = ["brand", "units_sold", "revenue", "avg_deal"]
    rows = execute_read_query(db, sql, params)
    chart = build_chart(rows, "brand", "revenue", "Brand revenue comparison")

    report = []
    if rows:
        leader = rows[0]
        report.append(
            f"{leader['brand']} leads this comparison with revenue {leader['revenue']} and {leader['units_sold']} completed units."
        )
        if len(rows) > 1:
            runner_up = rows[1]
            revenue_gap = float(leader["revenue"] or 0) - float(runner_up["revenue"] or 0)
            report.append(
                f"The revenue gap versus {runner_up['brand']} is {revenue_gap:.0f}, based on completed transactions."
            )
        report.append(
            "The agent used sale_price rather than listed vehicle price, matching the revenue rule from the knowledge base."
        )
    else:
        report = [
            "No completed sales were found for the selected brands and date window.",
            "Check pending pipeline or widen the date range before making a performance conclusion.",
        ]

    return result_payload(
        intent="rag_agent_brand_comparison",
        summary="Brand performance comparison using completed sales.",
        sql=sql,
        params=params,
        columns=columns,
        rows=rows,
        chart=chart,
        entities={
            "date_window": date_window,
            "start_date": start_date,
            "brands": ", ".join(brands),
        },
        retrieved_context=retrieved_context,
        plan_steps=[
            {
                "step": "Retrieve database knowledge",
                "detail": "Use schema, revenue definition, and comparison examples.",
            },
            {
                "step": "Identify comparison entities",
                "detail": f"Detected brands: {', '.join(brands)}.",
            },
            {
                "step": "Call query_database",
                "detail": "Aggregate units, revenue, and average deal size by brand.",
            },
            {
                "step": "Call generate_chart and generate_report",
                "detail": "Visualize the comparison and explain the business gap.",
            },
        ],
        tool_calls=[
            make_tool_call(
                "retrieve_knowledge",
                "Ground the comparison in schema and metric definitions.",
                question,
                f"{len(retrieved_context)} knowledge chunks retrieved.",
            ),
            make_tool_call(
                "query_database",
                "Fetch completed sales performance for selected brands.",
                clean_sql(sql),
                summarize_tool_output(rows, columns),
            ),
            make_tool_call(
                "calculate_metric",
                "Compare revenue, units, and average deal size.",
                f"brands={', '.join(brands)}",
                "Comparison metrics calculated from completed sales.",
            ),
            make_tool_call(
                "generate_report",
                "Summarize the performance difference.",
                "brand comparison",
                "Insight report generated.",
            ),
        ],
        report=report,
    )


def quarter_bounds(anchor, quarter):
    year = anchor.year
    start_month = (quarter - 1) * 3 + 1
    end_month = start_month + 3
    end_year = year
    if end_month > 12:
        end_month -= 12
        end_year += 1
    return f"{year}-{start_month:02d}-01", f"{end_year}-{end_month:02d}-01"


def summarize_month_range(rows, year, start_month, end_month):
    revenue = 0
    units = 0
    for row in rows:
        year_month = row["month"].split("-")
        row_year = int(year_month[0])
        row_month = int(year_month[1])
        if row_year == year and start_month <= row_month <= end_month:
            revenue += float(row["revenue"] or 0)
            units += int(row["units_sold"] or 0)
    return units, revenue


def run_diagnosis_agent(db, question, retrieved_context):
    anchor = latest_data_date(db)
    q2_start, q2_end = quarter_bounds(anchor, 2)
    monthly_sql = """
        SELECT strftime('%Y-%m', sold_at) AS month,
               COUNT(*) AS units_sold,
               ROUND(SUM(sale_price), 0) AS revenue
        FROM sales
        WHERE status = 'completed'
        GROUP BY month
        ORDER BY month
    """
    inventory_sql = """
        SELECT brand,
               COUNT(*) AS active_inventory,
               ROUND(AVG(julianday('now') - julianday(acquired_at)), 0) AS avg_days_in_stock
        FROM vehicles
        WHERE status != 'sold'
        GROUP BY brand
        ORDER BY active_inventory DESC, avg_days_in_stock DESC
    """
    pipeline_sql = """
        SELECT v.brand,
               COUNT(*) AS pending_deals,
               ROUND(SUM(s.sale_price), 0) AS pending_value
        FROM sales s
        JOIN vehicles v ON v.id = s.vehicle_id
        WHERE s.status = 'pending'
        GROUP BY v.brand
        ORDER BY pending_value DESC
    """
    brand_sql = """
        SELECT v.brand,
               COUNT(*) AS q2_units,
               ROUND(SUM(s.sale_price), 0) AS q2_revenue
        FROM sales s
        JOIN vehicles v ON v.id = s.vehicle_id
        WHERE s.status = 'completed'
          AND s.sold_at >= ?
          AND s.sold_at < ?
        GROUP BY v.brand
        ORDER BY q2_revenue DESC
    """

    monthly_rows = execute_read_query(db, monthly_sql)
    inventory_rows = execute_read_query(db, inventory_sql)
    pipeline_rows = execute_read_query(db, pipeline_sql)
    brand_rows = execute_read_query(db, brand_sql, (q2_start, q2_end))

    q1_units, q1_revenue = summarize_month_range(monthly_rows, anchor.year, 1, 3)
    q2_units = sum(int(row["q2_units"] or 0) for row in brand_rows)
    q2_revenue = sum(float(row["q2_revenue"] or 0) for row in brand_rows)
    revenue_change = q2_revenue - q1_revenue
    change_rate = (revenue_change / q1_revenue * 100) if q1_revenue else 0

    report = [
        f"Q2 completed revenue was {q2_revenue:.0f} from {q2_units} completed units, compared with Q1 revenue {q1_revenue:.0f} from {q1_units} units.",
        f"The revenue change is {revenue_change:.0f} ({change_rate:.1f}%).",
        "The main driver is completed-deal volume: pending deals are not counted as revenue until status becomes completed.",
    ]
    if pipeline_rows:
        top_pipeline = pipeline_rows[0]
        report.append(
            f"Pipeline follow-up should start with {top_pipeline['brand']}, which has pending value {top_pipeline['pending_value']}."
        )
    if inventory_rows:
        aging = inventory_rows[0]
        report.append(
            f"Inventory action: review {aging['brand']} first because it has {aging['active_inventory']} active units and average stock age {aging['avg_days_in_stock']} days."
        )

    chart = build_chart(monthly_rows, "month", "revenue", "Monthly completed revenue")

    return result_payload(
        intent="rag_agent_sales_decline_diagnosis",
        summary="Multi-step diagnosis across revenue trend, inventory, and pending pipeline.",
        sql=monthly_sql,
        params=(),
        columns=["month", "units_sold", "revenue"],
        rows=monthly_rows,
        chart=chart,
        entities={
            "analysis_window": f"{anchor.year} Q2",
            "q2_start": q2_start,
            "q2_end": q2_end,
            "q2_revenue": f"{q2_revenue:.0f}",
            "q2_units": q2_units,
        },
        retrieved_context=retrieved_context,
        plan_steps=[
            {
                "step": "Retrieve database knowledge",
                "detail": "Use revenue rules, monthly trend definition, and diagnosis example.",
            },
            {
                "step": "Plan investigation",
                "detail": "Check completed revenue trend, active inventory, pending pipeline, and Q2 brand mix.",
            },
            {
                "step": "Call database tools",
                "detail": "Run four read-only queries against sales and vehicles.",
            },
            {
                "step": "Calculate metrics",
                "detail": "Compare Q2 revenue and units against Q1.",
            },
            {
                "step": "Generate report",
                "detail": "Turn observations into operational recommendations.",
            },
        ],
        tool_calls=[
            make_tool_call(
                "retrieve_knowledge",
                "Find rules for revenue, trends, inventory, and diagnosis.",
                question,
                f"{len(retrieved_context)} knowledge chunks retrieved.",
            ),
            make_tool_call(
                "query_database",
                "Fetch completed monthly revenue trend.",
                clean_sql(monthly_sql),
                summarize_tool_output(monthly_rows, ["month", "units_sold", "revenue"]),
            ),
            make_tool_call(
                "query_database",
                "Fetch active inventory and stock age by brand.",
                clean_sql(inventory_sql),
                summarize_tool_output(
                    inventory_rows,
                    ["brand", "active_inventory", "avg_days_in_stock"],
                ),
            ),
            make_tool_call(
                "query_database",
                "Fetch pending pipeline by brand.",
                clean_sql(pipeline_sql),
                summarize_tool_output(pipeline_rows, ["brand", "pending_deals", "pending_value"]),
            ),
            make_tool_call(
                "calculate_metric",
                "Compute Q2 versus Q1 change.",
                f"q2_start={q2_start}, q2_end={q2_end}",
                f"revenue_change={revenue_change:.0f}, change_rate={change_rate:.1f}%",
            ),
            make_tool_call(
                "generate_report",
                "Generate diagnosis and actions.",
                "trend + inventory + pipeline",
                "Diagnosis report generated.",
            ),
        ],
        report=report,
        supporting_tables=[
            {
                "title": "Active inventory by brand",
                "columns": ["brand", "active_inventory", "avg_days_in_stock"],
                "rows": inventory_rows,
            },
            {
                "title": "Pending pipeline by brand",
                "columns": ["brand", "pending_deals", "pending_value"],
                "rows": pipeline_rows,
            },
            {
                "title": "Q2 completed sales by brand",
                "columns": ["brand", "q2_units", "q2_revenue"],
                "rows": brand_rows,
            },
        ],
    )


def run_sales_analyst(db, question):
    text = normalize(question)
    if not text:
        return None
    if is_unsafe_question(text):
        return {
            "unsupported": True,
            "summary": "For safety, AutoOps AI Sales Analyst only supports read-only operational questions.",
            "retrieved_context": [],
            "plan_steps": [],
            "tool_calls": [],
            "report": [],
        }

    retrieved_context = retrieve_knowledge(question)
    brands = detect_brands(db, text)

    diagnosis_terms = ["why", "decrease", "decline", "q2", "原因", "下降", "减少", "建议"]
    compare_terms = ["compare", "versus", "vs", "对比", "比较"]

    if any(term in text for term in diagnosis_terms):
        return run_diagnosis_agent(db, question, retrieved_context)

    if len(brands) >= 2 and any(term in text for term in compare_terms):
        return run_compare_agent(db, question, retrieved_context, brands)

    return run_template_agent(db, question, retrieved_context)
