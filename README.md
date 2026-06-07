# ORDRO — POS, Inventory & Delivery App

ORDRO is a point-of-sale, inventory, and order-management app for small shops,
restaurants, cafés, and home businesses. It runs in a browser on a phone,
tablet, or computer.

## Run
```cmd
python -m streamlit run app.py
```
Or double-click `run_app.bat` on Windows.

Requires Python 3.9+ and the packages in `requirements.txt`
(`pip install -r requirements.txt`). Streamlit 1.41 or newer is required so the
professional icons render on buttons and inputs.

## Default logins
- Admin: `admin / admin123`
- Staff: `staff / staff123`
- Delivery: `delivery / delivery123`

Change these after first sign-in (Settings -> Users). Passwords are now stored
as salted PBKDF2-SHA256 hashes, so they are no longer readable in the database.

## Roles & access
- **Admin** - full access, including Settings, the Activity Log, cost/profit
  figures, and user management. Admin can also "view as" Staff or Delivery.
- **Staff** - sales, inventory, customers, suppliers, expenses, reports, orders.
- **Delivery** - delivery and pickup handling only.

## What's included
- **Sell (POS)** - fast product search (works with a barcode/SKU scanner that
  types into the search box), cart, and checkout. Each sale records the seller.
- **Inventory** - products with cost, selling price, stock, category, image, and
  supplier. Live stock-value summary (retail value always; cost value for Admin),
  plus low-stock and out-of-stock counts and badges.
- **Customers** - records with purchase history and insights: order count,
  lifetime spend, and outstanding ("on account") balance.
- **Suppliers** - supplier directory linked to products.
- **Expenses** - one-off and recurring monthly expenses, with totals.
- **Reports** - daily revenue, sales by category, best-selling products, and
  sales by team member.
- **Orders & Delivery** - order tracking with statuses, payment status, and
  branded payment slips / receipts (generated as images).
- **Activity Log** (Admin) - records who did what and when: sign-ins, failed
  sign-ins, checkouts, and every create/edit across products, customers,
  suppliers, expenses, users, orders, deliveries, payments, and settings.
  Filter by user, period, or keyword, and export to CSV.
- **Settings** - business details, theme/appearance, payment options, and user
  management.

## Data & backups
- App data is stored in `data/ordro.db` (SQLite).
- Uploaded product, logo, and payment images are stored in `assets/uploads/`.
- To preserve your data during future updates, keep `data/ordro.db` and
  `assets/uploads/`. The app migrates the database automatically on startup
  (new tables/columns are added; existing data is kept).
