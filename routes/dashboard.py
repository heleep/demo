from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models.database import db
from models.product import Product
from models.invoice import Invoice
from models.inventory import InventoryTransaction
from models.customer import Customer
from sqlalchemy import func, extract
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    # Key metrics
    total_products = Product.query.filter_by(is_active=True).count()
    total_customers = Customer.query.filter_by(is_active=True).count()
    low_stock_products = Product.query.filter(
        Product.current_stock <= Product.reorder_level,
        Product.is_active == True
    ).count()

    # Monthly revenue
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0)
    monthly_revenue = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.payment_status == 'paid',
        Invoice.invoice_date >= month_start
    ).scalar() or 0

    # Total sales this month
    monthly_sales = Invoice.query.filter(
        Invoice.payment_status == 'paid',
        Invoice.invoice_date >= month_start
    ).count()

    # Today's sales
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_revenue = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.payment_status == 'paid',
        Invoice.invoice_date >= today_start
    ).scalar() or 0

    # Recent transactions
    recent_invoices = Invoice.query.order_by(Invoice.created_at.desc()).limit(8).all()

    # Low stock items
    low_stock_items = Product.query.filter(
        Product.current_stock <= Product.reorder_level,
        Product.is_active == True
    ).order_by(Product.current_stock.asc()).limit(6).all()

    # Inventory value
    products = Product.query.filter_by(is_active=True).all()
    total_inventory_value = sum(p.stock_value for p in products)

    # Pending invoices
    pending_amount = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.payment_status == 'pending'
    ).scalar() or 0

    return render_template('dashboard/index.html',
        total_products=total_products,
        total_customers=total_customers,
        low_stock_products=low_stock_products,
        monthly_revenue=monthly_revenue,
        monthly_sales=monthly_sales,
        today_revenue=today_revenue,
        recent_invoices=recent_invoices,
        low_stock_items=low_stock_items,
        total_inventory_value=total_inventory_value,
        pending_amount=pending_amount
    )


@dashboard_bp.route('/api/dashboard/chart-data')
@login_required
def chart_data():
    """API endpoint for dashboard charts"""
    # Last 7 days sales chart
    labels = []
    sales_data = []
    revenue_data = []

    for i in range(6, -1, -1):
        date = datetime.utcnow() - timedelta(days=i)
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = date.replace(hour=23, minute=59, second=59)

        count = Invoice.query.filter(
            Invoice.payment_status == 'paid',
            Invoice.invoice_date >= day_start,
            Invoice.invoice_date <= day_end
        ).count()

        rev = db.session.query(func.sum(Invoice.total_amount)).filter(
            Invoice.payment_status == 'paid',
            Invoice.invoice_date >= day_start,
            Invoice.invoice_date <= day_end
        ).scalar() or 0

        labels.append(date.strftime('%a %d'))
        sales_data.append(count)
        revenue_data.append(round(rev, 2))

    # Category distribution
    from models.product import Category
    from models.invoice import InvoiceItem
    categories = Category.query.all()
    cat_labels = [c.name for c in categories]
    cat_data = []
    for cat in categories:
        product_ids = [p.id for p in cat.products.filter_by(is_active=True).all()]
        total = 0
        if product_ids:
            total = db.session.query(func.sum(InvoiceItem.quantity)).filter(
                InvoiceItem.product_id.in_(product_ids)
            ).scalar() or 0
        cat_data.append(total)

    # Monthly revenue (last 6 months)
    monthly_labels = []
    monthly_revenue = []
    for i in range(5, -1, -1):
        date = datetime.utcnow() - timedelta(days=i * 30)
        rev = db.session.query(func.sum(Invoice.total_amount)).filter(
            Invoice.payment_status == 'paid',
            extract('month', Invoice.invoice_date) == date.month,
            extract('year', Invoice.invoice_date) == date.year
        ).scalar() or 0
        monthly_labels.append(date.strftime('%b %Y'))
        monthly_revenue.append(round(rev, 2))

    return jsonify({
        'daily': {'labels': labels, 'sales': sales_data, 'revenue': revenue_data},
        'categories': {'labels': cat_labels, 'data': cat_data},
        'monthly': {'labels': monthly_labels, 'revenue': monthly_revenue}
    })
