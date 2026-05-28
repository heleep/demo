from models.database import db
from datetime import datetime


class Invoice(db.Model):
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    invoice_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Amounts
    subtotal = db.Column(db.Float, default=0)
    total_gst = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, default=0)

    # Payment
    payment_status = db.Column(db.String(20), default='pending')
    # Statuses: pending, paid, cancelled
    payment_mode = db.Column(db.String(20), nullable=True)
    # Modes: cash, upi, card, bank_transfer

    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('InvoiceItem', backref='invoice', lazy='dynamic', cascade='all, delete-orphan')
    creator = db.relationship('User', foreign_keys=[created_by])

    @property
    def status_badge_class(self):
        classes = {
            'paid': 'badge-success',
            'pending': 'badge-warning',
            'cancelled': 'badge-danger'
        }
        return classes.get(self.payment_status, 'badge-secondary')

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'customer': self.customer.name if self.customer else 'Walk-in',
            'customer_id': self.customer_id,
            'invoice_date': self.invoice_date.strftime('%d %b %Y'),
            'subtotal': self.subtotal,
            'total_gst': self.total_gst,
            'discount': self.discount,
            'total_amount': self.total_amount,
            'payment_status': self.payment_status,
            'payment_mode': self.payment_mode,
            'items_count': self.items.count()
        }


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    gst_percentage = db.Column(db.Float, default=0)
    gst_amount = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'product': self.product.name if self.product else '',
            'sku': self.product.sku if self.product else '',
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'gst_percentage': self.gst_percentage,
            'gst_amount': self.gst_amount,
            'total_amount': self.total_amount
        }
