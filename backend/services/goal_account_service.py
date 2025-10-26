# Goal Account Service for Goal-Specific Financial Tracking

from models import db, GoalAccount, Goal
from datetime import datetime, date, timedelta
import json
import uuid
from typing import Dict, List, Optional, Any

class GoalAccountService:
    def __init__(self):
        pass
    
    def create_goal_account(self, goal_id: str) -> Dict[str, Any]:
        """Create a new account for a specific goal"""
        # Check if goal exists
        goal = Goal.query.filter_by(id=goal_id).first()
        if not goal:
            raise ValueError("Goal not found")
        
        # Check if account already exists for this goal
        existing_account = GoalAccount.query.filter_by(goal_id=goal_id).first()
        if existing_account:
            return existing_account.to_dict()
        
        # Create new goal account (truncate name to fit 100 char limit)
        goal_name_truncated = goal.name[:94]  # Leave room for "Goal: " (6 chars)
        account_name = f"Goal: {goal_name_truncated}"
        from decimal import Decimal
        
        goal_account = GoalAccount(
            goal_id=goal_id,
            account_name=account_name,
            current_balance=Decimal('0.0'),
            transactions=[],
            simulation_history=[],
            last_simulation_date=goal.start_date  # Set initial simulation date to goal start date
        )
        
        db.session.add(goal_account)
        db.session.commit()
        
        return goal_account.to_dict()
    
    def get_goal_account(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Get the account for a specific goal"""
        goal_account = GoalAccount.query.filter_by(goal_id=goal_id).first()
        
        if not goal_account:
            return None
        
        return goal_account.to_dict()
    
    def update_goal_account_balance(self, goal_id: str, new_balance: float) -> Dict[str, Any]:
        """Update the balance for a goal's account"""
        goal_account = GoalAccount.query.filter_by(goal_id=goal_id).first()
        
        if not goal_account:
            raise ValueError("Goal account not found")
        
        goal_account.current_balance = new_balance
        goal_account.updated_at = datetime.utcnow()
        
        # Also update the goal's current_amount
        goal = Goal.query.filter_by(id=goal_id).first()
        if goal:
            goal.current_amount = new_balance
            goal.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return goal_account.to_dict()
    
    def add_transaction_to_goal(self, goal_id: str, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Add a transaction to a goal's account"""
        goal_account = GoalAccount.query.filter_by(goal_id=goal_id).first()
        
        if not goal_account:
            raise ValueError("Goal account not found")
        
        # Add transaction to the list
        transactions = goal_account.transactions or []
        transaction['id'] = str(uuid.uuid4())
        transaction['created_at'] = datetime.utcnow().isoformat()
        transactions.append(transaction)
        
        goal_account.transactions = transactions
        
        # Update balance - convert to Decimal for proper arithmetic
        from decimal import Decimal
        amount = Decimal(str(transaction.get('amount', 0)))
        
        if transaction.get('transaction_type') == 'income':
            goal_account.current_balance += amount
        elif transaction.get('transaction_type') == 'expense':
            goal_account.current_balance -= amount
        
        goal_account.updated_at = datetime.utcnow()
        
        # Also update the goal's current_amount
        goal = Goal.query.filter_by(id=goal_id).first()
        if goal:
            goal.current_amount = float(goal_account.current_balance)
            goal.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return goal_account.to_dict()
    
    def get_goal_transactions(self, goal_id: str) -> List[Dict[str, Any]]:
        """Get all transactions for a specific goal"""
        goal_account = GoalAccount.query.filter_by(goal_id=goal_id).first()
        
        if not goal_account:
            return []
        
        return goal_account.transactions or []
    
    def simulate_goal_progress(self, goal_id: str, months_to_simulate: int) -> Dict[str, Any]:
        """Simulate progress for a specific goal only"""
        goal_account = GoalAccount.query.filter_by(goal_id=goal_id).first()
        
        if not goal_account:
            raise ValueError("Goal account not found")
        
        goal = Goal.query.filter_by(id=goal_id).first()
        if not goal:
            raise ValueError("Goal not found")
        
        # Generate mock transactions for this specific goal
        transactions_generated = 0
        current_date = goal_account.last_simulation_date or goal.start_date
        
        for month in range(months_to_simulate):
            # Generate 8-15 transactions per month
            num_transactions = 8 + (month % 8)  # Vary between 8-15
            
            for _ in range(num_transactions):
                # Generate mock transaction
                transaction = self._generate_mock_transaction(current_date, goal.category)
                
                # Add transaction to goal account
                self.add_transaction_to_goal(goal_id, transaction)
                transactions_generated += 1
            
            # Move to next month
            if isinstance(current_date, str):
                current_date = datetime.fromisoformat(current_date).date()
            current_date += timedelta(days=30)  # Approximate month
        
        # Update last simulation date
        goal_account.last_simulation_date = current_date
        db.session.commit()
        
        return {
            'success': True,
            'transactions_generated': transactions_generated,
            'months_simulated': months_to_simulate,
            'progress_until': current_date.isoformat(),
            'current_balance': float(goal_account.current_balance)
        }
    
    def _generate_mock_transaction(self, transaction_date: date, goal_category: str) -> Dict[str, Any]:
        """Generate a mock transaction for goal simulation"""
        import random
        
        # Determine transaction type (70% income, 30% expense for goal progress)
        transaction_type = 'income' if random.random() < 0.7 else 'expense'
        
        if transaction_type == 'income':
            # Income transactions (salary, bonus, etc.)
            income_types = ['Salary', 'Bonus', 'Freelance', 'Investment Return', 'Side Income']
            category = random.choice(income_types)
            amount = random.uniform(500, 3000)
            description = f"{category} payment"
        else:
            # Expense transactions (but smaller amounts for goal context)
            expense_types = ['Groceries', 'Utilities', 'Transportation', 'Entertainment', 'Shopping']
            category = random.choice(expense_types)
            amount = random.uniform(50, 500)
            description = f"{category} expense"
        
        return {
            'date': transaction_date.isoformat(),
            'amount': round(amount, 2),
            'category': category,
            'description': description,
            'transaction_type': transaction_type
        }
    
    def get_goal_simulation_history(self, goal_id: str) -> List[Dict[str, Any]]:
        """Get simulation history for a specific goal"""
        goal_account = GoalAccount.query.filter_by(goal_id=goal_id).first()
        
        if not goal_account:
            return []
        
        return goal_account.simulation_history or []
    
    def add_simulation_record(self, goal_id: str, simulation_data: Dict[str, Any]) -> None:
        """Add a record to the simulation history"""
        goal_account = GoalAccount.query.filter_by(goal_id=goal_id).first()
        
        if not goal_account:
            raise ValueError("Goal account not found")
        
        simulation_history = goal_account.simulation_history or []
        simulation_data['timestamp'] = datetime.utcnow().isoformat()
        simulation_history.append(simulation_data)
        
        goal_account.simulation_history = simulation_history
        goal_account.updated_at = datetime.utcnow()
        
        db.session.commit()
    
    def delete_goal_account(self, goal_id: str) -> None:
        """Delete a goal account (when goal is deleted)"""
        goal_account = GoalAccount.query.filter_by(goal_id=goal_id).first()
        
        if goal_account:
            db.session.delete(goal_account)
            db.session.commit()
