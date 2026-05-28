from models.database import db
from datetime import datetime


class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    customer_code = db.Column(db.String(20), unique=True, nullable=True)
    phone = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    gst_number = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    invoices = db.relationship('Invoice', backref='customer', lazy='dynamic')

    @property
    def total_purchases(self):
        return sum(inv.total_amount for inv in self.invoices if inv.payment_status == 'paid')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'customer_code': self.customer_code,
            'phone': self.phone,
            'email': self.email,
            'gst_number': self.gst_number,
            'address': self.address,
        }
