import sys
import os
from datetime import datetime, timedelta
import random

# Add root folder to python path so database imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from config import Config
from database.db import db
from database.models import User, Expense, Budget, FinancialGoal, AIInsight

def seed_database():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        # Drop all tables and recreate
        db.drop_all()
        db.create_all()

        print("Created database tables successfully.")

        # Create demo user
        user = User(
            name="Divya",
            email="demo@student.edu",
            college="National Institute of Technology",
            course="Computer Science & Engineering",
            year=3,
            monthly_income_or_allowance=15000.0
        )
        user.set_password("student123")
        db.session.add(user)
        db.session.commit()
        print(f"Created demo user: {user.email}")

        # Seed budgets for last 6 months and current month
        # Current date is 2026-08-14
        today = datetime.now().date()
        months = []
        for i in range(7):
            d = today - timedelta(days=i*30)
            months.append((d.month, d.year))

        # Distinct list of (month, year) pairs
        months = list(set(months))

        for m, y in months:
            # Overall budget
            b_overall = Budget(user_id=user.id, month=m, year=y, amount=12000.0, category=None)
            db.session.add(b_overall)
            
            # Category specific budgets
            b_food = Budget(user_id=user.id, month=m, year=y, amount=4000.0, category="Food")
            b_transport = Budget(user_id=user.id, month=m, year=y, amount=1500.0, category="Transport")
            b_shopping = Budget(user_id=user.id, month=m, year=y, amount=2000.0, category="Shopping")
            db.session.add_all([b_food, b_transport, b_shopping])

        # Seed Financial Goals
        g1 = FinancialGoal(
            user_id=user.id,
            title="New Coding Laptop",
            target_amount=60000.0,
            current_amount=18000.0,
            deadline=datetime(2027, 6, 30).date(),
            description="High-performance laptop for machine learning projects",
            status="active"
        )
        g2 = FinancialGoal(
            user_id=user.id,
            title="Summer Internship Trip",
            target_amount=10000.0,
            current_amount=6000.0,
            deadline=datetime(2027, 5, 15).date(),
            description="Travel expenses for internship in Bangalore",
            status="active"
        )
        db.session.add_all([g1, g2])
        db.session.commit()
        print("Created budgets and goals.")

        # Seed Expenses (6 months history starting from Feb 1, 2026)
        start_date = datetime(2026, 2, 1).date()
        end_date = today

        current_date = start_date
        expenses_to_add = []

        while current_date <= end_date:
            # Round amounts to keep it looking neat
            def neat_amount(low, high):
                return round(random.uniform(low, high) / 5) * 5

            # 1. Hostel/Rent on 1st of every month
            if current_date.day == 1:
                expenses_to_add.append(Expense(
                    user_id=user.id,
                    amount=4500.0,
                    category="Hostel/Rent",
                    subcategory="Room Rent",
                    description="Monthly room rent payment",
                    payment_method="Bank Transfer",
                    expense_date=current_date,
                    is_essential=True
                ))

            # 2. Monthly mobile recharge on 5th of every month
            if current_date.day == 5:
                expenses_to_add.append(Expense(
                    user_id=user.id,
                    amount=299.0,
                    category="Recharge",
                    subcategory="Mobile",
                    description="Jio 1.5GB/day recharge plan",
                    payment_method="UPI",
                    expense_date=current_date,
                    is_essential=True
                ))

            # 3. Monthly internet bill on 8th of every month
            if current_date.day == 8:
                expenses_to_add.append(Expense(
                    user_id=user.id,
                    amount=599.0,
                    category="Bills",
                    subcategory="Internet",
                    description="Wi-Fi broadband bill",
                    payment_method="Debit Card",
                    expense_date=current_date,
                    is_essential=True
                ))

            # 4. Weekly Transport (Monday & Friday)
            if current_date.weekday() in [0, 4]:  # Monday, Friday
                expenses_to_add.append(Expense(
                    user_id=user.id,
                    amount=float(random.choice([40, 50, 80, 100])),
                    category="Transport",
                    subcategory="Metro/Auto",
                    description=random.choice(["Metro smartcard auto-topup", "Auto rickshaw fare to college"]),
                    payment_method="UPI" if random.random() > 0.3 else "Cash",
                    expense_date=current_date,
                    is_essential=True
                ))

            # 5. Daily Canteen/Mess expenses (Food)
            # 1-2 transactions per day
            num_food_tx = random.choice([1, 2])
            for _ in range(num_food_tx):
                expenses_to_add.append(Expense(
                    user_id=user.id,
                    amount=float(neat_amount(50, 200)),
                    category="Food",
                    subcategory="College Canteen" if random.random() > 0.4 else "Tea/Coffee",
                    description=random.choice(["Lunch at canteen", "Evening tea and snacks", "Breakfast samosa & juice", "Mess bill extras"]),
                    payment_method=random.choice(["UPI", "Cash"]),
                    expense_date=current_date,
                    is_essential=True
                ))

            # 6. Occasional shopping on weekends (Saturday / Sunday)
            if current_date.weekday() in [5, 6] and random.random() < 0.25:
                expenses_to_add.append(Expense(
                    user_id=user.id,
                    amount=float(neat_amount(200, 1500)),
                    category="Shopping",
                    subcategory="Clothing" if random.random() > 0.5 else "Stationery",
                    description=random.choice(["T-shirt from mall", "Notebooks and pens", "Running shoes", "Lab record files"]),
                    payment_method=random.choice(["UPI", "Debit Card", "Credit Card"]),
                    expense_date=current_date,
                    is_essential=False
                ))

            # 7. Entertainment (movies, dining out)
            if current_date.weekday() in [4, 5] and random.random() < 0.15:
                expenses_to_add.append(Expense(
                    user_id=user.id,
                    amount=float(neat_amount(150, 750)),
                    category="Entertainment",
                    subcategory="Movie" if random.random() > 0.5 else "Dining Out",
                    description=random.choice(["Movie ticket and popcorn", "Dinner at cafe with friends", "Netflix subscription sharing"]),
                    payment_method="UPI",
                    expense_date=current_date,
                    is_essential=False
                ))

            # 8. Education expenses (books, online courses) - once a month around 15th
            if current_date.day == 15 and random.random() < 0.7:
                expenses_to_add.append(Expense(
                    user_id=user.id,
                    amount=float(neat_amount(300, 2000)),
                    category="Education",
                    subcategory="Books" if random.random() > 0.5 else "Online Course",
                    description=random.choice(["Python coding reference book", "Udemy web dev course", "Engineering math textbook"]),
                    payment_method="UPI" if random.random() > 0.3 else "Debit Card",
                    expense_date=current_date,
                    is_essential=True
                ))

            current_date += timedelta(days=1)

        # 9. Add intentional anomalies to show off anomaly detection
        # Food anomaly: birthday restaurant treat
        food_anomaly_date = today - timedelta(days=4)
        expenses_to_add.append(Expense(
            user_id=user.id,
            amount=2450.0,
            category="Food",
            subcategory="Dining Out",
            description="Birthday treat to friends at Bistro Cafe (Unusual high food spend)",
            payment_method="UPI",
            expense_date=food_anomaly_date,
            is_essential=False
        ))

        # Shopping anomaly: buying a printer/tablet
        shopping_anomaly_date = today - timedelta(days=12)
        expenses_to_add.append(Expense(
            user_id=user.id,
            amount=5600.0,
            category="Shopping",
            subcategory="Electronics",
            description="Bought laser printer for study notes (Unusual electronics shopping)",
            payment_method="Credit Card",
            expense_date=shopping_anomaly_date,
            is_essential=True
        ))

        # Travel anomaly: weekend trip to hill station
        travel_anomaly_date = today - timedelta(days=25)
        expenses_to_add.append(Expense(
            user_id=user.id,
            amount=4200.0,
            category="Travel",
            subcategory="Outstation",
            description="Weekend trip to Lonavala (Bus tickets & hotel share)",
            payment_method="Debit Card",
            expense_date=travel_anomaly_date,
            is_essential=False
        ))

        db.session.add_all(expenses_to_add)
        db.session.commit()
        print(f"Added {len(expenses_to_add)} student expenses.")

        # Let's seed some sample AI Insights
        i1 = AIInsight(
            user_id=user.id,
            title="High Food Spending Warning",
            content=f"Your food expenses surged by 24% on {food_anomaly_date.strftime('%B %d')}. This was driven by a single large transaction of ₹2,450 at Bistro Cafe. Consider sticking to college canteen for remainder of the month to balance your budget.",
            insight_type="anomaly"
        )
        i2 = AIInsight(
            user_id=user.id,
            title="Saving Goal Progress Status",
            content="Great job! You have accumulated ₹18,000 (30%) of your ₹60,000 'New Coding Laptop' savings target. Staying under budget this month could accelerate your progress by 5 days.",
            insight_type="recommendation"
        )
        db.session.add_all([i1, i2])
        db.session.commit()
        print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
