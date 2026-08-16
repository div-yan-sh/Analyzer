from flask import Blueprint, request, jsonify, session
from database.db import db
from database.models import Expense, AIInsight
from routes.auth_routes import login_required
from ml.category_classifier import classify_category
from ml.anomaly_detection import check_single_expense_anomaly
from datetime import datetime

expense_bp = Blueprint('expense', __name__)

@expense_bp.route('/api/expenses', methods=['GET'])
@login_required
def get_expenses():
    user_id = session['user_id']
    
    # Query parameters
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    payment_method = request.args.get('payment_method', '').strip()
    start_date_str = request.args.get('start_date', '').strip()
    end_date_str = request.args.get('end_date', '').strip()
    min_amount = request.args.get('min_amount', type=float)
    max_amount = request.args.get('max_amount', type=float)
    sort_by = request.args.get('sort_by', 'expense_date').strip()
    sort_order = request.args.get('sort_order', 'desc').strip()

    query = Expense.query.filter_by(user_id=user_id)

    # Filtering
    if search:
        query = query.filter(
            (Expense.description.ilike(f"%{search}%")) |
            (Expense.subcategory.ilike(f"%{search}%"))
        )
    if category:
        query = query.filter(Expense.category == category)
    if payment_method:
        query = query.filter(Expense.payment_method == payment_method)
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            query = query.filter(Expense.expense_date >= start_date)
        except ValueError:
            pass
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            query = query.filter(Expense.expense_date <= end_date)
        except ValueError:
            pass
    if min_amount is not None:
        query = query.filter(Expense.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Expense.amount <= max_amount)

    # Sorting
    sort_column = getattr(Expense, sort_by, Expense.expense_date)
    if sort_order == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Pagination
    pagination = query.paginate(page=page, per_page=limit, error_out=False)
    expenses = [exp.to_dict() for exp in pagination.items]

    return jsonify({
        "expenses": expenses,
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "has_prev": pagination.has_prev,
        "has_next": pagination.has_next
    }), 200

@expense_bp.route('/api/expenses', methods=['POST'])
@login_required
def add_expense():
    user_id = session['user_id']
    data = request.get_json() or {}

    amount_val = data.get('amount')
    description = data.get('description', '').strip()
    category = data.get('category', '').strip()
    subcategory = data.get('subcategory', '').strip()
    payment_method = data.get('payment_method')
    expense_date_str = data.get('expense_date')
    is_essential = data.get('is_essential', True)

    if amount_val is None or not payment_method:
        return jsonify({"error": "Amount and payment method are required."}), 400

    try:
        amount = float(amount_val)
        if amount <= 0:
            return jsonify({"error": "Amount must be greater than zero."}), 400
    except ValueError:
        return jsonify({"error": "Invalid amount format."}), 400

    # Auto detect category if not supplied or set to Auto
    if not category or category.lower() == 'auto':
        category = classify_category(description)

    # Date processing
    if expense_date_str:
        try:
            expense_date = datetime.strptime(expense_date_str, '%Y-%m-%d').date()
        except ValueError:
            expense_date = datetime.utcnow().date()
    else:
        expense_date = datetime.utcnow().date()

    try:
        # Create Expense record
        new_expense = Expense(
            user_id=user_id,
            amount=amount,
            category=category,
            subcategory=subcategory,
            description=description,
            payment_method=payment_method,
            expense_date=expense_date,
            is_essential=is_essential
        )
        db.session.add(new_expense)
        
        # Check anomaly before committing so we can return warnings
        historical_expenses = Expense.query.filter_by(user_id=user_id).all()
        is_anomaly, z_score, reason = check_single_expense_anomaly(amount, category, historical_expenses)
        
        anomaly_warning = None
        if is_anomaly:
            anomaly_warning = reason
            # Write an AI insight record
            insight = AIInsight(
                user_id=user_id,
                title=f"Unusual {category} Spending",
                content=reason,
                insight_type="anomaly"
            )
            db.session.add(insight)

        db.session.commit()

        return jsonify({
            "message": "Expense added successfully.",
            "expense": new_expense.to_dict(),
            "anomaly_warning": anomaly_warning
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to add expense: {str(e)}"}), 500

@expense_bp.route('/api/expenses/<int:expense_id>', methods=['PUT', 'DELETE'])
@login_required
def modify_expense(expense_id):
    user_id = session['user_id']
    expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first()

    if not expense:
        return jsonify({"error": "Expense not found."}), 404

    if request.method == 'DELETE':
        try:
            db.session.delete(expense)
            db.session.commit()
            return jsonify({"message": "Expense deleted successfully."}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to delete expense: {str(e)}"}), 500

    if request.method == 'PUT':
        data = request.get_json() or {}
        
        # Update attributes
        if 'amount' in data:
            try:
                amount = float(data['amount'])
                if amount <= 0:
                    return jsonify({"error": "Amount must be greater than zero."}), 400
                expense.amount = amount
            except ValueError:
                return jsonify({"error": "Invalid amount format."}), 400

        if 'description' in data:
            expense.description = data['description'].strip()
            
        if 'category' in data:
            category = data['category'].strip()
            if category:
                expense.category = category
                
        if 'subcategory' in data:
            expense.subcategory = data['subcategory'].strip()
            
        if 'payment_method' in data:
            expense.payment_method = data['payment_method']
            
        if 'expense_date' in data and data['expense_date']:
            try:
                expense.expense_date = datetime.strptime(data['expense_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Invalid date format. Expected YYYY-MM-DD."}), 400
                
        if 'is_essential' in data:
            expense.is_essential = bool(data['is_essential'])

        try:
            db.session.commit()
            return jsonify({"message": "Expense updated successfully.", "expense": expense.to_dict()}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to update expense: {str(e)}"}), 500
