from models.database import db
from datetime import datetime


class InventoryTransaction(db.Model):
    __tablename__ = 'inventory_transactions'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=True)
    transaction_type = db.Column(db.String(20), nullable=False)
    # Types: stock_in, stock_out, adjustment, sale, return
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=True)
    reference = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by])

    @property
    def type_display(self):
        types = {
            'stock_in': 'Stock In',
            'stock_out': 'Stock Out',
            'adjustment': 'Adjustment',
            'sale': 'Sale',
            'return': 'Return'
        }
        return types.get(self.transaction_type, self.transaction_type.title())

    @property
    def type_badge_class(self):
        classes = {
            'stock_in': 'badge-success',
            'stock_out': 'badge-danger',
            'adjustment': 'badge-warning',
            'sale': 'badge-info',
            'return': 'badge-secondary'
        }
        return classes.get(self.transaction_type, 'badge-secondary')

    def to_dict(self):
        return {
            'id': self.id,
            'product': self.product.name if self.product else '',
            'sku': self.product.sku if self.product else '',
            'type': self.transaction_type,
            'type_display': self.type_display,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'reference': self.reference,
            'notes': self.notes,
            'created_by': self.creator.name if self.creator else '',
            'created_at': self.created_at.strftime('%d %b %Y, %I:%M %p')
        }
