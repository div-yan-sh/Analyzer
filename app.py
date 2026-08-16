import os
from flask import Flask, render_template, redirect, url_for, session
from flask_cors import CORS
from config import Config
from database.db import db
from database.models import User

# Route blueprints imports
from routes.auth_routes import auth_bp
from routes.expense_routes import expense_bp
from routes.budget_routes import budget_bp
from routes.goal_routes import goal_bp
from routes.analytics_routes import analytics_bp
from routes.ai_routes import ai_bp
from routes.split_routes import split_bp
from routes.subscription_routes import subscription_bp

from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for local cross-origin testing if needed
CORS(app)

# Initialize database
db.init_app(app)

# Register backend API blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(expense_bp)
app.register_blueprint(budget_bp)
app.register_blueprint(goal_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(split_bp)
app.register_blueprint(subscription_bp)

# View decorator to protect frontend routes
def view_login_required(f):
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_view

# ----------------- Front-end View Routes -----------------

@app.route('/')
def landing_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    return render_template('landing.html')

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    return render_template('login.html')

@app.route('/register')
def register_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    return render_template('register.html')

@app.route('/dashboard')
@view_login_required
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/expenses')
@view_login_required
def expenses_page():
    return render_template('expenses.html')

@app.route('/scanner')
@view_login_required
def scanner_page():
    return render_template('scanner.html')

@app.route('/split')
@view_login_required
def split_page():
    return render_template('split.html')

@app.route('/subscriptions')
@view_login_required
def subscriptions_page():
    return render_template('subscriptions.html')

@app.route('/analytics')
@view_login_required
def analytics_page():
    return render_template('analytics.html')

@app.route('/budget')
@view_login_required
def budget_page():
    return render_template('budget.html')

@app.route('/goals')
@view_login_required
def goals_page():
    return render_template('goals.html')

@app.route('/insights')
@view_login_required
def insights_page():
    return render_template('insights.html')

@app.route('/ai-assistant')
@view_login_required
def ai_assistant_page():
    return render_template('ai_assistant.html')

@app.route('/profile')
@view_login_required
def profile_page():
    return render_template('profile.html')

# In-app context processor to inject current logged in user to all templates
@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return dict(current_user=user)
    return dict(current_user=None)

# Initialize database schema inside the app context
with app.app_context():
    try:
        db.create_all()
        # Safe migration for existing SQLite databases
        with db.engine.connect() as conn:
            # Check users table columns
            cursor = conn.connection.cursor()
            cursor.execute("PRAGMA table_info(users)")
            user_cols = [row[1] for row in cursor.fetchall()]
            
            if 'google_id' not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN google_id VARCHAR(100)")
            if 'avatar_url' not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)")
                
            cursor.execute("PRAGMA table_info(expenses)")
            exp_cols = [row[1] for row in cursor.fetchall()]
            if 'receipt_url' not in exp_cols:
                cursor.execute("ALTER TABLE expenses ADD COLUMN receipt_url VARCHAR(500)")
                
            conn.connection.commit()
        print("Database schema and migrations verified.")
    except Exception as e:
        print(f"Error during schema creation: {e}")

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)

