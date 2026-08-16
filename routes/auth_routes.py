import os
import secrets
import requests
from flask import Blueprint, request, jsonify, session, redirect, url_for, current_app
from database.db import db
from database.models import User, Expense, Budget, FinancialGoal, AIInsight, Subscription, GroupSplit, ReceiptScan
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized. Please log in."}), 401
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    college = data.get('college', '')
    course = data.get('course', '')
    year = data.get('year')
    allowance = data.get('monthly_income_or_allowance', 0.0)

    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required."}), 400

    # Clean email
    email = email.strip().lower()

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User with this email already exists."}), 400

    try:
        user = User(
            name=name,
            email=email,
            college=college,
            course=course,
            year=int(year) if year else 1,
            monthly_income_or_allowance=float(allowance) if allowance else 0.0
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Log the user in automatically
        session['user_id'] = user.id
        return jsonify({"message": "Registration successful.", "user": user.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create user: {str(e)}"}), 500

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    remember = data.get('remember', False)

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    email = email.strip().lower()
    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password."}), 401

    session['user_id'] = user.id
    if remember:
        session.permanent = True
    else:
        session.permanent = False

    return jsonify({"message": "Login successful.", "user": user.to_dict()}), 200

@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('oauth_state', None)
    return jsonify({"message": "Logged out successfully."}), 200

# ----------------- Google OAuth 2.0 Endpoints -----------------

@auth_bp.route('/api/auth/google/status', methods=['GET'])
def google_auth_status():
    """Returns whether real Google OAuth client credentials are configured."""
    client_id = current_app.config.get('GOOGLE_CLIENT_ID', '')
    is_configured = bool(client_id and not client_id.startswith('YOUR_'))
    return jsonify({"configured": is_configured, "client_id": client_id if is_configured else None})

@auth_bp.route('/api/auth/google/login')
def google_login():
    """
    Redirects user to Google OAuth 2.0 consent page.
    If Google credentials are not configured, redirects to demo Google authentication.
    """
    client_id = current_app.config.get('GOOGLE_CLIENT_ID', '')
    redirect_uri = current_app.config.get('GOOGLE_REDIRECT_URI', 'http://127.0.0.1:5000/api/auth/google/callback')

    if not client_id or client_id.startswith('YOUR_'):
        # Fallback to demo login if Google credentials haven't been provided yet
        return redirect(url_for('auth.google_demo_login'))

    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state

    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        "response_type=code&"
        "scope=openid%20email%20profile&"
        f"state={state}&"
        "access_type=offline&"
        "prompt=select_account"
    )
    return redirect(google_auth_url)

@auth_bp.route('/api/auth/google/callback')
def google_callback():
    """
    Handles Google OAuth 2.0 code exchange, fetches user profile,
    and logs user into SpendIntel.
    """
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')

    if error:
        return redirect(url_for('login_page') + f'?error=Google+login+cancelled:+{error}')

    if not code:
        return redirect(url_for('login_page') + '?error=Invalid+Google+authorization+code')

    client_id = current_app.config.get('GOOGLE_CLIENT_ID', '')
    client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET', '')
    redirect_uri = current_app.config.get('GOOGLE_REDIRECT_URI', 'http://127.0.0.1:5000/api/auth/google/callback')

    try:
        # Exchange code for tokens
        token_res = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri
            },
            timeout=10
        )
        token_data = token_res.json()
        access_token = token_data.get('access_token')

        if not access_token:
            return redirect(url_for('login_page') + '?error=Failed+to+obtain+Google+access+token')

        # Fetch Google user profile
        userinfo_res = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        user_info = userinfo_res.json()

        google_id = user_info.get('sub')
        email = user_info.get('email', '').strip().lower()
        name = user_info.get('name') or user_info.get('given_name') or 'Google Student'
        picture = user_info.get('picture')

        if not email:
            return redirect(url_for('login_page') + '?error=Google+account+missing+email')

        # Find or create user
        user = User.query.filter((User.google_id == google_id) | (User.email == email)).first()
        if user:
            # Update user with Google info
            user.google_id = google_id
            if picture:
                user.avatar_url = picture
            if not user.name:
                user.name = name
        else:
            # Create new user
            user = User(
                name=name,
                email=email,
                google_id=google_id,
                avatar_url=picture,
                college='University / College',
                course='Student',
                year=1,
                monthly_income_or_allowance=15000.0
            )
            db.session.add(user)

        db.session.commit()

        # Set session
        session['user_id'] = user.id
        return redirect(url_for('dashboard_page'))

    except Exception as e:
        db.session.rollback()
        return redirect(url_for('login_page') + f'?error=OAuth+error:+{str(e)}')

@auth_bp.route('/api/auth/google/demo')
def google_demo_login():
    """
    Instant 1-click Google Sign-In demonstration user.
    Enables testing Google auth flow when real Client IDs are not yet registered.
    """
    demo_email = "alex.chen.student@gmail.com"
    demo_google_id = "google_demo_10829371029381029"
    demo_avatar = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80"
    
    user = User.query.filter_by(email=demo_email).first()
    if not user:
        user = User(
            name="Alex Chen (Google User)",
            email=demo_email,
            google_id=demo_google_id,
            avatar_url=demo_avatar,
            college="MIT / State Tech University",
            course="Computer Science",
            year=2,
            monthly_income_or_allowance=18000.0
        )
        db.session.add(user)
        db.session.commit()
    else:
        user.avatar_url = demo_avatar
        user.google_id = demo_google_id
        db.session.commit()

    session['user_id'] = user.id
    return redirect(url_for('dashboard_page'))

# ----------------- User Profile & Data -----------------

@auth_bp.route('/api/user/profile', methods=['GET', 'PUT'])
@login_required
def profile():
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "User not found."}), 404

    if request.method == 'GET':
        return jsonify(user.to_dict()), 200

    if request.method == 'PUT':
        data = request.get_json() or {}
        
        user.name = data.get('name', user.name)
        user.college = data.get('college', user.college)
        user.course = data.get('course', user.course)
        user.avatar_url = data.get('avatar_url', user.avatar_url)
        
        if 'year' in data:
            user.year = int(data['year']) if data['year'] else user.year
            
        if 'monthly_income_or_allowance' in data:
            user.monthly_income_or_allowance = float(data['monthly_income_or_allowance']) if data['monthly_income_or_allowance'] is not None else user.monthly_income_or_allowance

        new_password = data.get('password')
        if new_password:
            user.set_password(new_password)

        try:
            db.session.commit()
            return jsonify({"message": "Profile updated successfully.", "user": user.to_dict()}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to update profile: {str(e)}"}), 500

@auth_bp.route('/api/user/reset', methods=['POST'])
@login_required
def reset_data():
    user_id = session['user_id']
    try:
        Expense.query.filter_by(user_id=user_id).delete()
        Budget.query.filter_by(user_id=user_id).delete()
        FinancialGoal.query.filter_by(user_id=user_id).delete()
        AIInsight.query.filter_by(user_id=user_id).delete()
        Subscription.query.filter_by(user_id=user_id).delete()
        GroupSplit.query.filter_by(user_id=user_id).delete()
        ReceiptScan.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return jsonify({"message": "All user data reset successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to reset data: {str(e)}"}), 500
