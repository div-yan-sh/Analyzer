import pandas as pd
import numpy as np
from datetime import datetime, date
import calendar
from sklearn.linear_model import LinearRegression
from ml.preprocessing import expenses_to_df

def get_days_in_month(year, month):
    return calendar.monthrange(year, month)[1]

def predict_current_month_end(expenses, budget_amount, current_date=None):
    """
    Predicts the total spending at the end of the current month.
    Uses linear regression on cumulative daily spending if we have >= 3 days of data.
    Otherwise, uses simple daily rate extrapolation.
    """
    if not current_date:
        current_date = datetime.now().date()
        
    df = expenses_to_df(expenses)
    if df.empty:
        return 0.0, 0.0, "No transactions recorded yet."

    # Filter for the current month
    df_current = df[(df['expense_date'].dt.year == current_date.year) & 
                    (df['expense_date'].dt.month == current_date.month)]
    
    current_spent = float(df_current['amount'].sum()) if not df_current.empty else 0.0
    days_in_month = get_days_in_month(current_date.year, current_date.month)
    current_day = current_date.day

    if df_current.empty or current_day < 3:
        # Fallback to simple average daily rate if it's the beginning of the month
        # or no data exists yet.
        daily_rate = current_spent / max(1, current_day)
        predicted_end = daily_rate * days_in_month
        return round(predicted_end, 2), round(current_spent, 2), "Prediction based on simple daily rate extrapolation."

    # Fit a linear regression on cumulative daily spending
    # Create daily series from day 1 to current_day
    daily_spend = df_current.groupby(df_current['expense_date'].dt.day)['amount'].sum()
    all_days = pd.Series(0.0, index=range(1, current_day + 1))
    all_days.update(daily_spend)
    
    cumulative_spend = all_days.cumsum()
    
    X = np.array(cumulative_spend.index).reshape(-1, 1)
    y = cumulative_spend.values
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict for the last day of the month
    predicted_end = float(model.predict(np.array([[days_in_month]]))[0])
    
    # Cap prediction to prevent negative projections
    predicted_end = max(current_spent, predicted_end)
    
    return round(predicted_end, 2), round(current_spent, 2), "Prediction based on cumulative linear regression trend."

def predict_next_month(expenses):
    """
    Predicts next month's total spending based on historical monthly totals.
    Uses linear regression if >= 3 months of data exist, otherwise returns average.
    """
    df = expenses_to_df(expenses)
    if df.empty:
        return 0.0, "No historical data."

    # Group by year-month
    df['year_month'] = df['expense_date'].dt.to_period('M')
    monthly_totals = df.groupby('year_month')['amount'].sum().sort_index()

    if len(monthly_totals) < 3:
        # Fallback to historical monthly average
        avg = float(monthly_totals.mean())
        return round(avg, 2), f"Based on average of last {len(monthly_totals)} month(s)."

    # Fit linear regression
    X = np.arange(len(monthly_totals)).reshape(-1, 1)
    y = monthly_totals.values

    model = LinearRegression()
    model.fit(X, y)

    next_idx = len(monthly_totals)
    predicted_val = float(model.predict(np.array([[next_idx]]))[0])
    predicted_val = max(0.0, predicted_val)

    return round(predicted_val, 2), "Based on linear regression of monthly spending trends."

def predict_category_spending(expenses):
    """
    Predicts next month's spending for each category.
    """
    df = expenses_to_df(expenses)
    predictions = {}
    
    if df.empty:
        return predictions

    categories = df['category'].unique()
    df['year_month'] = df['expense_date'].dt.to_period('M')

    for cat in categories:
        df_cat = df[df['category'] == cat]
        monthly_cat = df_cat.groupby('year_month')['amount'].sum().sort_index()
        
        if len(monthly_cat) < 3:
            predictions[cat] = round(float(monthly_cat.mean()), 2)
        else:
            X = np.arange(len(monthly_cat)).reshape(-1, 1)
            y = monthly_cat.values
            model = LinearRegression()
            model.fit(X, y)
            next_idx = len(monthly_cat)
            pred = float(model.predict(np.array([[next_idx]]))[0])
            predictions[cat] = round(max(0.0, pred), 2)
            
    return predictions
