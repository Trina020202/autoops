# AutoOps NL2SQL Examples

## Top brands by revenue

Question:

Which brand generated the highest revenue last month?

SQL pattern:

```sql
SELECT v.brand,
       COUNT(*) AS units_sold,
       ROUND(SUM(s.sale_price), 0) AS revenue
FROM sales s
JOIN vehicles v ON v.id = s.vehicle_id
WHERE s.status = 'completed'
  AND s.sold_at >= ?
GROUP BY v.brand
ORDER BY revenue DESC
LIMIT ?;
```

## Compare brand performance

Question:

Compare XPeng and BYD sales performance this year.

SQL pattern:

```sql
SELECT v.brand,
       COUNT(*) AS units_sold,
       ROUND(SUM(s.sale_price), 0) AS revenue,
       ROUND(AVG(s.sale_price), 0) AS avg_deal
FROM sales s
JOIN vehicles v ON v.id = s.vehicle_id
WHERE s.status = 'completed'
  AND s.sold_at >= ?
  AND v.brand IN (?, ?)
GROUP BY v.brand
ORDER BY revenue DESC;
```

## Diagnose a sales decline

Question:

Analyze why sales decreased in Q2 and suggest actions.

Agent plan:

1. Query monthly completed revenue and units.
2. Query active inventory by brand and stock age.
3. Query pending pipeline by brand.
4. Compare deal count, revenue, inventory pressure, and pending sales.
5. Generate an action report.

## Salesperson ranking

Question:

Who is the top salesperson by revenue?

SQL pattern:

```sql
SELECT s.sales_rep,
       COUNT(*) AS units_sold,
       ROUND(SUM(s.sale_price), 0) AS revenue
FROM sales s
WHERE s.status = 'completed'
GROUP BY s.sales_rep
ORDER BY revenue DESC
LIMIT ?;
```
