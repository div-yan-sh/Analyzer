from flask import Blueprint, request, jsonify, session
from database.db import db
from database.models import FinancialGoal
from routes.auth_routes import login_required
from datetime import datetime

goal_bp = Blueprint('goal', __name__)

@goal_bp.route('/api/goals', methods=['GET'])
@login_required
def get_goals():
    user_id = session['user_id']
    goals = FinancialGoal.query.filter_by(user_id=user_id).all()
    today = datetime.now().date()

    results = []
    for g in goals:
        g_dict = g.to_dict()
        
        # Calculate progress indicators
        target = g.target_amount
        current = g.current_amount
        pct = (current / target) * 100 if target > 0 else 0.0
        remaining = max(0.0, target - current)
        
        # Suggested monthly contribution
        deadline = g.deadline
        days_left = (deadline - today).days
        months_left = days_left / 30.4
        
        if months_left > 0 and remaining > 0:
            suggested = remaining / months_left
        else:
            suggested = remaining
            
        g_dict.update({
            "percentage": round(pct, 1),
            "remaining_amount": round(remaining, 2),
            "days_remaining": max(0, days_left),
            "suggested_monthly_contribution": round(suggested, 2)
        })
        results.append(g_dict)

    return jsonify(results), 200

@goal_bp.route('/api/goals', methods=['POST'])
@login_required
def add_goal():
    user_id = session['user_id']
    data = request.get_json() or {}

    title = data.get('title')
    target_val = data.get('target_amount')
    current_val = data.get('current_amount', 0.0)
    deadline_str = data.get('deadline')
    description = data.get('description', '').strip()

    if not title or target_val is None or not deadline_str:
        return jsonify({"error": "Title, target amount, and deadline are required."}), 400

    try:
        target_amount = float(target_val)
        current_amount = float(current_val)
        if target_amount <= 0 or current_amount < 0:
            return jsonify({"error": "Amounts must be positive."}), 400
    except ValueError:
        return jsonify({"error": "Invalid numeric amounts."}), 400

    try:
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Expected YYYY-MM-DD."}), 400

    try:
        new_goal = FinancialGoal(
            user_id=user_id,
            title=title.strip(),
            target_amount=target_amount,
            current_amount=current_amount,
            deadline=deadline,
            description=description,
            status='active'
        )
        db.session.add(new_goal)
        db.session.commit()
        return jsonify({"message": "Goal added successfully.", "goal": new_goal.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to add goal: {str(e)}"}), 500

@goal_bp.route('/api/goals/<int:goal_id>', methods=['PUT', 'DELETE'])
@login_required
def modify_goal(goal_id):
    user_id = session['user_id']
    goal = FinancialGoal.query.filter_by(id=goal_id, user_id=user_id).first()

    if not goal:
        return jsonify({"error": "Goal not found."}), 404

    if request.method == 'DELETE':
        try:
            db.session.delete(goal)
            db.session.commit()
            return jsonify({"message": "Goal deleted successfully."}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to delete goal: {str(e)}"}), 500

    if request.method == 'PUT':
        data = request.get_json() or {}
        
        if 'title' in data:
            goal.title = data['title'].strip()
            
        if 'target_amount' in data:
            try:
                goal.target_amount = float(data['target_amount'])
            except ValueError:
                return jsonify({"error": "Invalid target amount."}), 400
                
        if 'current_amount' in data:
            try:
                goal.current_amount = float(data['current_amount'])
            except ValueError:
                return jsonify({"error": "Invalid current amount."}), 400
                
        if 'deadline' in data and data['deadline']:
            try:
                goal.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Invalid deadline date."}), 400
                
        if 'description' in data:
            goal.description = data['description'].strip()
            
        if 'status' in data:
            status = data['status']
            if status in ['active', 'completed']:
                goal.status = status

        try:
            db.session.commit()
            return jsonify({"message": "Goal updated successfully.", "goal": goal.to_dict()}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to update goal: {str(e)}"}), 500
