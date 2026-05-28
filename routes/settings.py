import os
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from models.database import db
from models.settings import CompanySettings

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/settings')
@login_required
def index():
    if current_user.role != 'admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('dashboard.index'))
    settings = CompanySettings.query.first()
    return render_template('settings/index.html', settings=settings)


@settings_bp.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
    settings = CompanySettings.query.first()
    if not settings:
        return jsonify({})
    return jsonify({
        'company_name': settings.company_name,
        'gst_number': settings.gst_number,
        'pan_number': settings.pan_number,
        'address': settings.address,
        'phone': settings.phone,
        'email': settings.email,
        'website': settings.website,
        'invoice_prefix': settings.invoice_prefix,
        'invoice_footer': settings.invoice_footer,
        'bank_details': settings.bank_details,
        'default_gst': settings.default_gst
    })


@settings_bp.route('/api/settings', methods=['POST'])
@login_required
def update_settings():
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403

    settings = CompanySettings.query.first()
    if not settings:
        settings = CompanySettings()
        db.session.add(settings)

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    settings.company_name = data.get('company_name', settings.company_name)
    settings.gst_number = data.get('gst_number', settings.gst_number)
    settings.pan_number = data.get('pan_number', settings.pan_number)
    settings.address = data.get('address', settings.address)
    settings.phone = data.get('phone', settings.phone)
    settings.email = data.get('email', settings.email)
    settings.website = data.get('website', settings.website)
    settings.invoice_prefix = data.get('invoice_prefix', settings.invoice_prefix)
    settings.invoice_footer = data.get('invoice_footer', settings.invoice_footer)
    settings.bank_details = data.get('bank_details', settings.bank_details)
    settings.default_gst = float(data.get('default_gst', settings.default_gst))

    db.session.commit()
    return jsonify({'success': True})
