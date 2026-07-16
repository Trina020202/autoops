# AutoOps Database Schema

## users

Internal application users.

- id: unique user identifier.
- name: staff display name.
- email: unique login email.
- password_hash: hashed password, never stored in plain text.
- role: user role such as Operations Manager or Staff.
- created_at: account creation timestamp.

## vehicles

Inventory records for vehicles managed by the dealership.

- id: unique vehicle identifier.
- vin: unique vehicle identification number.
- brand: car manufacturer or brand, for example XPeng, BYD, Tesla, NIO, Li Auto, AITO, Zeekr.
- model: vehicle model and trim.
- year: model year.
- price: listed selling price.
- color: exterior color.
- mileage: current mileage.
- status: inventory state. Allowed values are available, reserved, and sold.
- acquired_at: date when the vehicle entered inventory.
- created_at: row creation timestamp.

## customers

Customer records used by the sales workflow.

- id: unique customer identifier.
- name: customer name.
- phone: customer phone number.
- email: customer email address.
- city: customer city.
- created_at: row creation timestamp.

## sales

Sales pipeline and completed transaction records.

- id: unique sales record identifier.
- vehicle_id: foreign key to vehicles.id.
- customer_id: foreign key to customers.id.
- sales_rep: staff member responsible for the sale.
- sale_price: final transaction price.
- status: sales state. Allowed values are pending, completed, and cancelled.
- sold_at: transaction date or expected deal date.
- notes: operational notes.
- created_at: row creation timestamp.

## Relationships

- sales.vehicle_id joins to vehicles.id.
- sales.customer_id joins to customers.id.
- Completed sales should be analyzed with sales.status = 'completed'.
- Brand, model, year, price, mileage, and inventory status come from vehicles.
- Customer value analysis joins sales to customers.
