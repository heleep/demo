# Trionix Technologies — Inventory & GST Billing ERP
## Starter Plan · v1.0.0

A professional, multi-user SaaS ERP system built with Python Flask for retail shops, small warehouses, traders, and startups.

---

## 🚀 Quick Start (Local)

```bash
# 1. Clone / extract the project
cd trionix-erp

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings

# 5. Run the application
python app.py
```

Open `http://localhost:5000` in your browser.

---

## 🔑 Demo Credentials

| Role               | Email                  | Password      |
|--------------------|------------------------|---------------|
| Administrator      | admin@demo.com         | admin123      |
| Cashier            | cashier@demo.com       | cashier123    |
| Inventory Manager  | inventory@demo.com     | inventory123  |

---

## 📦 Tech Stack

- **Backend**: Python Flask 3.0
- **Database**: SQLite (dev) / MySQL / PostgreSQL (prod)
- **Frontend**: HTML5 + Tailwind CSS + JavaScript
- **Charts**: Chart.js 4.4
- **Auth**: Flask-Login
- **Deployment**: Gunicorn + Render-ready

---

## 🗄️ MySQL Setup (Production)

```sql
CREATE DATABASE trionix_erp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'trionix'@'localhost' IDENTIFIED BY 'strongpassword';
GRANT ALL PRIVILEGES ON trionix_erp.* TO 'trionix'@'localhost';
FLUSH PRIVILEGES;
```

Then set in `.env`:
```
DATABASE_URL=mysql+pymysql://trionix:strongpassword@localhost:3306/trionix_erp
```

---

## ☁️ Deploy to Render

1. Push code to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. Set environment variables:
   - `SECRET_KEY` = (generate random 32+ char string)
   - `DATABASE_URL` = (your PostgreSQL/MySQL connection string)
   - `FLASK_ENV` = `production`
5. Build command: `pip install -r requirements.txt`
6. Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`
7. Deploy!

---

## 📋 Starter Plan Features

| Feature              | Limit          |
|----------------------|----------------|
| Users                | 3              |
| Warehouses           | 1              |
| Products             | Unlimited      |
| Invoices             | Unlimited      |
| Reports              | Basic (4 types)|

---

## 🏗️ Project Structure

```
trionix-erp/
├── app.py              # Main Flask app + seed data
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── Procfile            # Render/Heroku deployment
├── runtime.txt         # Python version
├── models/
│   ├── user.py         # User model + roles
│   ├── product.py      # Product + Category models
│   ├── inventory.py    # Inventory transaction model
│   ├── invoice.py      # Invoice + InvoiceItem models
│   ├── customer.py     # Customer model
│   ├── warehouse.py    # Warehouse model
│   └── settings.py     # Company settings model
├── routes/
│   ├── auth.py         # Login/logout
│   ├── dashboard.py    # Dashboard + chart API
│   ├── products.py     # Product CRUD API
│   ├── inventory.py    # Stock in/out/adjustment
│   ├── billing.py      # Invoice creation + management
│   ├── users.py        # User management
│   ├── reports.py      # Reports API
│   └── settings.py     # Settings API
└── templates/
    ├── base.html       # Sidebar layout
    ├── auth/           # Login, forgot password
    ├── dashboard/      # Analytics dashboard
    ├── products/       # Product catalog
    ├── inventory/      # Stock management
    ├── billing/        # Invoice creation + print
    ├── users/          # User management
    ├── reports/        # Sales, inventory, revenue
    ├── settings/       # Company settings
    └── errors/         # 404, 403 pages
```

---

## 🔐 Role-Based Access Control

| Module      | Admin | Cashier | Inventory Manager |
|-------------|-------|---------|-------------------|
| Dashboard   | ✅    | ✅      | ✅                |
| Products    | ✅    | 👁 View | ✅                |
| Inventory   | ✅    | ❌      | ✅                |
| Billing     | ✅    | ✅      | ❌                |
| Users       | ✅    | ❌      | ❌                |
| Reports     | ✅    | ❌      | ✅                |
| Settings    | ✅    | ❌      | ❌                |

---

## 🔒 Security Features

- Password hashing (Werkzeug PBKDF2)
- Session management with 8-hour timeout
- Role-based access control on every route
- SQL injection prevention via SQLAlchemy ORM
- Soft delete (products/users never hard-deleted)

---

Built with ❤️ by **Trionix Technologies**
