from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models.database import db
from models.invoice import Invoice, InvoiceItem
from models.product import Product
from models.customer import Customer
from models.inventory import InventoryTransaction
from models.settings import CompanySettings
from datetime import datetime

billing_bp = Blueprint('billing', __name__)


@billing_bp.route('/billing')
@login_required
def index():
    if not current_user.has_access('billing'):
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard.index'))
    customers = Customer.query.filter_by(is_active=True).order_by(Customer.name).all()
    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()
    return render_template('billing/index.html', customers=customers, products=products)


@billing_bp.route('/billing/invoices')
@login_required
def invoices():
    if not current_user.has_access('billing'):
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard.index'))
    return render_template('billing/invoices.html')


@billing_bp.route('/billing/invoice/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    settings = CompanySettings.query.first()
    items = invoice.items.all()
    return render_template('billing/invoice_view.html',
                           invoice=invoice, items=items, settings=settings)


@billing_bp.route('/billing/invoice/<int:invoice_id>/print')
@login_required
def print_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    settings = CompanySettings.query.first()
    items = invoice.items.all()
    return render_template('billing/invoice_print.html',
                           invoice=invoice, items=items, settings=settings)


@billing_bp.route('/api/invoices', methods=['GET'])
@login_required
def get_invoices():
    page = int(request.args.get('page', 1))
    per_page = 15
    search = request.args.get('search', '')
    status = request.args.get('status', '')

    query = Invoice.query

    if search:
        query = query.filter(Invoice.invoice_number.ilike(f'%{search}%'))
    if status:
        query = query.filter_by(payment_status=status)

    total = query.count()
    invoices = query.order_by(Invoice.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'invoices': [inv.to_dict() for inv in invoices],
        'total': total,
        'pages': (total + per_page - 1) // per_page,
        'current_page': page
    })


@billing_bp.route('/api/invoices', methods=['POST'])
@login_required
def create_invoice():
    data = request.get_json()
    if not data or not data.get('items'):
        return jsonify({'error': 'Invoice items are required'}), 400

    settings = CompanySettings.query.first()
    invoice_number = settings.get_next_invoice_number()

    invoice = Invoice(
        invoice_number=invoice_number,
        customer_id=data.get('customer_id') or None,
        invoice_date=datetime.utcnow(),
        payment_status=data.get('payment_status', 'paid'),
        payment_mode=data.get('payment_mode', 'cash'),
        notes=data.get('notes', ''),
        discount=float(data.get('discount', 0)),
        created_by=current_user.id
    )
    db.session.add(invoice)
    db.session.flush()

    subtotal = 0
    total_gst = 0

    for item_data in data['items']:
        product = Product.query.get(int(item_data['product_id']))
        if not product:
            continue

        qty = int(item_data['quantity'])
        unit_price = float(item_data.get('unit_price', product.selling_price))
        gst_pct = float(item_data.get('gst_percentage', product.gst_percentage))
        gst_amount = (unit_price * qty * gst_pct) / 100
        total = unit_price * qty + gst_amount

        item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=product.id,
            quantity=qty,
            unit_price=unit_price,
            gst_percentage=gst_pct,
            gst_amount=gst_amount,
            total_amount=total
        )
        db.session.add(item)
        subtotal += unit_price * qty
        total_gst += gst_amount

        # Reduce stock
        if product.current_stock >= qty:
            product.current_stock -= qty
            txn = InventoryTransaction(
                product_id=product.id,
                warehouse_id=product.warehouse_id,
                transaction_type='sale',
                quantity=qty,
                unit_price=unit_price,
                reference=invoice_number,
                notes=f'Sale via invoice {invoice_number}',
                created_by=current_user.id
            )
            db.session.add(txn)

    invoice.subtotal = subtotal
    invoice.total_gst = total_gst
    invoice.total_amount = subtotal + total_gst - invoice.discount

    db.session.commit()

    return jsonify({
        'success': True,
        'invoice_id': invoice.id,
        'invoice_number': invoice.invoice_number,
        'total': invoice.total_amount
    }), 201


@billing_bp.route('/api/invoices/<int:invoice_id>/status', methods=['PUT'])
@login_required
def update_invoice_status(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    data = request.get_json()
    invoice.payment_status = data.get('status', invoice.payment_status)
    invoice.payment_mode = data.get('payment_mode', invoice.payment_mode)
    db.session.commit()
    return jsonify({'success': True})


@billing_bp.route('/api/customers', methods=['GET'])
@login_required
def get_customers():
    customers = Customer.query.filter_by(is_active=True).order_by(Customer.name).all()
    return jsonify([c.to_dict() for c in customers])


@billing_bp.route('/api/customers', methods=['POST'])
@login_required
def create_customer():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'error': 'Customer name is required'}), 400

    # Generate customer code
    count = Customer.query.count() + 1
    code = f"CUST{count:04d}"

    customer = Customer(
        name=data['name'],
        customer_code=code,
        phone=data.get('phone', ''),
        email=data.get('email', ''),
        gst_number=data.get('gst_number', ''),
        address=data.get('address', '')
    )
    db.session.add(customer)
    db.session.commit()
    return jsonify({'success': True, 'customer': customer.to_dict()}), 201
