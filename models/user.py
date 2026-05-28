from models.database import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='cashier')
    # Roles: admin, cashier, inventory_manager
    is_active = db.Column(db.Boolean, default=True)
    avatar = db.Column(db.String(200), nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_access(self, module):
        """Role-based access control"""
        access_map = {
            'admin': ['dashboard', 'products', 'inventory', 'billing', 'users', 'reports', 'settings'],
            'cashier': ['dashboard', 'billing', 'products'],
            'inventory_manager': ['dashboard', 'products', 'inventory', 'reports'],
        }
        return module in access_map.get(self.role, [])

    @property
    def role_display(self):
        roles = {
            'admin': 'Administrator',
            'cashier': 'Cashier',
            'inventory_manager': 'Inventory Manager'
        }
        return roles.get(self.role, self.role.title())

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'role_display': self.role_display,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%d %b %Y')
        }
