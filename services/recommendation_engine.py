from datetime import datetime, timedelta
import pandas as pd
from ml.preprocessing import expenses_to_df

def generate_recommendations(user, expenses, budgets, goals, current_date=None):
    """
    Analyzes user financial data and generates student-focused recommendations.
    Ensures no professional investment/crypto advice is given.
    """
    if not current_date:
        current_date = datetime.now().date()

    recommendations = []
    
    df = expenses_to_df(expenses)
    if df.empty:
        return [
            {
                "title": "Welcome to your Expense Portal!",
                "content": "Start tracking your daily expenses to receive personalized savings recommendations and financial health insights.",
                "type": "info"
            }
        ]

    # Current month and last month filters
    curr_month = current_date.month
    curr_year = current_date.year
    
    # Calculate previous month info
    last_month_date = current_date.replace(day=1) - timedelta(days=1)
    prev_month = last_month_date.month
    prev_year = last_month_date.year

    df_curr = df[(df['expense_date'].dt.month == curr_month) & (df['expense_date'].dt.year == curr_year)]
    df_prev = df[(df['expense_date'].dt.month == prev_month) & (df['expense_date'].dt.year == prev_year)]

    curr_total = float(df_curr['amount'].sum()) if not df_curr.empty else 0.0
    prev_total = float(df_prev['amount'].sum()) if not df_prev.empty else 0.0

    # Get overall budget for current month
    overall_budget = None
    for b in budgets:
        if b.month == curr_month and b.year == curr_year and b.category is None:
            overall_budget = b.amount
            break

    # Recommendation 1: Budget Utilization status
    if overall_budget:
        utilization = (curr_total / overall_budget) * 100
        if utilization >= 100:
            recommendations.append({
                "title": "Monthly Budget Exceeded",
                "content": f"You have spent ₹{curr_total:.2f}, exceeding your monthly budget of ₹{overall_budget:.2f} by ₹{curr_total - overall_budget:.2f}. Try to cut down on non-essential spending.",
                "type": "danger"
            })
        elif utilization >= 80:
            recommendations.append({
                "title": "Approaching Budget Limit",
                "content": f"You have used {utilization:.1f}% of your ₹{overall_budget:.2f} budget. You only have ₹{overall_budget - curr_total:.2f} remaining for this month.",
                "type": "warning"
            })
        elif utilization < 50 and current_date.day > 15:
            recommendations.append({
                "title": "Budget Surplus Opportunity",
                "content": f"Good job! You are past the 15th of the month and have used only {utilization:.1f}% of your budget. Consider allocating some of the remaining ₹{overall_budget - curr_total:.2f} to your active savings goals.",
                "type": "success"
            })

    # Recommendation 2: Category level spending changes
    categories_to_check = ["Food", "Shopping", "Transport", "Entertainment"]
    for cat in categories_to_check:
        curr_cat_total = float(df_curr[df_curr['category'] == cat]['amount'].sum()) if not df_curr.empty else 0.0
        prev_cat_total = float(df_prev[df_prev['category'] == cat]['amount'].sum()) if not df_prev.empty else 0.0
        
        if prev_cat_total > 0:
            pct_change = ((curr_cat_total - prev_cat_total) / prev_cat_total) * 100
            if pct_change >= 20 and (curr_cat_total - prev_cat_total) > 150:
                recommendations.append({
                    "title": f"Surge in {cat} Spending",
                    "content": f"Your {cat} spending increased by {pct_change:.1f}% compared to last month (₹{curr_cat_total:.0f} vs ₹{prev_cat_total:.0f}). Consider setting a weekly limit for {cat}.",
                    "type": "warning"
                })
            elif pct_change <= -20 and (prev_cat_total - curr_cat_total) > 150:
                recommendations.append({
                    "title": f"Great Savings on {cat}",
                    "content": f"Awesome work! You spent {abs(pct_change):.1f}% less on {cat} this month compared to last month.",
                    "type": "success"
                })

    # Recommendation 3: Essential vs Non-essential spending
    if not df_curr.empty:
        essential_total = float(df_curr[df_curr['is_essential'] == True]['amount'].sum())
        non_essential_total = float(df_curr[df_curr['is_essential'] == False]['amount'].sum())
        
        if curr_total > 0:
            non_essential_ratio = (non_essential_total / curr_total) * 100
            if non_essential_ratio > 40:
                recommendations.append({
                    "title": "High Non-Essential Spending",
                    "content": f"Non-essential items (Shopping, Entertainment, Travel, etc.) make up {non_essential_ratio:.1f}% of this month's spending. Trimming these could boost your savings.",
                    "type": "warning"
                })

    # Recommendation 4: Goals suggestion
    for g in goals:
        if g.status == 'active':
            remaining_needed = g.target_amount - g.current_amount
            if remaining_needed > 0:
                days_left = (g.deadline - current_date).days
                months_left = days_left / 30.4
                if months_left > 0:
                    suggested_monthly = remaining_needed / months_left
                    recommendations.append({
                        "title": f"Goal Track: {g.title}",
                        "content": f"To reach your goal of ₹{g.target_amount} by {g.deadline.strftime('%B %Y')}, you need to save approximately ₹{suggested_monthly:.2f} per month.",
                        "type": "info"
                    })

    # Add a general student tip if list is short
    if len(recommendations) < 3:
        recommendations.append({
            "title": "Student Savings Tip",
            "content": "Always ask for student discounts when buying textbooks, software, transit passes, or electronics. Small savings add up over time!",
            "type": "info"
        })

    return recommendations
