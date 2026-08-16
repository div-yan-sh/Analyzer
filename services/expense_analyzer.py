from datetime import datetime, timedelta
import pandas as pd
from ml.preprocessing import expenses_to_df

def calculate_financial_health_score(user, expenses, budgets, goals, current_date=None):
    """
    Calculates a student financial health score out of 100.
    Considers:
    - Budget Control (25 points)
    - Saving Behavior (25 points)
    - Spending Stability / Consistency (20 points)
    - Expense Management (15 points)
    - Goal Progress (15 points)
    Returns a dict with score, category ratings, breakdown, and text explanation.
    """
    if not current_date:
        current_date = datetime.now().date()

    df = expenses_to_df(expenses)
    
    # Initialize defaults
    budget_score = 15.0
    saving_score = 15.0
    stability_score = 15.0
    mgmt_score = 10.0
    goal_score = 5.0
    
    curr_month = current_date.month
    curr_year = current_date.year
    
    # Calculate previous month date
    last_month_date = current_date.replace(day=1) - timedelta(days=1)
    prev_month = last_month_date.month
    prev_year = last_month_date.year

    df_curr = df[(df['expense_date'].dt.month == curr_month) & (df['expense_date'].dt.year == curr_year)] if not df.empty else pd.DataFrame()
    df_prev = df[(df['expense_date'].dt.month == prev_month) & (df['expense_date'].dt.year == prev_year)] if not df.empty else pd.DataFrame()

    curr_total = float(df_curr['amount'].sum()) if not df_curr.empty else 0.0
    prev_total = float(df_prev['amount'].sum()) if not df_prev.empty else 0.0

    # Get overall budget for current month
    overall_budget = None
    for b in budgets:
        if b.month == curr_month and b.year == curr_year and b.category is None:
            overall_budget = b.amount
            break

    # 1. Budget Control (25 points)
    if overall_budget:
        if curr_total <= 0.8 * overall_budget:
            budget_score = 25.0
        elif curr_total <= overall_budget:
            # Linear decrease from 25 to 10
            diff = curr_total - (0.8 * overall_budget)
            span = 0.2 * overall_budget
            budget_score = 25.0 - (diff / span) * 15.0
        else:
            # Over budget
            over_pct = (curr_total - overall_budget) / overall_budget
            budget_score = max(0.0, 10.0 - over_pct * 20.0)
    else:
        # Default if no budget is configured
        budget_score = 15.0

    # 2. Saving Behavior (25 points)
    allowance = user.monthly_income_or_allowance or 0.0
    if allowance > 0:
        savings = allowance - curr_total
        saving_rate = savings / allowance
        if saving_rate >= 0.3:
            saving_score = 25.0
        elif saving_rate >= 0.0:
            # Scale from 0 to 25
            saving_score = (saving_rate / 0.3) * 25.0
        else:
            # Negative savings
            saving_score = 0.0
    else:
        saving_score = 12.0 # Default if no income info

    # 3. Spending Stability / Consistency (20 points)
    if prev_total > 0:
        pct_growth = ((curr_total - prev_total) / prev_total) * 100
        if pct_growth <= 10:
            stability_score = 20.0
        else:
            # Decreases if growth is high
            stability_score = max(0.0, 20.0 - (pct_growth - 10) * 0.5)
    else:
        stability_score = 15.0

    # 4. Expense Management - Essential vs Non-essential (15 points)
    if not df_curr.empty:
        non_essential = float(df_curr[df_curr['is_essential'] == False]['amount'].sum())
        if curr_total > 0:
            non_essential_pct = (non_essential / curr_total) * 100
            if non_essential_pct <= 30:
                mgmt_score = 15.0
            elif non_essential_pct <= 60:
                mgmt_score = 15.0 - ((non_essential_pct - 30) / 30.0) * 10.0
            else:
                mgmt_score = max(0.0, 5.0 - ((non_essential_pct - 60) / 40.0) * 5.0)
        else:
            mgmt_score = 15.0
    else:
        mgmt_score = 12.0

    # 5. Goal Progress (15 points)
    active_goals = [g for g in goals if g.status == 'active']
    if active_goals:
        progresses = []
        for g in active_goals:
            p = g.current_amount / g.target_amount if g.target_amount > 0 else 0
            progresses.append(min(1.0, p))
        avg_p = sum(progresses) / len(progresses)
        goal_score = avg_p * 15.0
    else:
        goal_score = 8.0 # Default points for having no active goal debt

    total_score = round(budget_score + saving_score + stability_score + mgmt_score + goal_score)
    total_score = min(100, max(0, total_score))

    # Rating class and explanation
    if total_score >= 85:
        rating = "Excellent"
        explanation = "Outstanding job! You are maintaining high savings, staying well within your budget, and making great progress on your goals."
    elif total_score >= 70:
        rating = "Good"
        explanation = "You have healthy financial habits. You are keeping spending in check, though minor adjustments to non-essential shopping can boost your savings."
    elif total_score >= 50:
        rating = "Moderate"
        explanation = "Your finances are average. You are close to exceeding budgets or saving less than 15% of your allowance. Review your dining out and entertainment expenses."
    else:
        rating = "Needs Attention"
        explanation = "Your spending is high relative to your budget or allowance. It is highly recommended to set a strict weekly pocket limit and reduce credit/UPI payments."

    return {
        "score": total_score,
        "rating": rating,
        "explanation": explanation,
        "breakdown": {
            "budget_control": round(budget_score, 1),
            "saving_behavior": round(saving_score, 1),
            "spending_stability": round(stability_score, 1),
            "expense_management": round(mgmt_score, 1),
            "goal_progress": round(goal_score, 1)
        }
    }
