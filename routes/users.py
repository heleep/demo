from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models.database import db
from models.user import User
from werkzeug.security import generate_password_hash
from config import Config

users_bp = Blueprint('users', __name__)


@users_bp.route('/users')
@login_required
def index():
    if current_user.role != 'admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('dashboard.index'))
    users = User.query.all()
    return render_template('users/index.html', users=users, max_users=Config.MAX_USERS)


@users_bp.route('/api/users', methods=['GET'])
@login_required
def get_users():
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])


@users_bp.route('/api/users', methods=['POST'])
@login_required
def create_user():
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403

    # Starter plan limit
    current_count = User.query.filter_by(is_active=True).count()
    if current_count >= Config.MAX_USERS:
        return jsonify({'error': f'Starter Plan allows maximum {Config.MAX_USERS} users. Upgrade to add more.'}), 400

    data = request.get_json()
    if not data or not all([data.get('name'), data.get('email'), data.get('password')]):
        return jsonify({'error': 'Name, email and password are required'}), 400

    if User.query.filter_by(email=data['email'].lower()).first():
        return jsonify({'error': 'Email already registered'}), 400

    user = User(
        name=data['name'],
        email=data['email'].lower(),
        password_hash=generate_password_hash(data['password']),
        role=data.get('role', 'cashier'),
        is_active=True
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True, 'user': user.to_dict()}), 201


@users_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403

    user = User.query.get_or_404(user_id)
    data = request.get_json()

    user.name = data.get('name', user.name)
    user.role = data.get('role', user.role)
    user.is_active = data.get('is_active', user.is_active)

    if data.get('password'):
        user.password_hash = generate_password_hash(data['password'])

    db.session.commit()
    return jsonify({'success': True, 'user': user.to_dict()})


@users_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400

    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    return jsonify({'success': True})
