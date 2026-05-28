from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models.database import db
from models.product import Product, Category
from models.warehouse import Warehouse
from functools import wraps

products_bp = Blueprint('products', __name__)


def require_role(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if current_user.role not in roles:
                return jsonify({'error': 'Access denied'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


@products_bp.route('/products')
@login_required
def index():
    if not current_user.has_access('products'):
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard.index'))

    categories = Category.query.all()
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    return render_template('products/index.html',
                           categories=categories, warehouses=warehouses)


@products_bp.route('/api/products', methods=['GET'])
@login_required
def get_products():
    search = request.args.get('search', '')
    category_id = request.args.get('category', '')
    low_stock = request.args.get('low_stock', '')
    page = int(request.args.get('page', 1))
    per_page = 15

    query = Product.query.filter_by(is_active=True)

    if search:
        query = query.filter(
            db.or_(
                Product.name.ilike(f'%{search}%'),
                Product.sku.ilike(f'%{search}%')
            )
        )
    if category_id:
        query = query.filter_by(category_id=int(category_id))
    if low_stock == '1':
        query = query.filter(Product.current_stock <= Product.reorder_level)

    total = query.count()
    products = query.order_by(Product.name).offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'products': [p.to_dict() for p in products],
        'total': total,
        'pages': (total + per_page - 1) // per_page,
        'current_page': page
    })


@products_bp.route('/api/products/<int:product_id>', methods=['GET'])
@login_required
def get_product(product_id):
    p = Product.query.get_or_404(product_id)
    return jsonify(p.to_dict())


@products_bp.route('/api/products', methods=['POST'])
@login_required
def create_product():
    if current_user.role not in ['admin', 'inventory_manager']:
        return jsonify({'error': 'Access denied'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Validation
    if not data.get('name') or not data.get('selling_price'):
        return jsonify({'error': 'Name and selling price are required'}), 400

    # Auto-generate SKU if not provided
    sku = data.get('sku', '').strip()
    if not sku:
        sku = Product.generate_sku()
        while Product.query.filter_by(sku=sku).first():
            sku = Product.generate_sku()
    else:
        if Product.query.filter_by(sku=sku).first():
            return jsonify({'error': 'SKU already exists'}), 400

    product = Product(
        name=data['name'],
        sku=sku,
        description=data.get('description', ''),
        category_id=data.get('category_id') or None,
        warehouse_id=data.get('warehouse_id') or None,
        purchase_price=float(data.get('purchase_price', 0)),
        selling_price=float(data['selling_price']),
        gst_percentage=float(data.get('gst_percentage', 18)),
        current_stock=int(data.get('current_stock', 0)),
        reorder_level=int(data.get('reorder_level', 10)),
        unit=data.get('unit', 'pcs')
    )
    db.session.add(product)

    # Record initial stock transaction
    if product.current_stock > 0:
        from models.inventory import InventoryTransaction
        txn = InventoryTransaction(
            product_id=product.id,
            warehouse_id=product.warehouse_id,
            transaction_type='stock_in',
            quantity=product.current_stock,
            unit_price=product.purchase_price,
            reference='INITIAL',
            notes='Initial stock on product creation',
            created_by=current_user.id
        )
        db.session.add(txn)

    db.session.commit()
    return jsonify({'success': True, 'product': product.to_dict()}), 201


@products_bp.route('/api/products/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    if current_user.role not in ['admin', 'inventory_manager']:
        return jsonify({'error': 'Access denied'}), 403

    product = Product.query.get_or_404(product_id)
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Check SKU uniqueness if changed
    new_sku = data.get('sku', '').strip()
    if new_sku and new_sku != product.sku:
        if Product.query.filter_by(sku=new_sku).first():
            return jsonify({'error': 'SKU already exists'}), 400
        product.sku = new_sku

    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.category_id = data.get('category_id') or product.category_id
    product.warehouse_id = data.get('warehouse_id') or product.warehouse_id
    product.purchase_price = float(data.get('purchase_price', product.purchase_price))
    product.selling_price = float(data.get('selling_price', product.selling_price))
    product.gst_percentage = float(data.get('gst_percentage', product.gst_percentage))
    product.reorder_level = int(data.get('reorder_level', product.reorder_level))
    product.unit = data.get('unit', product.unit)

    db.session.commit()
    return jsonify({'success': True, 'product': product.to_dict()})


@products_bp.route('/api/products/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403

    product = Product.query.get_or_404(product_id)
    product.is_active = False  # Soft delete
    db.session.commit()
    return jsonify({'success': True})


@products_bp.route('/api/categories', methods=['GET'])
@login_required
def get_categories():
    categories = Category.query.all()
    return jsonify([c.to_dict() for c in categories])


@products_bp.route('/api/categories', methods=['POST'])
@login_required
def create_category():
    if current_user.role not in ['admin']:
        return jsonify({'error': 'Access denied'}), 403
    data = request.get_json()
    cat = Category(name=data['name'], description=data.get('description', ''))
    db.session.add(cat)
    db.session.commit()
    return jsonify({'success': True, 'category': cat.to_dict()})
