# Database Models for Risk Assessment and Goal Tracking App

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from enum import Enum
import json
import uuid

# This will be initialized by the main app
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    assessments = db.relationship('Assessment', backref='user', lazy=True, cascade='all, delete-orphan')
    goals = db.relationship('Goal', backref='user', lazy=True, cascade='all, delete-orphan')
    progress_snapshots = db.relationship('ProgressSnapshot', backref='user', lazy=True, cascade='all, delete-orphan')
    accounts = db.relationship('Account', backref='user', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'username': self.username,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }

class Assessment(db.Model):
    __tablename__ = 'assessments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    answers = db.Column(db.JSON, nullable=False, default=dict)
    risk_score = db.Column(db.Float)
    risk_label = db.Column(db.String(50))
    risk_description = db.Column(db.Text)
    individual_scores = db.Column(db.JSON, default=dict)
    question_weights = db.Column(db.JSON, default=dict)
    status = db.Column(db.String(20), default='in_progress')  # in_progress, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'answers': self.answers,
            'risk_score': self.risk_score,
            'risk_label': self.risk_label,
            'risk_description': self.risk_description,
            'individual_scores': self.individual_scores,
            'question_weights': self.question_weights,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class GoalCategory(Enum):
    EMERGENCY_FUND = "Emergency Fund"
    RETIREMENT = "Retirement"
    VACATION = "Vacation"
    EDUCATION = "Education"
    HOME_PURCHASE = "Home Purchase"
    DEBT_PAYOFF = "Debt Payoff"
    INVESTMENT = "Investment"
    BUSINESS = "Business"
    OTHER = "Other"

class Goal(db.Model):
    __tablename__ = 'goals'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)
    target_amount = db.Column(db.Numeric(15, 2), nullable=False)
    target_date = db.Column(db.Date, nullable=False)
    start_amount = db.Column(db.Numeric(15, 2), default=0.0)
    start_date = db.Column(db.Date, default=date.today)
    current_amount = db.Column(db.Numeric(15, 2), default=0.0)
    status = db.Column(db.String(20), default='active')  # active, completed, paused, deleted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    progress_snapshots = db.relationship('ProgressSnapshot', backref='goal', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'target_amount': float(self.target_amount),
            'target_date': self.target_date.isoformat(),
            'start_amount': float(self.start_amount),
            'start_date': self.start_date.isoformat(),
            'current_amount': float(self.current_amount),
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)  # checking, savings, investment, credit
    balance = db.Column(db.Numeric(15, 2), default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='account', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_name': self.account_name,
            'account_type': self.account_type,
            'balance': float(self.balance),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)  # positive = inflow, negative = outflow
    category = db.Column(db.String(50))
    description = db.Column(db.String(200))
    transaction_type = db.Column(db.String(20), nullable=False)  # income, expense, transfer, investment
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_id': self.account_id,
            'date': self.date.isoformat(),
            'amount': float(self.amount),
            'category': self.category,
            'description': self.description,
            'transaction_type': self.transaction_type,
            'created_at': self.created_at.isoformat()
        }

class ProgressSnapshot(db.Model):
    __tablename__ = 'progress_snapshots'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    goal_id = db.Column(db.String(36), db.ForeignKey('goals.id'), nullable=False)
    as_of = db.Column(db.DateTime, nullable=False)
    current_amount = db.Column(db.Numeric(15, 2), nullable=False)
    progress_pct = db.Column(db.Float, nullable=False)
    pacing_status = db.Column(db.String(20), nullable=False)  # on_track, ahead, behind
    pacing_detail = db.Column(db.String(200))
    weekly_net_savings = db.Column(db.Numeric(15, 2))
    savings_rate_30d = db.Column(db.Numeric(15, 2))
    target_amount = db.Column(db.Numeric(15, 2), nullable=False)
    target_date = db.Column(db.Date, nullable=False)
    start_amount = db.Column(db.Numeric(15, 2), nullable=False)
    kpis = db.Column(db.JSON, default=dict)
    source_hash = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal_id': self.goal_id,
            'as_of': self.as_of.isoformat(),
            'current_amount': float(self.current_amount),
            'progress_pct': self.progress_pct,
            'pacing_status': self.pacing_status,
            'pacing_detail': self.pacing_detail,
            'weekly_net_savings': float(self.weekly_net_savings) if self.weekly_net_savings else None,
            'savings_rate_30d': float(self.savings_rate_30d) if self.savings_rate_30d else None,
            'target_amount': float(self.target_amount),
            'target_date': self.target_date.isoformat(),
            'start_amount': float(self.start_amount),
            'kpis': self.kpis,
            'source_hash': self.source_hash,
            'created_at': self.created_at.isoformat()
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    goal_id = db.Column(db.String(36), db.ForeignKey('goals.id'), nullable=True)
    type = db.Column(db.String(50), nullable=False)  # milestone, deadline, weekly_update, recommendation
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    sent_email = db.Column(db.Boolean, default=False)
    sent_push = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal_id': self.goal_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'sent_email': self.sent_email,
            'sent_push': self.sent_push,
            'created_at': self.created_at.isoformat()
        }
