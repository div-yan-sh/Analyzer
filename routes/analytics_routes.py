from flask import Blueprint, request, jsonify, session
from database.db import db
from database.models import Expense, Budget, FinancialGoal, User
from routes.auth_routes import login_required
from ml.preprocessing import expenses_to_df, aggregate_by_category, aggregate_by_date, get_daily_average
from ml.spending_prediction import predict_current_month_end
from ml.anomaly_detection import scan_all_anomalies
from services.expense_analyzer import calculate_financial_health_score
from datetime import datetime, timedelta
import pandas as pd

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/api/analytics/summary', methods=['GET'])
@login_required
def get_summary():
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    now = datetime.now()
    curr_month = now.month
    curr_year = now.year

    # Fetch expenses for current month
    start_date = datetime(curr_year, curr_month, 1).date()
    if curr_month == 12:
        end_date = datetime(curr_year + 1, 1, 1).date()
    else:
        end_date = datetime(curr_year, curr_month + 1, 1).date()

    expenses_all = Expense.query.filter_by(user_id=user_id).all()
    expenses_curr = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.expense_date >= start_date,
        Expense.expense_date < end_date
    ).all()

    overall_budget_item = Budget.query.filter_by(user_id=user_id, month=curr_month, year=curr_year, category=None).first()
    budget_amount = overall_budget_item.amount if overall_budget_item else 0.0

    # Convert to DataFrames
    df_all = expenses_to_df(expenses_all)
    df_curr = expenses_to_df(expenses_curr)

    total_spent = float(df_curr['amount'].sum()) if not df_curr.empty else 0.0
    daily_avg = get_daily_average(df_curr, days=now.day)

    # Predictions
    predicted_spend, _, _ = predict_current_month_end(expenses_all, budget_amount)

    # Health score
    budgets_all = Budget.query.filter_by(user_id=user_id).all()
    goals_all = FinancialGoal.query.filter_by(user_id=user_id).all()
    health_score_data = calculate_financial_health_score(user, expenses_all, budgets_all, goals_all)

    # In-app notifications/alerts checks
    alerts = []
    if budget_amount > 0:
        pct = (total_spent / budget_amount) * 100
        if pct >= 100:
            alerts.append({"type": "danger", "message": f"🚨 You have exceeded your monthly budget by ₹{round(total_spent - budget_amount, 2)}!"})
        elif pct >= 80:
            alerts.append({"type": "warning", "message": f"⚠ Budget usage is above 80% ({round(pct, 1)}% used)."})
            
    if predicted_spend > budget_amount > 0:
        alerts.append({"type": "warning", "message": f"🔮 Forecast alert: Your predicted monthly spending (₹{round(predicted_spend, 2)}) is above your budget limit."})

    for g in goals_all:
        if g.status == 'active':
            g_pct = (g.current_amount / g.target_amount) * 100 if g.target_amount > 0 else 0
            if g_pct >= 80:
                alerts.append({"type": "success", "message": f"🎯 You are {round(g_pct, 1)}% toward your goal: '{g.title}'!"})

    # Find anomalies to alert in-app
    detected_anoms = scan_all_anomalies(expenses_all)
    current_month_anoms = [a for a in detected_anoms if datetime.strptime(a['expense_date'], '%Y-%m-%d').month == curr_month]
    for anom in current_month_anoms[:2]:  # Show top 2 recent anomalies
        alerts.append({"type": "warning", "message": f"📈 Unusual expense detected: ₹{anom['amount']} spent on {anom['category']} ('{anom['description']}')."})

    if not alerts:
        alerts.append({"type": "success", "message": "✅ You stayed under budget this week! Keep it up."})

    return jsonify({
        "total_spent": round(total_spent, 2),
        "budget": budget_amount,
        "daily_average": round(daily_avg, 2),
        "predicted_spend": round(predicted_spend, 2),
        "health_score": health_score_data["score"],
        "health_rating": health_score_data["rating"],
        "health_explanation": health_score_data["explanation"],
        "alerts": alerts
    }), 200

