from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models.database import db
from models.product import Product
from models.inventory import InventoryTransaction
from models.warehouse import Warehouse

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/inventory')
@login_required
def index():
    if not current_user.has_access('inventory'):
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard.index'))

    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    return render_template('inventory/index.html', products=products, warehouses=warehouses)


@inventory_bp.route('/api/inventory/transactions', methods=['GET'])
@login_required
def get_transactions():
    page = int(request.args.get('page', 1))
    per_page = 20
    product_id = request.args.get('product_id', '')
    txn_type = request.args.get('type', '')

    query = InventoryTransaction.query.join(Product)

    if product_id:
        query = query.filter(InventoryTransaction.product_id == int(product_id))
    if txn_type:
        query = query.filter(InventoryTransaction.transaction_type == txn_type)

    total = query.count()
    txns = query.order_by(InventoryTransaction.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'transactions': [t.to_dict() for t in txns],
        'total': total,
        'pages': (total + per_page - 1) // per_page,
        'current_page': page
    })


@inventory_bp.route('/api/inventory/stock-in', methods=['POST'])
@login_required
def stock_in():
    if current_user.role not in ['admin', 'inventory_manager']:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    product = Product.query.get_or_404(int(data['product_id']))
    quantity = int(data['quantity'])

    if quantity <= 0:
        return jsonify({'error': 'Quantity must be positive'}), 400

    product.current_stock += quantity

    txn = InventoryTransaction(
        product_id=product.id,
        warehouse_id=data.get('warehouse_id') or product.warehouse_id,
        transaction_type='stock_in',
        quantity=quantity,
        unit_price=float(data.get('unit_price') or product.purchase_price),
        reference=data.get('reference', ''),
        notes=data.get('notes', ''),
        created_by=current_user.id
    )
    db.session.add(txn)
    db.session.commit()

    return jsonify({'success': True, 'new_stock': product.current_stock})


@inventory_bp.route('/api/inventory/stock-out', methods=['POST'])
@login_required
def stock_out():
    if current_user.role not in ['admin', 'inventory_manager']:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    product = Product.query.get_or_404(int(data['product_id']))
    quantity = int(data['quantity'])

    if quantity <= 0:
        return jsonify({'error': 'Quantity must be positive'}), 400
    if quantity > product.current_stock:
        return jsonify({'error': f'Insufficient stock. Available: {product.current_stock}'}), 400

    product.current_stock -= quantity

    txn = InventoryTransaction(
        product_id=product.id,
        warehouse_id=data.get('warehouse_id') or product.warehouse_id,
        transaction_type='stock_out',
        quantity=quantity,
        unit_price=float(data.get('unit_price') or product.selling_price),
        reference=data.get('reference', ''),
        notes=data.get('notes', ''),
        created_by=current_user.id
    )
    db.session.add(txn)
    db.session.commit()

    return jsonify({'success': True, 'new_stock': product.current_stock})


@inventory_bp.route('/api/inventory/adjustment', methods=['POST'])
@login_required
def adjustment():
    if current_user.role not in ['admin']:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    product = Product.query.get_or_404(int(data['product_id']))
    new_quantity = int(data['new_quantity'])
    old_quantity = product.current_stock
    diff = new_quantity - old_quantity

    product.current_stock = new_quantity

    txn = InventoryTransaction(
        product_id=product.id,
        warehouse_id=data.get('warehouse_id') or product.warehouse_id,
        transaction_type='adjustment',
        quantity=abs(diff),
        reference=data.get('reference', 'ADJUSTMENT'),
        notes=f"Adjusted from {old_quantity} to {new_quantity}. {data.get('notes', '')}",
        created_by=current_user.id
    )
    db.session.add(txn)
    db.session.commit()

    return jsonify({'success': True, 'new_stock': product.current_stock})
