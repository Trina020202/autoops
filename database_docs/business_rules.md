# AutoOps Business Rules

## Inventory Rules

- Available inventory includes vehicles where vehicles.status is not sold.
- Sold inventory includes vehicles where vehicles.status = 'sold'.
- Reserved vehicles should remain in active inventory until the sale is completed.
- Completing a sale should update the related vehicle status to sold.
- A sold vehicle should not be sold again.
- VIN values must be unique.

## Sales Rules

- Completed sales are records where sales.status = 'completed'.
- Pending sales are pipeline records and should not count toward revenue.
- Cancelled sales should not count toward revenue or completed units.
- Revenue is calculated from completed sale_price values, not listed vehicle price.
- Deal count is the number of completed sales records.
- Average deal size is completed revenue divided by completed deal count.
- Date filtering should use sales.sold_at for sales analysis.

## Operational Analysis Rules

- Top brand by units ranks brands by completed sales count.
- Top brand by revenue ranks brands by SUM(sales.sale_price).
- Top salesperson ranks sales_rep by completed sales count or completed revenue.
- Customer value ranks customers by completed revenue and purchase count.
- Inventory pressure can be approximated by days in stock and active inventory count.
- If a question asks why sales changed, compare completed sales trend, brand mix, pending pipeline, and active inventory.