@analytics_bp.route('/api/analytics/categories', methods=['GET'])
@login_required
def get_category_analytics():
    user_id = session['user_id']
    
    # Optional date range query params
    start_date_str = request.args.get('start_date', '').strip()
    end_date_str = request.args.get('end_date', '').strip()

    query = Expense.query.filter_by(user_id=user_id)

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

    expenses = query.all()
    df = expenses_to_df(expenses)

    if df.empty:
        return jsonify({
            "categories": {},
            "payment_methods": {},
            "essential_vs_non_essential": {"essential": 0, "non_essential": 0}
        }), 200

    # Category totals
    cat_totals = df.groupby('category')['amount'].sum().to_dict()
    cat_totals = {k: round(float(v), 2) for k, v in cat_totals.items()}

    # Payment methods distribution
    pm_totals = df.groupby('payment_method')['amount'].sum().to_dict()
    pm_totals = {k: round(float(v), 2) for k, v in pm_totals.items()}

    # Essential vs Non-essential distribution
    essential_totals = df.groupby('is_essential')['amount'].sum().to_dict()
    essential_dist = {
        "essential": round(float(essential_totals.get(True, 0.0)), 2),
        "non_essential": round(float(essential_totals.get(False, 0.0)), 2)
    }

    return jsonify({
        "categories": cat_totals,
        "payment_methods": pm_totals,
        "essential_vs_non_essential": essential_dist
    }), 200

@analytics_bp.route('/api/analytics/monthly', methods=['GET'])
@login_required
def get_monthly_analytics():
    user_id = session['user_id']
    expenses = Expense.query.filter_by(user_id=user_id).all()
    df = expenses_to_df(expenses)

    if df.empty:
        return jsonify([]), 200

    # Group by month/year for the last 6 months
    df['month_year'] = df['expense_date'].dt.strftime('%b %Y')
    df['period_index'] = df['expense_date'].dt.to_period('M')
    
    monthly_grouped = df.groupby(['period_index', 'month_year'])['amount'].sum().reset_index()
    monthly_grouped = monthly_grouped.sort_values('period_index').tail(6)

    result = []
    for _, row in monthly_grouped.iterrows():
        result.append({
            "label": row['month_year'],
            "total": round(float(row['amount']), 2)
        })

    return jsonify(result), 200

@analytics_bp.route('/api/analytics/trends', methods=['GET'])
@login_required
def get_trends():
    user_id = session['user_id']
    days = request.args.get('days', 30, type=int)

    start_date = datetime.now().date() - timedelta(days=days)
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.expense_date >= start_date
    ).all()

    df = expenses_to_df(expenses)
    if df.empty:
        return jsonify([]), 200

    # Aggregated by date
    daily_sums = df.groupby(df['expense_date'].dt.strftime('%Y-%m-%d'))['amount'].sum().to_dict()
    
    # Fill in intermediate dates
    date_list = [start_date + timedelta(days=x) for x in range(days + 1)]
    result = []
    for d in date_list:
        date_str = d.strftime('%Y-%m-%d')
        result.append({
            "date": date_str,
            "total": round(float(daily_sums.get(date_str, 0.0)), 2)
        })

    return jsonify(result), 200

@analytics_bp.route('/api/anomalies', methods=['GET'])
@login_required
def get_anomalies():
    user_id = session['user_id']
    expenses = Expense.query.filter_by(user_id=user_id).all()
    anomalies = scan_all_anomalies(expenses)
    return jsonify(anomalies), 200

@analytics_bp.route('/api/insights', methods=['GET'])
@login_required
def get_insights():
    user_id = session['user_id']
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404
    expenses = Expense.query.filter_by(user_id=user_id).all()
    budgets = Budget.query.filter_by(user_id=user_id).all()
    goals = FinancialGoal.query.filter_by(user_id=user_id).all()
    
    from services.recommendation_engine import generate_recommendations
    recs = generate_recommendations(user, expenses, budgets, goals)
    return jsonify(recs), 200

