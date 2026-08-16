import pandas as pd
import numpy as np
from ml.preprocessing import expenses_to_df

def check_single_expense_anomaly(amount, category, historical_expenses, threshold_z=2.5):
    """
    Checks if a single expense amount is anomalous within its category.
    Uses Z-score if we have >= 5 historical records, otherwise uses 3x multiplier.
    Returns: (is_anomaly, z_score, reason)
    """
    if not historical_expenses:
        return False, 0.0, "Insufficient history."
        
    df = expenses_to_df(historical_expenses)
    df_cat = df[df['category'] == category]
    
    if len(df_cat) < 5:
        # Fallback for small sample sizes
        mean_val = float(df_cat['amount'].mean()) if not df_cat.empty else 0.0
        if mean_val > 0 and amount > 3.0 * mean_val:
            return True, 3.0, f"Unusual spend: This amount (₹{amount}) is over 3x higher than your typical {category} expense of ₹{round(mean_val, 2)}."
        return False, 0.0, "Insufficient history for reliable detection."

    mean_val = float(df_cat['amount'].mean())
    std_val = float(df_cat['amount'].std())

    if std_val == 0:
        # If std is 0, standard deviation is not defined/helpful
        if amount > 2.0 * mean_val:
            return True, 2.0, f"Unusual spend: Amount is 2x higher than your constant historical spend of ₹{round(mean_val, 2)}."
        return False, 0.0, "Typical spending pattern."

    z_score = (amount - mean_val) / std_val

    if z_score > threshold_z:
        reason = (
            f"Unusual spend: This {category} expense of ₹{amount} is significantly higher than your "
            f"typical average of ₹{round(mean_val, 2)} (Z-score: {round(z_score, 2)})."
        )
        return True, z_score, reason
        
    return False, z_score, "Typical spending pattern."

def scan_all_anomalies(expenses, threshold_z=2.5):
    """
    Scans a list of expenses and returns a list of dicts for all flagged anomalies.
    """
    anomalies = []
    df = expenses_to_df(expenses)
    if df.empty:
        return anomalies
        
    categories = df['category'].unique()
    
    for cat in categories:
        df_cat = df[df['category'] == cat]
        if len(df_cat) < 5:
            # Check using simple multiplier fallback
            mean_val = df_cat['amount'].mean()
            for idx, row in df_cat.iterrows():
                if mean_val > 0 and row['amount'] > 3.0 * mean_val:
                    anomalies.append({
                        "id": int(row['id']),
                        "amount": float(row['amount']),
                        "category": str(row['category']),
                        "description": str(row['description']),
                        "expense_date": row['expense_date'].strftime('%Y-%m-%d'),
                        "reason": f"This amount (₹{row['amount']}) is over 3 times your category average of ₹{round(mean_val, 2)}."
                    })
            continue

        mean_val = df_cat['amount'].mean()
        std_val = df_cat['amount'].std()
        
        if std_val == 0:
            continue
            
        for idx, row in df_cat.iterrows():
            z = (row['amount'] - mean_val) / std_val
            if z > threshold_z:
                anomalies.append({
                    "id": int(row['id']),
                    "amount": float(row['amount']),
                    "category": str(row['category']),
                    "description": str(row['description']),
                    "expense_date": row['expense_date'].strftime('%Y-%m-%d'),
                    "reason": f"This amount (₹{row['amount']}) is significantly above your {cat} average of ₹{round(mean_val, 2)} (Z-score: {round(z, 2)})."
                })
                
    return sorted(anomalies, key=lambda x: x['expense_date'], reverse=True)
