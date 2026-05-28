from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models.database import db
from models.invoice import Invoice, InvoiceItem
from models.product import Product, Category
from models.inventory import InventoryTransaction
from sqlalchemy import func
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/reports')
@login_required
def index():
    if not current_user.has_access('reports'):
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard.index'))
    return render_template('reports/index.html')


@reports_bp.route('/api/reports/sales')
@login_required
def sales_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Invoice.query.filter(Invoice.payment_status == 'paid')

    if start_date:
        query = query.filter(Invoice.invoice_date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(Invoice.invoice_date <= datetime.strptime(end_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))

    invoices = query.order_by(Invoice.invoice_date.desc()).all()

    total_sales = len(invoices)
    total_revenue = sum(inv.total_amount for inv in invoices)
    total_gst = sum(inv.total_gst for inv in invoices)

    return jsonify({
        'summary': {
            'total_sales': total_sales,
            'total_revenue': round(total_revenue, 2),
            'total_gst': round(total_gst, 2),
            'net_revenue': round(total_revenue - total_gst, 2)
        },
        'invoices': [inv.to_dict() for inv in invoices]
    })


@reports_bp.route('/api/reports/inventory')
@login_required
def inventory_report():
    products = Product.query.filter_by(is_active=True).all()
    categories = Category.query.all()

    total_value = sum(p.stock_value for p in products)
    low_stock = [p.to_dict() for p in products if p.is_low_stock]
    out_of_stock = [p.to_dict() for p in products if p.current_stock == 0]

    # Category summary
    cat_summary = []
    for cat in categories:
        prods = cat.products.filter_by(is_active=True).all()
        cat_summary.append({
            'category': cat.name,
            'products': len(prods),
            'total_stock': sum(p.current_stock for p in prods),
            'total_value': round(sum(p.stock_value for p in prods), 2)
        })

    return jsonify({
        'summary': {
            'total_products': len(products),
            'total_inventory_value': round(total_value, 2),
            'low_stock_count': len(low_stock),
            'out_of_stock_count': len(out_of_stock)
        },
        'products': [p.to_dict() for p in products],
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'category_summary': cat_summary
    })


@reports_bp.route('/api/reports/revenue')
@login_required
def revenue_summary():
    # Last 12 months
    months = []
    for i in range(11, -1, -1):
        date = datetime.utcnow() - timedelta(days=i * 30)
        from sqlalchemy import extract
        rev = db.session.query(func.sum(Invoice.total_amount)).filter(
            Invoice.payment_status == 'paid',
            extract('month', Invoice.invoice_date) == date.month,
            extract('year', Invoice.invoice_date) == date.year
        ).scalar() or 0
        count = Invoice.query.filter(
            Invoice.payment_status == 'paid',
            extract('month', Invoice.invoice_date) == date.month,
            extract('year', Invoice.invoice_date) == date.year
        ).count()
        months.append({
            'month': date.strftime('%b %Y'),
            'revenue': round(rev, 2),
            'sales': count
        })

    return jsonify({'monthly_data': months})
