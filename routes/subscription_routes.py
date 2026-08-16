from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session
from database.db import db
from database.models import Subscription, User
from routes.auth_routes import login_required

subscription_bp = Blueprint('subscription', __name__)

@subscription_bp.route('/api/subscriptions', methods=['GET', 'POST'])
@login_required
def subscriptions():
    user_id = session['user_id']

    if request.method == 'GET':
        subs = Subscription.query.filter_by(user_id=user_id).order_by(Subscription.next_billing_date.asc()).all()
        return jsonify([s.to_dict() for s in subs]), 200

    if request.method == 'POST':
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        amount = data.get('amount')
        billing_cycle = data.get('billing_cycle', 'monthly')
        next_billing_date_str = data.get('next_billing_date')
        category = data.get('category', 'Entertainment')
        payment_method = data.get('payment_method', 'UPI')
        notes = data.get('notes', '').strip()

        if not name or amount is None or not next_billing_date_str:
            return jsonify({"error": "Name, amount, and next billing date are required."}), 400

        try:
            amount = float(amount)
            if amount <= 0:
                return jsonify({"error": "Amount must be positive."}), 400
        except ValueError:
            return jsonify({"error": "Invalid amount format."}), 400

        try:
            next_date = datetime.strptime(next_billing_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Expected YYYY-MM-DD."}), 400

        # Auto select icon based on subscription name
        name_lower = name.lower()
        icon = 'fa-solid fa-bell'
        if 'netflix' in name_lower or 'prime' in name_lower or 'hotstar' in name_lower or 'movie' in name_lower:
            icon = 'fa-solid fa-film'
        elif 'spotify' in name_lower or 'apple music' in name_lower or 'youtube' in name_lower or 'music' in name_lower:
            icon = 'fa-solid fa-music'
        elif 'gym' in name_lower or 'fitness' in name_lower:
            icon = 'fa-solid fa-dumbbell'
        elif 'mess' in name_lower or 'tiffin' in name_lower or 'food' in name_lower:
            icon = 'fa-solid fa-utensils'
        elif 'wifi' in name_lower or 'broadband' in name_lower or 'internet' in name_lower:
            icon = 'fa-solid fa-wifi'
        elif 'cloud' in name_lower or 'drive' in name_lower or 'icloud' in name_lower:
            icon = 'fa-solid fa-cloud'

        try:
            sub = Subscription(
                user_id=user_id,
                name=name,
                amount=amount,
                billing_cycle=billing_cycle,
                next_billing_date=next_date,
                category=category,
                payment_method=payment_method,
                status='active',
                icon=icon,
                notes=notes
            )
            db.session.add(sub)
            db.session.commit()
            return jsonify({"message": "Subscription added successfully.", "subscription": sub.to_dict()}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to save subscription: {str(e)}"}), 500

@subscription_bp.route('/api/subscriptions/<int:sub_id>', methods=['PUT', 'DELETE'])
@login_required
def modify_subscription(sub_id):
    user_id = session['user_id']
    sub = Subscription.query.filter_by(id=sub_id, user_id=user_id).first()

    if not sub:
        return jsonify({"error": "Subscription not found."}), 404

    if request.method == 'DELETE':
        try:
            db.session.delete(sub)
            db.session.commit()
            return jsonify({"message": "Subscription removed."}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to delete subscription: {str(e)}"}), 500

    if request.method == 'PUT':
        data = request.get_json() or {}
        if 'name' in data:
            sub.name = data['name'].strip()
        if 'amount' in data:
            sub.amount = float(data['amount'])
        if 'billing_cycle' in data:
            sub.billing_cycle = data['billing_cycle']
        if 'category' in data:
            sub.category = data['category']
        if 'status' in data:
            sub.status = data['status']
        if 'notes' in data:
            sub.notes = data['notes']
        if 'next_billing_date' in data and data['next_billing_date']:
            try:
                sub.next_billing_date = datetime.strptime(data['next_billing_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Invalid date format."}), 400

        try:
            db.session.commit()
            return jsonify({"message": "Subscription updated.", "subscription": sub.to_dict()}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to update subscription: {str(e)}"}), 500

@subscription_bp.route('/api/subscriptions/summary', methods=['GET'])
@login_required
def subscriptions_summary():
    """Calculates monthly run-rate, active count, and upcoming renewals in the next 7 days."""
    user_id = session['user_id']
    subs = Subscription.query.filter_by(user_id=user_id, status='active').all()
    
    monthly_total = 0.0
    upcoming_7_days = []
    today = datetime.now().date()
    seven_days = today + timedelta(days=7)

    for s in subs:
        # Normalize to monthly cost
        if s.billing_cycle == 'yearly':
            monthly_cost = s.amount / 12.0
        elif s.billing_cycle == 'quarterly':
            monthly_cost = s.amount / 3.0
        else:
            monthly_cost = s.amount
        monthly_total += monthly_cost

        if s.next_billing_date and today <= s.next_billing_date <= seven_days:
            upcoming_7_days.append(s.to_dict())

    return jsonify({
        "monthly_run_rate": round(monthly_total, 2),
        "yearly_cost": round(monthly_total * 12, 2),
        "active_count": len(subs),
        "upcoming_renewals": upcoming_7_days
    }), 200
