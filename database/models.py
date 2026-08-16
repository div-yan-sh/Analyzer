from datetime import datetime
from database.db import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True) # Nullable for OAuth users
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    college = db.Column(db.String(150))
    course = db.Column(db.String(100))
    year = db.Column(db.Integer)  # 1st year, 2nd year, etc.
    monthly_income_or_allowance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    expenses = db.relationship('Expense', backref='user', lazy=True, cascade="all, delete-orphan")
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade="all, delete-orphan")
    goals = db.relationship('FinancialGoal', backref='user', lazy=True, cascade="all, delete-orphan")
    insights = db.relationship('AIInsight', backref='user', lazy=True, cascade="all, delete-orphan")
    subscriptions = db.relationship('Subscription', backref='user', lazy=True, cascade="all, delete-orphan")
    splits = db.relationship('GroupSplit', backref='user', lazy=True, cascade="all, delete-orphan")
    receipts = db.relationship('ReceiptScan', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "google_id": self.google_id,
            "avatar_url": self.avatar_url,
            "college": self.college,
            "course": self.course,
            "year": self.year,
            "monthly_income_or_allowance": self.monthly_income_or_allowance,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    subcategory = db.Column(db.String(50))
    description = db.Column(db.String(200))
    payment_method = db.Column(db.String(50), nullable=False)  # Cash, UPI, Debit Card, etc.
    expense_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    is_essential = db.Column(db.Boolean, default=True)
    receipt_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "category": self.category,
            "subcategory": self.subcategory or "",
            "description": self.description or "",
            "payment_method": self.payment_method,
            "expense_date": self.expense_date.isoformat() if self.expense_date else None,
            "is_essential": self.is_essential,
            "receipt_url": self.receipt_url,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Budget(db.Model):
    __tablename__ = 'budgets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1 to 12
    year = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=True)  # Null means overall monthly budget

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "month": self.month,
            "year": self.year,
            "amount": self.amount,
            "category": self.category or "Overall"
        }

class FinancialGoal(db.Model):
    __tablename__ = 'financial_goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    deadline = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(250))
    status = db.Column(db.String(20), default='active')  # active, completed

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "target_amount": self.target_amount,
            "current_amount": self.current_amount,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "description": self.description or "",
            "status": self.status
        }

class AIInsight(db.Model):
    __tablename__ = 'ai_insights'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    insight_type = db.Column(db.String(50))  # anomaly, recommendation, prediction
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "content": self.content,
            "insight_type": self.insight_type,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False) # e.g. Netflix, Spotify, Gym, Mess Fee
    amount = db.Column(db.Float, nullable=False)
    billing_cycle = db.Column(db.String(20), default='monthly') # monthly, yearly, quarterly
    next_billing_date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50), default='Entertainment')
    payment_method = db.Column(db.String(50), default='UPI')
    status = db.Column(db.String(20), default='active') # active, paused, cancelled
    icon = db.Column(db.String(50), default='fa-solid fa-bell')
    notes = db.Column(db.String(250))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "amount": self.amount,
            "billing_cycle": self.billing_cycle,
            "next_billing_date": self.next_billing_date.isoformat() if self.next_billing_date else None,
            "category": self.category,
            "payment_method": self.payment_method,
            "status": self.status,
            "icon": self.icon,
            "notes": self.notes or "",
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class GroupSplit(db.Model):
    __tablename__ = 'group_splits'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False) # e.g. "Weekend Pizza Party", "Hostel Electricity Bill"
    total_amount = db.Column(db.Float, nullable=False)
    paid_by = db.Column(db.String(100), nullable=False) # e.g. "You" or roommate name
    upi_id = db.Column(db.String(100), nullable=True) # for one-click payment QR / deep-link
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    settled = db.Column(db.Boolean, default=False)

    members = db.relationship('SplitMember', backref='split', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "total_amount": self.total_amount,
            "paid_by": self.paid_by,
            "upi_id": self.upi_id or "",
            "settled": self.settled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "members": [m.to_dict() for m in self.members]
        }

class SplitMember(db.Model):
    __tablename__ = 'split_members'
    
    id = db.Column(db.Integer, primary_key=True)
    split_id = db.Column(db.Integer, db.ForeignKey('group_splits.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    share_amount = db.Column(db.Float, nullable=False)
    has_paid = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "split_id": self.split_id,
            "name": self.name,
            "share_amount": self.share_amount,
            "has_paid": self.has_paid
        }

class ReceiptScan(db.Model):
    __tablename__ = 'receipt_scans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    merchant = db.Column(db.String(150), nullable=True)
    total_amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=True)
    date = db.Column(db.Date, nullable=True)
    items_json = db.Column(db.Text, nullable=True) # JSON list of detected items
    raw_ocr = db.Column(db.Text, nullable=True)
    confidence = db.Column(db.Float, default=0.95)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "merchant": self.merchant or "Unknown Merchant",
            "total_amount": self.total_amount,
            "category": self.category or "Other",
            "date": self.date.isoformat() if self.date else None,
            "items": self.items_json,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
