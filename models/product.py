from models.database import db
from datetime import datetime
import random
import string


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship('Product', backref='category', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'product_count': self.products.count()
        }


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=True)

    # Pricing
    purchase_price = db.Column(db.Float, nullable=False, default=0)
    selling_price = db.Column(db.Float, nullable=False, default=0)
    gst_percentage = db.Column(db.Float, nullable=False, default=18)

    # Stock
    current_stock = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=10)
    unit = db.Column(db.String(20), default='pcs')

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    invoice_items = db.relationship('InvoiceItem', backref='product', lazy='dynamic')
    inventory_txns = db.relationship('InventoryTransaction', backref='product', lazy='dynamic')

    @staticmethod
    def generate_sku(prefix="PRD"):
        suffix = ''.join(random.choices(string.digits, k=4))
        return f"{prefix}{suffix}"

    @property
    def is_low_stock(self):
        return self.current_stock <= self.reorder_level

    @property
    def stock_value(self):
        return self.current_stock * self.purchase_price

    @property
    def selling_price_with_gst(self):
        return self.selling_price * (1 + self.gst_percentage / 100)

    @property
    def profit_margin(self):
        if self.purchase_price > 0:
            return ((self.selling_price - self.purchase_price) / self.purchase_price) * 100
        return 0

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sku': self.sku,
            'category': self.category.name if self.category else 'Uncategorized',
            'category_id': self.category_id,
            'purchase_price': self.purchase_price,
            'selling_price': self.selling_price,
            'gst_percentage': self.gst_percentage,
            'current_stock': self.current_stock,
            'reorder_level': self.reorder_level,
            'unit': self.unit,
            'is_low_stock': self.is_low_stock,
            'stock_value': self.stock_value,
            'is_active': self.is_active
        }
