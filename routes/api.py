from flask import Blueprint, jsonify
from flask_login import login_required
from models.product import Product

api_bp = Blueprint('api', __name__)


@api_bp.route('/api/products/search')
@login_required
def search_products():
    from flask import request
    q = request.args.get('q', '')
    products = Product.query.filter(
        Product.name.ilike(f'%{q}%'),
        Product.is_active == True
    ).limit(10).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'sku': p.sku,
        'selling_price': p.selling_price,
        'gst_percentage': p.gst_percentage,
        'current_stock': p.current_stock,
        'unit': p.unit
    } for p in products])
