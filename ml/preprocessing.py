import pandas as pd
import numpy as np

def expenses_to_df(expenses):
    """
    Converts a list of Expense SQLAlchemy objects into a pandas DataFrame.
    """
    if not expenses:
        return pd.DataFrame(columns=[
            'id', 'user_id', 'amount', 'category', 'subcategory', 
            'description', 'payment_method', 'expense_date', 'is_essential'
        ])
    
    data = []
    for exp in expenses:
        data.append({
            'id': exp.id,
            'user_id': exp.user_id,
            'amount': exp.amount,
            'category': exp.category,
            'subcategory': exp.subcategory,
            'description': exp.description,
            'payment_method': exp.payment_method,
            'expense_date': exp.expense_date,  # Date object
            'is_essential': exp.is_essential
        })
    df = pd.DataFrame(data)
    df['expense_date'] = pd.to_datetime(df['expense_date'])
    return df

def add_date_features(df):
    """
    Adds custom date components to the DataFrame for analysis/ML.
    """
    if df.empty:
        return df
    df = df.copy()
    df['year'] = df['expense_date'].dt.year
    df['month'] = df['expense_date'].dt.month
    df['day'] = df['expense_date'].dt.day
    df['dayofweek'] = df['expense_date'].dt.dayofweek
    df['is_weekend'] = df['dayofweek'].isin([5, 6]).astype(int)
    return df

def aggregate_by_category(df):
    """
    Groups expenses by category. Returns a dict.
    """
    if df.empty:
        return {}
    grouped = df.groupby('category')['amount'].sum().to_dict()
    return {k: round(v, 2) for k, v in grouped.items()}

def aggregate_by_date(df):
    """
    Groups expenses by date. Returns a dictionary of date string to total amount.
    """
    if df.empty:
        return {}
    df_sorted = df.sort_values('expense_date')
    grouped = df_sorted.groupby(df_sorted['expense_date'].dt.strftime('%Y-%m-%d'))['amount'].sum().to_dict()
    return grouped

def get_daily_average(df, days=30):
    """
    Calculates average daily spending over the last N days.
    """
    if df.empty:
        return 0.0
    daily_sums = df.groupby(df['expense_date'].dt.date)['amount'].sum()
    if daily_sums.empty:
        return 0.0
    return float(round(daily_sums.tail(days).mean(), 2))
