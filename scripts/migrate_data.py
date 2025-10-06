# Data Migration Script for Existing JSON Data

import json
import os
import sys
from datetime import datetime, date
from decimal import Decimal
import uuid

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from models import db, User, Assessment, Goal, Account, Transaction, ProgressSnapshot
from flask import Flask
from werkzeug.security import generate_password_hash

def create_app():
    """Create Flask app for migration"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://risk_agent_user:risk_agent_password@localhost:5432/risk_agent_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def migrate_user_data():
    """Migrate existing user data from JSON files"""
    app = create_app()
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Migrate user data from user_data directory
        user_data_dir = os.path.join(os.path.dirname(__file__), '..', 'user_data')
        
        if os.path.exists(user_data_dir):
            for filename in os.listdir(user_data_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(user_data_dir, filename)
                    migrate_user_file(filepath)
        
        # Migrate mock data
        mock_data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'mock')
        if os.path.exists(mock_data_dir):
            for user_dir in os.listdir(mock_data_dir):
                user_path = os.path.join(mock_data_dir, user_dir)
                if os.path.isdir(user_path):
                    migrate_mock_user_data(user_dir, user_path)

def migrate_user_file(filepath):
    """Migrate a single user JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        user_id = data.get('user_id')
        if not user_id:
            return
        
        # Create user
        user = User.query.filter_by(id=user_id).first()
        if not user:
            user = User(
                id=user_id,
                email=f"{user_id}@example.com",
                password_hash=generate_password_hash("password123"),
                full_name=f"User {user_id}",
                username=user_id,
                phone="+1234567890"
            )
            db.session.add(user)
            db.session.commit()
        
        # Migrate assessment data
        if 'assessment_data' in data:
            migrate_assessment_data(user_id, data['assessment_data'])
        
        # Migrate goals
        if 'goals' in data and 'selected_goals' in data['goals']:
            migrate_goals_data(user_id, data['goals']['selected_goals'])
        
        print(f"Migrated user data for {user_id}")
        
    except Exception as e:
        print(f"Error migrating {filepath}: {e}")

def migrate_assessment_data(user_id, assessment_data):
    """Migrate assessment data"""
    assessment = Assessment.query.filter_by(user_id=user_id).first()
    if not assessment:
        assessment = Assessment(
            user_id=user_id,
            answers=assessment_data.get('answers', {}),
            risk_score=assessment_data.get('risk_profile', {}).get('score_percentage'),
            risk_label=assessment_data.get('risk_profile', {}).get('label'),
            risk_description=assessment_data.get('risk_profile', {}).get('description'),
            individual_scores=assessment_data.get('individual_scores', {}),
            question_weights=assessment_data.get('question_weights', {}),
            status='completed',
            completed_at=datetime.utcnow()
        )
        db.session.add(assessment)
        db.session.commit()

def migrate_goals_data(user_id, goals_data):
    """Migrate goals data"""
    for goal_data in goals_data:
        if goal_data.get('status') == 'active':
            goal = Goal(
                user_id=user_id,
                name=goal_data.get('text', 'Migrated Goal'),
                description='Migrated from JSON data',
                category='Other',
                target_amount=10000.0,  # Default amount
                target_date=date(2026, 12, 31),  # Default date
                start_amount=0.0,
                current_amount=0.0
            )
            db.session.add(goal)
    
    db.session.commit()

def migrate_mock_user_data(user_id, user_path):
    """Migrate mock user data"""
    try:
        # Create user
        user = User.query.filter_by(id=user_id).first()
        if not user:
            user = User(
                id=user_id,
                email=f"{user_id}@example.com",
                password_hash=generate_password_hash("password123"),
                full_name=f"Mock User {user_id}",
                username=user_id,
                phone="+1234567890"
            )
            db.session.add(user)
            db.session.commit()
        
        # Migrate profile data
        profile_file = os.path.join(user_path, 'profile.json')
        if os.path.exists(profile_file):
            with open(profile_file, 'r') as f:
                profile_data = json.load(f)
            
            # Create assessment
            assessment = Assessment.query.filter_by(user_id=user_id).first()
            if not assessment:
                assessment = Assessment(
                    user_id=user_id,
                    answers={},
                    risk_score=50.0,
                    risk_label=profile_data.get('risk_label', 'Balanced'),
                    risk_description='Migrated from mock data',
                    status='completed',
                    completed_at=datetime.utcnow()
                )
                db.session.add(assessment)
                db.session.commit()
            
            # Create goal from profile
            goal_data = profile_data.get('goal', {})
            if goal_data:
                goal = Goal(
                    user_id=user_id,
                    name=goal_data.get('name', 'Migrated Goal'),
                    description='Migrated from mock data',
                    category='Other',
                    target_amount=float(goal_data.get('target_amount', 10000)),
                    target_date=datetime.fromisoformat(goal_data.get('target_date', '2026-12-31')).date(),
                    start_amount=float(goal_data.get('start_amount', 0)),
                    current_amount=float(goal_data.get('start_amount', 0))
                )
                db.session.add(goal)
                db.session.commit()
        
        # Migrate accounts
        accounts_file = os.path.join(user_path, 'accounts.json')
        if os.path.exists(accounts_file):
            with open(accounts_file, 'r') as f:
                accounts_data = json.load(f)
            
            for account_data in accounts_data:
                account = Account(
                    user_id=user_id,
                    account_name=f"{account_data.get('type', 'account').title()} Account",
                    account_type=account_data.get('type', 'checking'),
                    balance=float(account_data.get('balance', 0))
                )
                db.session.add(account)
            
            db.session.commit()
        
        # Migrate transactions
        transactions_file = os.path.join(user_path, 'transactions.json')
        if os.path.exists(transactions_file):
            with open(transactions_file, 'r') as f:
                transactions_data = json.load(f)
            
            # Get accounts for this user
            accounts = Account.query.filter_by(user_id=user_id).all()
            if accounts:
                account = accounts[0]  # Use first account
                
                for txn_data in transactions_data:
                    transaction = Transaction(
                        user_id=user_id,
                        account_id=account.id,
                        date=datetime.fromisoformat(txn_data.get('date', '2025-01-01')).date(),
                        amount=float(txn_data.get('amount', 0)),
                        category=txn_data.get('category'),
                        description=txn_data.get('description'),
                        transaction_type='income' if float(txn_data.get('amount', 0)) > 0 else 'expense'
                    )
                    db.session.add(transaction)
                
                db.session.commit()
        
        print(f"Migrated mock data for {user_id}")
        
    except Exception as e:
        print(f"Error migrating mock data for {user_id}: {e}")

if __name__ == "__main__":
    print("Starting data migration...")
    migrate_user_data()
    print("Data migration completed!")
