# AutoOps Metric Definitions

## Revenue

Revenue = SUM(sales.sale_price) for completed sales.

Recommended SQL filter:

```sql
WHERE sales.status = 'completed'
```

## Units Sold

Units Sold = COUNT(*) for completed sales.

## Active Inventory

Active Inventory = COUNT(*) from vehicles where status is not sold.

```sql
WHERE vehicles.status != 'sold'
```

## Average Deal Size

Average Deal Size = SUM(completed sale_price) / COUNT(completed sales).

## Salesperson Performance

Salesperson performance can be ranked by:

- completed revenue,
- completed units sold,
- average deal size.

## Monthly Trend

Monthly trend groups completed sales by month using sold_at.

```sql
strftime('%Y-%m', sales.sold_at)
```

## Inventory Aging

Inventory aging estimates how long a vehicle has been held:

```sql
julianday('now') - julianday(vehicles.acquired_at)
```

Longer days in stock can indicate inventory pressure.
