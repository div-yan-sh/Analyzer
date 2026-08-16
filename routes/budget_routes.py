from flask import Blueprint, request, jsonify, session
from database.db import db
from database.models import Budget, Expense
from routes.auth_routes import login_required
from datetime import datetime

budget_bp = Blueprint('budget', __name__)

@budget_bp.route('/api/budget', methods=['GET'])
@login_required
def get_budgets():
    user_id = session['user_id']
    
    # Query parameters
    now = datetime.now()
    month = request.args.get('month', now.month, type=int)
    year = request.args.get('year', now.year, type=int)

    # Fetch budgets for this month/year
    budgets = Budget.query.filter_by(user_id=user_id, month=month, year=year).all()
    
    # Fetch expenses for this month/year
    start_date = datetime(year, month, 1).date()
    # Handle end of month date calculations
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
        
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.expense_date >= start_date,
        Expense.expense_date < end_date
    ).all()

    # Calculate spent amounts
    total_spent = sum(e.amount for e in expenses)
    category_spent = {}
    for e in expenses:
        category_spent[e.category] = category_spent.get(e.category, 0) + e.amount

    # Build response data structure
    overall_budget_item = next((b for b in budgets if b.category is None), None)
    overall_amount = overall_budget_item.amount if overall_budget_item else 0.0

    utilization_list = []
    
    # Calculate for overall budget
    if overall_amount > 0:
        pct = (total_spent / overall_amount) * 100
        rem = overall_amount - total_spent
        if pct < 60:
            status_desc = "You're comfortably within your budget."
            status_level = "success"
        elif pct < 80:
            status_desc = "You're approaching your budget limit."
            status_level = "info"
        elif pct <= 100:
            status_desc = "Your spending is getting high."
            status_level = "warning"
        else:
            status_desc = "You have exceeded your monthly budget."
            status_level = "danger"
            
        utilization_list.append({
            "category": "Overall",
            "budget": overall_amount,
            "spent": round(total_spent, 2),
            "remaining": round(rem, 2),
            "percentage": round(pct, 1),
            "warning_text": status_desc,
            "status_level": status_level
        })
    else:
        utilization_list.append({
            "category": "Overall",
            "budget": 0,
            "spent": round(total_spent, 2),
            "remaining": 0,
            "percentage": 0,
            "warning_text": "No overall budget set for this month.",
            "status_level": "muted"
        })

    # Calculate for category budgets
    for b in budgets:
        if b.category is None:
            continue
        c_spent = category_spent.get(b.category, 0.0)
        c_pct = (c_spent / b.amount) * 100 if b.amount > 0 else 0
        c_rem = b.amount - c_spent
        
        if c_pct < 60:
            c_desc = f"Spent is normal."
            c_lvl = "success"
        elif c_pct < 80:
            c_desc = f"Spent approaching budget limit for {b.category}."
            c_lvl = "info"
        elif c_pct <= 100:
            c_desc = f"Spent is getting high for {b.category}."
            c_lvl = "warning"
        else:
            c_desc = f"Exceeded {b.category} budget!"
            c_lvl = "danger"

        utilization_list.append({
            "category": b.category,
            "budget": b.amount,
            "spent": round(c_spent, 2),
            "remaining": round(c_rem, 2),
            "percentage": round(c_pct, 1),
            "warning_text": c_desc,
            "status_level": c_lvl
        })

    return jsonify({
        "month": month,
        "year": year,
        "budgets": [b.to_dict() for b in budgets],
        "utilization": utilization_list
    }), 200

@budget_bp.route('/api/budget', methods=['POST', 'PUT'])
@login_required
def set_budget():
    user_id = session['user_id']
    data = request.get_json() or {}

    amount_val = data.get('amount')
    category = data.get('category')  # Can be string or null/empty
    now = datetime.now()
    month = data.get('month', now.month)
    year = data.get('year', now.year)

    if amount_val is None:
        return jsonify({"error": "Amount is required."}), 400

    try:
        amount = float(amount_val)
        if amount < 0:
            return jsonify({"error": "Amount cannot be negative."}), 400
    except ValueError:
        return jsonify({"error": "Invalid amount format."}), 400

    # Standardize category
    if not category or category.strip() == '' or category.lower() == 'overall':
        category = None
    else:
        category = category.strip()

    try:
        # Check if budget already exists
        existing = Budget.query.filter_by(
            user_id=user_id,
            month=int(month),
            year=int(year),
            category=category
        ).first()

        if existing:
            existing.amount = amount
            message = "Budget updated successfully."
            res_budget = existing
        else:
            new_budget = Budget(
                user_id=user_id,
                month=int(month),
                year=int(year),
                amount=amount,
                category=category
            )
            db.session.add(new_budget)
            message = "Budget set successfully."
            res_budget = new_budget

        db.session.commit()
        return jsonify({"message": message, "budget": res_budget.to_dict()}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to save budget: {str(e)}"}), 500
