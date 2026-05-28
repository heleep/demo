from models.database import db
from datetime import datetime


class CompanySettings(db.Model):
    __tablename__ = 'company_settings'

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), nullable=False, default='My Company')
    gst_number = db.Column(db.String(20), nullable=True)
    pan_number = db.Column(db.String(15), nullable=True)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    website = db.Column(db.String(200), nullable=True)
    logo = db.Column(db.String(200), nullable=True)

    # Invoice settings
    invoice_prefix = db.Column(db.String(10), default='INV')
    invoice_counter = db.Column(db.Integer, default=1001)
    invoice_footer = db.Column(db.Text, nullable=True)
    bank_details = db.Column(db.Text, nullable=True)

    # Tax settings
    default_gst = db.Column(db.Float, default=18)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_next_invoice_number(self):
        from models.database import db
        num = f"{self.invoice_prefix}{self.invoice_counter:04d}"
        self.invoice_counter += 1
        db.session.flush()  # persist counter increment before invoice INSERT
        return num
