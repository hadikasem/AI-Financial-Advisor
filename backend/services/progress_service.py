# Progress Service for Smart Time-Based Progress Tracking

from models import db, User, Goal, ProgressSnapshot, Account, Transaction
from datetime import datetime, date, timedelta
import json
import uuid
import hashlib
import random
from typing import Dict, List, Optional, Any
from decimal import Decimal

class ProgressService:
    def __init__(self):
        self.transaction_categories = {
            'income': ['Salary', 'Bonus', 'Freelance', 'Investment Returns', 'Rental Income'],
            'housing': ['Rent', 'Mortgage', 'Property Tax', 'Home Insurance', 'Utilities'],
            'food': ['Groceries', 'Restaurants', 'Coffee', 'Takeout', 'Dining Out'],
            'transportation': ['Gas', 'Public Transit', 'Car Payment', 'Car Insurance', 'Maintenance'],
            'entertainment': ['Movies', 'Streaming', 'Concerts', 'Sports', 'Games'],
            'health': ['Insurance', 'Doctor', 'Pharmacy', 'Gym', 'Medical'],
            'shopping': ['Clothing', 'Electronics', 'Home Goods', 'Personal Care'],
            'investment': ['401k', 'IRA', 'Stocks', 'Bonds', 'ETF'],
            'transfer': ['Savings Transfer', 'Investment Transfer', 'Account Transfer']
        }
    
    def update_progress(self, user_id: str) -> Dict[str, Any]:
        """Update progress with smart time-based simulation"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Get user's active goals
        goals = Goal.query.filter_by(user_id=user_id, status='active').all()
        if not goals:
            raise ValueError("No active goals found")
        
        # Get or create user's simulation timestamp
        simulation_timestamp = self._get_user_simulation_timestamp(user_id)
        
        # Calculate time elapsed since last update
        now = datetime.utcnow()
        time_elapsed = now - simulation_timestamp
        
        # Generate realistic data for the elapsed time
        self._generate_time_based_data(user_id, time_elapsed)
        
        # Update simulation timestamp
        self._update_user_simulation_timestamp(user_id, now)
        
        # Calculate progress for all goals
        progress_results = []
        for goal in goals:
            progress = self._calculate_goal_progress(goal)
            progress_results.append(progress)
            
            # Create progress snapshot
            self._create_progress_snapshot(user_id, goal.id, progress)
        
        return {
            'message': 'Progress updated successfully',
            'time_elapsed_days': time_elapsed.days,
            'goals_progress': progress_results,
            'updated_at': now.isoformat()
        }
    
    def get_progress(self, user_id: str, goal_id: str) -> Dict[str, Any]:
        """Get progress for a specific goal"""
        goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
        if not goal:
            raise ValueError("Goal not found")
        
        # Get latest progress snapshot
        latest_snapshot = ProgressSnapshot.query.filter_by(
            user_id=user_id, 
            goal_id=goal_id
        ).order_by(ProgressSnapshot.as_of.desc()).first()
        
        if latest_snapshot:
            return latest_snapshot.to_dict()
        
        # Calculate current progress if no snapshot exists
        progress = self._calculate_goal_progress(goal)
        return progress
    
    def _get_user_simulation_timestamp(self, user_id: str) -> datetime:
        """Get user's simulation timestamp (stored in user metadata or default to account creation)"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # For now, use user creation date as starting point
        # In a real implementation, you'd store this in a separate table
        return user.created_at
    
    def _update_user_simulation_timestamp(self, user_id: str, timestamp: datetime) -> None:
        """Update user's simulation timestamp"""
        # In a real implementation, you'd store this in a separate table
        # For now, we'll use a simple approach
        pass
    
    def _generate_time_based_data(self, user_id: str, time_elapsed: timedelta) -> None:
        """Generate realistic financial data for the elapsed time period"""
        days_elapsed = time_elapsed.days
        
        if days_elapsed <= 0:
            return
        
        # Get user's accounts
        accounts = Account.query.filter_by(user_id=user_id, is_active=True).all()
        if not accounts:
            # Create default accounts if none exist
            accounts = self._create_default_accounts(user_id)
        
        # Generate transactions for each day
        for day_offset in range(days_elapsed):
            transaction_date = (datetime.utcnow() - timedelta(days=days_elapsed - day_offset)).date()
            self._generate_daily_transactions(user_id, accounts, transaction_date)
        
        # Update account balances
        self._update_account_balances(user_id, accounts)
    
    def _create_default_accounts(self, user_id: str) -> List[Account]:
        """Create default accounts for a user"""
        default_accounts = [
            Account(user_id=user_id, account_name="Checking Account", account_type="checking", balance=5000.0),
            Account(user_id=user_id, account_name="Savings Account", account_type="savings", balance=10000.0),
            Account(user_id=user_id, account_name="Investment Account", account_type="investment", balance=15000.0)
        ]
        
        for account in default_accounts:
            db.session.add(account)
        
        db.session.commit()
        return default_accounts
    
    def _generate_daily_transactions(self, user_id: str, accounts: List[Account], transaction_date: date) -> None:
        """Generate realistic transactions for a specific day"""
        # Determine transaction patterns based on day of week and date
        day_of_week = transaction_date.weekday()
        day_of_month = transaction_date.day
        
        transactions = []
        
        # Salary deposits (bi-weekly on Fridays)
        if day_of_week == 4 and day_of_month % 14 < 2:  # Roughly bi-weekly
            salary_amount = random.uniform(3000, 8000)
            transactions.append({
                'account_id': accounts[0].id,  # Checking account
                'amount': salary_amount,
                'category': 'income',
                'description': 'Salary Deposit',
                'transaction_type': 'income'
            })
        
        # Rent payment (1st of month)
        if day_of_month == 1:
            rent_amount = random.uniform(1200, 3000)
            transactions.append({
                'account_id': accounts[0].id,
                'amount': -rent_amount,
                'category': 'housing',
                'description': 'Rent Payment',
                'transaction_type': 'expense'
            })
        
        # Regular expenses
        if random.random() < 0.8:  # 80% chance of daily expenses
            expense_categories = ['food', 'transportation', 'entertainment', 'shopping']
            category = random.choice(expense_categories)
            amount = random.uniform(10, 200)
            
            transactions.append({
                'account_id': accounts[0].id,
                'amount': -amount,
                'category': category,
                'description': random.choice(self.transaction_categories.get(category, ['Purchase'])),
                'transaction_type': 'expense'
            })
        
        # Investment contributions (monthly)
        if day_of_month == 15 and random.random() < 0.7:
            investment_amount = random.uniform(500, 2000)
            transactions.append({
                'account_id': accounts[2].id,  # Investment account
                'amount': investment_amount,
                'category': 'investment',
                'description': 'Monthly Investment Contribution',
                'transaction_type': 'investment'
            })
        
        # Savings transfers (weekly)
        if day_of_week == 0 and random.random() < 0.6:  # Sunday
            savings_amount = random.uniform(200, 1000)
            transactions.append({
                'account_id': accounts[1].id,  # Savings account
                'amount': savings_amount,
                'category': 'transfer',
                'description': 'Weekly Savings Transfer',
                'transaction_type': 'transfer'
            })
        
        # Create transactions in database
        for txn_data in transactions:
            transaction = Transaction(
                user_id=user_id,
                account_id=txn_data['account_id'],
                date=transaction_date,
                amount=txn_data['amount'],
                category=txn_data['category'],
                description=txn_data['description'],
                transaction_type=txn_data['transaction_type']
            )
            db.session.add(transaction)
        
        db.session.commit()
    
    def _update_account_balances(self, user_id: str, accounts: List[Account]) -> None:
        """Update account balances based on transactions"""
        for account in accounts:
            # Get all transactions for this account
            transactions = Transaction.query.filter_by(
                user_id=user_id,
                account_id=account.id
            ).all()
            
            # Calculate new balance
            new_balance = sum(float(t.amount) for t in transactions)
            
            # Add some market fluctuation for investment accounts
            if account.account_type == 'investment':
                fluctuation = random.uniform(-0.02, 0.02)  # ±2% daily fluctuation
                new_balance *= (1 + fluctuation)
            
            account.balance = new_balance
        
        db.session.commit()
    
    def _calculate_goal_progress(self, goal: Goal) -> Dict[str, Any]:
        """Calculate comprehensive progress metrics for a goal"""
        # Get user's total account balance
        accounts = Account.query.filter_by(user_id=goal.user_id, is_active=True).all()
        total_balance = sum(float(account.balance) for account in accounts)
        
        # Update goal's current amount
        goal.current_amount = total_balance
        db.session.commit()
        
        # Calculate progress percentage
        total_needed = float(goal.target_amount) - float(goal.start_amount)
        if total_needed <= 0:
            progress_pct = 100.0
        else:
            progress_pct = max(0.0, min(100.0, 
                ((total_balance - float(goal.start_amount)) / total_needed) * 100.0))
        
        # Calculate pacing
        today = date.today()
        total_days = (goal.target_date - goal.start_date).days
        elapsed_days = (today - goal.start_date).days
        
        if total_days <= 0:
            pacing_status = "completed" if progress_pct >= 100 else "overdue"
            pacing_detail = "Goal date has passed"
        else:
            expected_progress = (elapsed_days / total_days) * 100
            progress_diff = progress_pct - expected_progress
            
            if abs(progress_diff) < 5:
                pacing_status = "on_track"
                pacing_detail = "On track with target pace"
            elif progress_diff > 0:
                pacing_status = "ahead"
                weeks_ahead = int(progress_diff * total_days / 700)  # Rough weeks calculation
                pacing_detail = f"~{weeks_ahead} weeks ahead of target pace"
            else:
                pacing_status = "behind"
                weeks_behind = int(abs(progress_diff) * total_days / 700)
                pacing_detail = f"~{weeks_behind} weeks behind target pace"
        
        # Calculate savings metrics
        weekly_net = self._calculate_weekly_net_savings(goal.user_id)
        monthly_savings = self._calculate_monthly_savings(goal.user_id)
        
        return {
            'goal_id': goal.id,
            'current_amount': total_balance,
            'progress_pct': progress_pct,
            'pacing_status': pacing_status,
            'pacing_detail': pacing_detail,
            'weekly_net_savings': weekly_net,
            'savings_rate_30d': monthly_savings,
            'target_amount': float(goal.target_amount),
            'target_date': goal.target_date.isoformat(),
            'start_amount': float(goal.start_amount),
            'days_remaining': max(0, (goal.target_date - today).days)
        }
    
    def _calculate_weekly_net_savings(self, user_id: str) -> float:
        """Calculate net savings over the last 7 days"""
        cutoff_date = date.today() - timedelta(days=7)
        transactions = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.date >= cutoff_date
        ).all()
        
        return sum(float(t.amount) for t in transactions)
    
    def _calculate_monthly_savings(self, user_id: str) -> float:
        """Calculate net savings over the last 30 days"""
        cutoff_date = date.today() - timedelta(days=30)
        transactions = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.date >= cutoff_date
        ).all()
        
        return sum(float(t.amount) for t in transactions)
    
    def _create_progress_snapshot(self, user_id: str, goal_id: str, progress_data: Dict[str, Any]) -> None:
        """Create a progress snapshot record"""
        # Create source hash for idempotency
        source_data = f"{user_id}_{goal_id}_{progress_data['current_amount']}_{datetime.utcnow().isoformat()}"
        source_hash = hashlib.md5(source_data.encode()).hexdigest()[:8]
        
        snapshot = ProgressSnapshot(
            user_id=user_id,
            goal_id=goal_id,
            as_of=datetime.utcnow(),
            current_amount=progress_data['current_amount'],
            progress_pct=progress_data['progress_pct'],
            pacing_status=progress_data['pacing_status'],
            pacing_detail=progress_data['pacing_detail'],
            weekly_net_savings=progress_data['weekly_net_savings'],
            savings_rate_30d=progress_data['savings_rate_30d'],
            target_amount=progress_data['target_amount'],
            target_date=datetime.fromisoformat(progress_data['target_date']).date(),
            start_amount=progress_data['start_amount'],
            kpis={'days_remaining': progress_data['days_remaining']},
            source_hash=source_hash
        )
        
        db.session.add(snapshot)
        db.session.commit()
