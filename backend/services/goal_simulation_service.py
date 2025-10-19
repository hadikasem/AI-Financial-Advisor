# Goal Simulation Service for Goal-Specific Financial Tracking

from models import db, Goal, Account, Transaction
from datetime import datetime, date, timedelta
import json
import uuid
import random
from typing import Dict, List, Optional, Any
from decimal import Decimal

class GoalSimulationService:
    def __init__(self):
        pass
    
    def get_goal_account(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Get the account associated with a goal"""
        goal = Goal.query.get(goal_id)
        if not goal:
            return None
        
        # If goal doesn't have an account_id, create one
        if not goal.account_id:
            account = Account(
                account_name=f"Goal: {goal.name}",
                account_type="Goal Account",
                balance=0.0,
                user_id=goal.user_id
            )
            db.session.add(account)
            db.session.flush()  # Get the account ID
            
            # Link goal to account
            goal.account_id = account.id
            db.session.commit()
            
            return account.to_dict()
        
        account = Account.query.get(goal.account_id)
        if not account:
            return None
        
        return account.to_dict()
    
    def get_goal_transactions(self, goal_id: str) -> List[Dict[str, Any]]:
        """Get transactions for a specific goal"""
        goal = Goal.query.get(goal_id)
        if not goal:
            return []
        
        # If goal doesn't have an account_id, create one
        if not goal.account_id:
            account = Account(
                account_name=f"Goal: {goal.name}",
                account_type="Goal Account",
                balance=0.0,
                user_id=goal.user_id
            )
            db.session.add(account)
            db.session.flush()  # Get the account ID
            
            # Link goal to account
            goal.account_id = account.id
            db.session.commit()
        
        transactions = Transaction.query.filter_by(
            account_id=goal.account_id,
            user_id=goal.user_id
        ).order_by(Transaction.date.desc(), Transaction.created_at.desc()).all()
        
        return [transaction.to_dict() for transaction in transactions]
    
    def simulate_goal_progress(self, goal_id: str, months_to_simulate: int) -> Dict[str, Any]:
        """Simulate progress for a specific goal by adding transactions"""
        goal = Goal.query.get(goal_id)
        if not goal:
            raise ValueError("Goal not found")
        
        account = Account.query.get(goal.account_id)
        if not account:
            raise ValueError("Goal account not found")
        
        # Get the last simulation date or start from goal start date
        last_simulation_date = getattr(goal, 'last_simulation_date', None)
        if last_simulation_date:
            current_date = last_simulation_date
        else:
            current_date = goal.start_date
        
        # Generate mock transactions for this specific goal
        transactions_generated = 0
        simulation_end_date = current_date
        
        for month in range(months_to_simulate):
            # Generate 8-15 transactions per month
            num_transactions = 8 + (month % 8)  # Vary between 8-15
            
            for transaction_num in range(num_transactions):
                # Distribute transactions throughout the month
                days_into_month = (transaction_num * 30) // num_transactions
                transaction_date = current_date + timedelta(days=days_into_month)
                
                # Generate mock transaction
                transaction = self._generate_mock_transaction(transaction_date, goal.category)
                
                # Add transaction to the transactions table
                self._add_transaction_to_goal(goal_id, account.id, goal.user_id, transaction)
                transactions_generated += 1
            
            # Move to next month
            current_date += timedelta(days=30)  # Approximate month
            simulation_end_date = current_date
        
        # Update goal's current_amount to match account balance
        goal.current_amount = float(account.balance)
        goal.updated_at = datetime.utcnow()
        
        # Store the last simulation date in goal metadata
        goal.last_simulation_date = simulation_end_date
        
        # Check if goal is completed
        is_completed = float(account.balance) >= float(goal.target_amount)
        if is_completed:
            goal.status = 'completed'
            goal.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return {
            'success': True,
            'transactions_generated': transactions_generated,
            'months_simulated': months_to_simulate,
            'progress_until': simulation_end_date.isoformat(),
            'current_balance': float(account.balance),
            'is_completed': is_completed,
            'goal_status': goal.status
        }
    
    def _generate_mock_transaction(self, transaction_date: date, goal_category: str) -> Dict[str, Any]:
        """Generate a mock transaction for goal simulation"""
        # Generate random amount between $50 and $500
        amount = round(random.uniform(50, 500), 2)
        
        # Generate transaction type (mostly income/savings for goals)
        transaction_types = ['income', 'savings', 'expense']
        weights = [0.4, 0.4, 0.2]  # 40% income, 40% savings, 20% expense
        transaction_type = random.choices(transaction_types, weights=weights)[0]
        
        # Generate category based on goal category
        categories = {
            'Emergency Fund': ['Salary', 'Bonus', 'Investment', 'Other Income'],
            'Vacation': ['Salary', 'Bonus', 'Savings', 'Other Income'],
            'Education': ['Salary', 'Scholarship', 'Grant', 'Other Income'],
            'Home': ['Salary', 'Investment', 'Savings', 'Other Income'],
            'Car': ['Salary', 'Bonus', 'Savings', 'Other Income'],
            'Business': ['Revenue', 'Investment', 'Grant', 'Other Income'],
            'Retirement': ['Salary', 'Investment', 'Pension', 'Other Income'],
            'Other': ['Salary', 'Investment', 'Savings', 'Other Income']
        }
        
        category_options = categories.get(goal_category, categories['Other'])
        category = random.choice(category_options)
        
        # Generate description
        descriptions = {
            'income': f"Mock income for {category}",
            'savings': f"Mock savings contribution for {category}",
            'expense': f"Mock expense for {category}"
        }
        
        description = descriptions.get(transaction_type, f"Mock {transaction_type} for {category}")
        
        return {
            'date': transaction_date.isoformat(),
            'amount': amount,
            'category': category,
            'description': description,
            'transaction_type': transaction_type
        }
    
    def _add_transaction_to_goal(self, goal_id: str, account_id: str, user_id: str, transaction_data: Dict[str, Any]) -> None:
        """Add a transaction to a goal's account and update balance"""
        # Create transaction
        transaction = Transaction(
            user_id=user_id,
            account_id=account_id,
            date=datetime.fromisoformat(transaction_data['date']).date(),
            amount=Decimal(str(transaction_data['amount'])),
            category=transaction_data['category'],
            description=transaction_data['description'],
            transaction_type=transaction_data['transaction_type']
        )
        
        db.session.add(transaction)
        
        # Update account balance
        account = Account.query.get(account_id)
        if transaction_data['transaction_type'] in ['income', 'savings']:
            account.balance += Decimal(str(transaction_data['amount']))
        elif transaction_data['transaction_type'] == 'expense':
            account.balance -= Decimal(str(transaction_data['amount']))
        
        account.updated_at = datetime.utcnow()
    
    def get_goal_dashboard_data(self, goal_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a goal"""
        goal = Goal.query.get(goal_id)
        if not goal:
            raise ValueError("Goal not found")
        
        account = Account.query.get(goal.account_id) if goal.account_id else None
        transactions = self.get_goal_transactions(goal_id)
        
        return {
            'goal': goal.to_dict(),
            'account': account.to_dict() if account else None,
            'transactions': transactions,
            'current_balance': float(account.balance) if account else 0.0,
            'progress_percentage': (float(account.balance) / goal.target_amount * 100) if account and goal.target_amount > 0 else 0.0
        }
