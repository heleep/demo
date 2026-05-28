"""
Trionix Technologies - Inventory & GST Billing ERP System
Starter Plan - Multi-user SaaS ERP
"""

from flask import Flask, render_template, redirect, url_for, flash, session
from flask_login import LoginManager, current_user
from config import Config
from models.database import db
from models.user import User

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.products import products_bp
    from routes.inventory import inventory_bp
    from routes.billing import billing_bp
    from routes.users import users_bp
    from routes.reports import reports_bp
    from routes.settings import settings_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(api_bp)

    # Create tables and seed demo data
    with app.app_context():
        db.create_all()
        seed_demo_data()

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.context_processor
    def inject_globals():
        from models.settings import CompanySettings
        settings = CompanySettings.query.first()
        return dict(company_settings=settings)

    return app


def seed_demo_data():
    """Seed database with demo data for testing"""
    from models.user import User
    from models.product import Product, Category
    from models.warehouse import Warehouse
    from models.customer import Customer
    from models.settings import CompanySettings
    from models.inventory import InventoryTransaction
    from models.invoice import Invoice, InvoiceItem
    from werkzeug.security import generate_password_hash
    from datetime import datetime, timedelta
    import random

    # Check if already seeded
    if User.query.first():
        return

    print("🌱 Seeding demo data...")

    # Company settings
    settings = CompanySettings(
        company_name="Demo Retail Store",
        gst_number="27AABCU9603R1ZX",
        address="123, MG Road, Mumbai, Maharashtra - 400001",
        phone="9876543210",
        email="demo@retailstore.com",
        invoice_prefix="INV",
        invoice_counter=1001
    )
    db.session.add(settings)

    # Warehouse
    warehouse = Warehouse(name="Main Warehouse", location="Mumbai", capacity=10000)
    db.session.add(warehouse)
    db.session.flush()

    # Users
    admin = User(
        name="Rajesh Kumar",
        email="admin@demo.com",
        password_hash=generate_password_hash("admin123"),
        role="admin",
        is_active=True
    )
    cashier = User(
        name="Priya Sharma",
        email="cashier@demo.com",
        password_hash=generate_password_hash("cashier123"),
        role="cashier",
        is_active=True
    )
    inv_manager = User(
        name="Amit Singh",
        email="inventory@demo.com",
        password_hash=generate_password_hash("inventory123"),
        role="inventory_manager",
        is_active=True
    )
    for u in [admin, cashier, inv_manager]:
        db.session.add(u)
    db.session.flush()

    # Categories
    categories_data = [
        ("Electronics", "Electronic products and gadgets"),
        ("Clothing", "Apparel and fashion items"),
        ("Food & Beverages", "FMCG and grocery items"),
        ("Office Supplies", "Stationery and office products"),
        ("Home & Kitchen", "Household items"),
    ]
    categories = []
    for name, desc in categories_data:
        cat = Category(name=name, description=desc)
        db.session.add(cat)
        categories.append(cat)
    db.session.flush()

    # Products
    products_data = [
        ("Samsung Galaxy M14", "ELEC001", categories[0].id, 18, 12000, 15999, 150, 20, warehouse.id),
        ("Realme Buds Wireless", "ELEC002", categories[0].id, 18, 800, 1299, 200, 30, warehouse.id),
        ("USB Type-C Cable", "ELEC003", categories[0].id, 18, 120, 299, 500, 50, warehouse.id),
        ("Men's Cotton Shirt", "CLTH001", categories[1].id, 5, 350, 799, 300, 25, warehouse.id),
        ("Women's Kurti", "CLTH002", categories[1].id, 5, 280, 649, 250, 20, warehouse.id),
        ("Basmati Rice 5kg", "FOOD001", categories[2].id, 5, 280, 450, 400, 50, warehouse.id),
        ("Tata Salt 1kg", "FOOD002", categories[2].id, 5, 18, 26, 600, 100, warehouse.id),
        ("Colgate Toothpaste", "FOOD003", categories[2].id, 12, 45, 85, 350, 50, warehouse.id),
        ("A4 Paper Ream", "OFFC001", categories[3].id, 12, 180, 320, 200, 30, warehouse.id),
        ("Ball Point Pen (Pack)", "OFFC002", categories[3].id, 12, 35, 75, 800, 100, warehouse.id),
        ("Steel Water Bottle", "HOME001", categories[4].id, 12, 180, 399, 180, 20, warehouse.id),
        ("Non-stick Tawa", "HOME002", categories[4].id, 12, 320, 699, 90, 15, warehouse.id),
    ]
    products = []
    for name, sku, cat_id, gst, purchase, selling, stock, reorder, wh_id in products_data:
        p = Product(
            name=name, sku=sku, category_id=cat_id,
            gst_percentage=gst, purchase_price=purchase,
            selling_price=selling, current_stock=stock,
            reorder_level=reorder, warehouse_id=wh_id,
            is_active=True
        )
        db.session.add(p)
        products.append(p)
    db.session.flush()

    # Customers
    customers_data = [
        ("Suresh Traders", "CUST001", "9876543210", "suresh@traders.com", "12ABCDE1234F1Z5", "456 Market St, Mumbai"),
        ("Meena Enterprises", "CUST002", "9871234567", "meena@ent.com", "27FGHIJ5678K2L3", "789 Commercial Rd, Pune"),
        ("Raj Retail", "CUST003", "9812345678", "raj@retail.com", "", "321 Shop St, Nashik"),
        ("Walk-in Customer", "CUST004", "", "", "", ""),
    ]
    customers = []
    for name, code, phone, email, gst, addr in customers_data:
        c = Customer(name=name, customer_code=code, phone=phone,
                     email=email, gst_number=gst, address=addr)
        db.session.add(c)
        customers.append(c)
    db.session.flush()

    # Inventory transactions
    for i, p in enumerate(products):
        txn = InventoryTransaction(
            product_id=p.id, warehouse_id=warehouse.id,
            transaction_type="stock_in", quantity=p.current_stock,
            unit_price=p.purchase_price, reference="INITIAL_STOCK",
            notes="Opening stock", created_by=admin.id,
            created_at=datetime.utcnow() - timedelta(days=30)
        )
        db.session.add(txn)

    # Sample invoices over last 30 days
    invoice_counter = 1001
    for day in range(29, -1, -1):
        date = datetime.utcnow() - timedelta(days=day)
        num_invoices = random.randint(1, 4)
        for _ in range(num_invoices):
            customer = random.choice(customers)
            invoice = Invoice(
                invoice_number=f"INV{invoice_counter:04d}",
                customer_id=customer.id,
                invoice_date=date,
                payment_status=random.choice(["paid", "paid", "paid", "pending"]),
                payment_mode=random.choice(["cash", "upi", "card"]),
                created_by=admin.id
            )
            db.session.add(invoice)
            db.session.flush()

            # Add 1-4 items per invoice
            subtotal = 0
            total_gst = 0
            selected_products = random.sample(products, random.randint(1, 4))
            for prod in selected_products:
                qty = random.randint(1, 5)
                unit_price = prod.selling_price
                gst_amount = (unit_price * qty * prod.gst_percentage) / 100
                item_total = unit_price * qty + gst_amount
                item = InvoiceItem(
                    invoice_id=invoice.id, product_id=prod.id,
                    quantity=qty, unit_price=unit_price,
                    gst_percentage=prod.gst_percentage,
                    gst_amount=gst_amount, total_amount=item_total
                )
                db.session.add(item)
                subtotal += unit_price * qty
                total_gst += gst_amount

            invoice.subtotal = subtotal
            invoice.total_gst = total_gst
            invoice.total_amount = subtotal + total_gst
            invoice_counter += 1

    db.session.commit()
    print("✅ Demo data seeded successfully!")
    print("   Admin: admin@demo.com / admin123")
    print("   Cashier: cashier@demo.com / cashier123")
    print("   Inventory: inventory@demo.com / inventory123")


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
