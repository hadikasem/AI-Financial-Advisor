# Mock Progress Service for simulating user progress updates

from datetime import datetime, date, timedelta
from decimal import Decimal
import random
import uuid
from typing import Dict, List, Optional, Any
from sqlalchemy import func

from models import db, User, Goal, Transaction, Account, ProgressSnapshot


class MockProgressService:
    """Service for generating mock progress data and updating user goals"""
    
    def __init__(self):
        pass
    
    def update_progress(self, user_id: str, months_to_simulate: int = 1) -> Dict[str, Any]:
        """
        Update user progress by generating mock transactions for specified months
        
        Args:
            user_id: User ID to update progress for
            months_to_simulate: Number of months to simulate (1, 3, 6, or 12)
            
        Returns:
            Dictionary with updated progress information
        """
        try:
            # Get user and their active goals
            user = User.query.get(user_id)
            if not user:
                raise ValueError("User not found")
            
            goals = Goal.query.filter_by(user_id=user_id, status='active').all()
            if not goals:
                raise ValueError("No active goals found for user")
            
            # Get user's accounts for transactions
            accounts = Account.query.filter_by(user_id=user_id, is_active=True).all()
            if not accounts:
                # Create a default savings account if none exist
                default_account = Account(
                    user_id=user_id,
                    account_name="Savings Account",
                    account_type="savings",
                    balance=0.0
                )
                db.session.add(default_account)
                db.session.flush()  # Get the ID
                accounts = [default_account]
            
            # Determine start date for mock data
            start_date = self._get_start_date(user, months_to_simulate)
            
            # Generate mock transactions for the simulation period
            total_transactions = 0
            last_generated_date = start_date
            
            # Calculate the simulation period
            if user.last_mock_date:
                # For subsequent simulations, start from the day after last mock date
                simulation_start = user.last_mock_date + timedelta(days=1)
            else:
                # For first simulation, use the calculated start date
                simulation_start = start_date
            
            end_date = simulation_start + timedelta(days=months_to_simulate * 30)
            
            
            # Generate transactions distributed across the simulation period
            transactions_count = self._generate_transactions_in_range(
                user_id, accounts, simulation_start, end_date, goals
            )
            total_transactions += transactions_count
            last_generated_date = end_date
            
            # Update user's last_mock_date to simulate time progression
            # Each simulation click represents time passing by the simulated months
            user.last_mock_date = end_date
            
            # Recalculate progress for all goals using simulated current date
            updated_goals = []
            simulated_current_date = user.last_mock_date
            
            for goal in goals:
                updated_goal = self._recalculate_goal_progress(goal, simulated_current_date)
                updated_goals.append(updated_goal)
            
            # Create progress snapshot using simulated current date
            self._create_progress_snapshots(user_id, updated_goals, simulated_current_date)
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Generated {total_transactions} transactions for {months_to_simulate} month(s)',
                'transactions_generated': total_transactions,
                'months_simulated': months_to_simulate,
                'progress_until': user.last_mock_date.isoformat(),
                'goals_updated': len(updated_goals),
                'updated_metrics': self._get_updated_metrics(updated_goals, simulated_current_date)
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_start_date(self, user: User, months_to_simulate: int) -> Optional[date]:
        """Determine the start date for mock data generation"""
        if user.last_mock_date:
            # For subsequent simulations, return the last mock date
            # The actual simulation start will be calculated as last_mock_date + 1 day
            return user.last_mock_date
        else:
            # For first simulation, start from the earliest goal start date
            goals = Goal.query.filter_by(user_id=user.id, status='active').all()
            if goals:
                # Find the earliest start date among all goals
                earliest_goal_start = min(goal.start_date for goal in goals)
                start_date = earliest_goal_start
            else:
                # No goals, start from user creation date or 6 months ago
                user_start = user.created_at.date() if user.created_at else date.today()
                six_months_ago = date.today() - timedelta(days=180)
                start_date = max(user_start, six_months_ago)
            
            # Ensure we don't go too far back
            user_start = user.created_at.date() if user.created_at else date.today()
            start_date = max(start_date, user_start)
            
            return start_date
    
    def _generate_transactions_in_range(self, user_id: str, accounts: List[Account], 
                                      start_date: date, end_date: date, goals: List[Goal]) -> int:
        """Generate mock transactions distributed across a date range"""
        transactions_count = 0
        
        # Calculate total days in the range
        total_days = (end_date - start_date).days
        if total_days <= 0:
            return 0
        
        # Generate 8-15 transactions per month (scaled to the range)
        transactions_per_month = random.randint(8, 15)
        num_transactions = int(transactions_per_month * (total_days / 30))
        
        for _ in range(num_transactions):
            # Random day within the range
            random_days = random.randint(0, total_days - 1)
            transaction_date = start_date + timedelta(days=random_days)
            
            # Note: We allow future dates for simulation purposes
            
            # Choose random account
            account = random.choice(accounts)
            
            # Generate transaction amount (70% positive, 30% negative)
            is_positive = random.random() < 0.7
            
            if is_positive:
                # Income/savings transactions
                amount = random.uniform(50, 2000)
                transaction_type = random.choice(['income', 'transfer'])
                category = random.choice(['salary', 'bonus', 'investment', 'savings', 'refund'])
                description = f"Mock {category.title()}"
            else:
                # Expense transactions
                amount = -random.uniform(20, 800)
                transaction_type = 'expense'
                category = random.choice(['food', 'transportation', 'entertainment', 'utilities', 'shopping'])
                description = f"Mock {category.title()} Expense"
            
            # Create transaction
            transaction = Transaction(
                user_id=user_id,
                account_id=account.id,
                date=transaction_date,
                amount=Decimal(str(round(amount, 2))),
                category=category,
                description=description,
                transaction_type=transaction_type
            )
            
            db.session.add(transaction)
            transactions_count += 1
        
        return transactions_count
    
    def _generate_monthly_transactions(self, user_id: str, accounts: List[Account], 
                                     month_date: date, goals: List[Goal]) -> int:
        """Generate mock transactions for a specific month (legacy method)"""
        # Calculate start and end of the month
        start_date = month_date.replace(day=1)
        if month_date.month == 12:
            end_date = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)
        
        return self._generate_transactions_in_range(user_id, accounts, start_date, end_date, goals)
    
    def _recalculate_goal_progress(self, goal: Goal, simulated_current_date: date = None) -> Goal:
        """Recalculate progress for a specific goal"""
        # Use simulated current date if provided, otherwise use today
        if simulated_current_date is None:
            simulated_current_date = date.today()
        
        # Get all transactions for this user since goal start up to simulated current date
        transactions = Transaction.query.filter(
            Transaction.user_id == goal.user_id,
            Transaction.date >= goal.start_date,
            Transaction.date <= simulated_current_date
        ).all()
        
        # Calculate current amount (start_amount + sum of all transactions)
        total_amount = goal.start_amount
        for transaction in transactions:
            total_amount += transaction.amount
        
        # Update goal
        goal.current_amount = max(Decimal('0'), total_amount)  # Don't go below 0
        
        # Calculate progress percentage
        if goal.target_amount > 0:
            progress_pct = float(goal.current_amount) / float(goal.target_amount) * 100
            # Cap progress at 100% to avoid showing more than 100%
            progress_pct = min(100.0, progress_pct)
        else:
            progress_pct = 0.0
        
        # Mark as completed if target reached
        if progress_pct >= 100:
            goal.status = 'completed'
            goal.updated_at = datetime.utcnow()
        
        return goal
    
    def _create_progress_snapshots(self, user_id: str, goals: List[Goal], simulated_current_date: date):
        """Create progress snapshots for all goals"""
        for goal in goals:
            # Calculate days remaining based on simulated current date
            days_remaining = (goal.target_date - simulated_current_date).days
            
            # Calculate pacing status
            pacing_status, pacing_detail = self._calculate_pacing_status(goal, simulated_current_date)
            
            # Calculate weekly net savings (last 30 days from simulated date)
            weekly_savings = self._calculate_weekly_savings(user_id, goal, simulated_current_date)
            
            # Calculate progress percentage for snapshot
            if goal.target_amount > 0:
                progress_pct = float(goal.current_amount) / float(goal.target_amount) * 100
                progress_pct = min(100.0, progress_pct)  # Cap at 100%
            else:
                progress_pct = 0.0
            
            # Create snapshot
            snapshot = ProgressSnapshot(
                user_id=user_id,
                goal_id=goal.id,
                as_of=datetime.utcnow(),
                current_amount=goal.current_amount,
                progress_pct=progress_pct,
                pacing_status=pacing_status,
                pacing_detail=pacing_detail,
                weekly_net_savings=weekly_savings,
                savings_rate_30d=Decimal(str(float(weekly_savings) * 4)),  # Convert to Decimal properly
                target_amount=goal.target_amount,
                target_date=goal.target_date,
                start_amount=goal.start_amount,
                kpis={
                    'days_remaining': days_remaining,
                    'months_remaining': max(0, days_remaining // 30),
                    'avg_monthly_savings': float(self._calculate_avg_monthly_savings(user_id, goal, simulated_current_date))  # Convert to float for JSON
                }
            )
            
            db.session.add(snapshot)
    
    def _calculate_pacing_status(self, goal: Goal, simulated_current_date: date) -> tuple[str, str]:
        """Calculate if user is on track, ahead, or behind schedule"""
        if goal.target_amount <= 0:
            return 'unknown', 'No target amount set'
        
        # Calculate expected progress based on time elapsed
        total_days = (goal.target_date - goal.start_date).days
        elapsed_days = (simulated_current_date - goal.start_date).days
        
        if total_days <= 0:
            return 'unknown', 'Invalid date range'
        
        expected_progress = (elapsed_days / total_days) * 100
        actual_progress = float(goal.current_amount) / float(goal.target_amount) * 100
        
        difference = actual_progress - expected_progress
        
        if difference > 10:
            return 'ahead', f'Ahead by {difference:.1f}% - Great job!'
        elif difference < -10:
            return 'behind', f'Behind by {abs(difference):.1f}% - Consider increasing savings'
        else:
            return 'on_track', f'On track - {actual_progress:.1f}% complete'
    
    def _calculate_weekly_savings(self, user_id: str, goal: Goal, simulated_current_date: date) -> Decimal:
        """Calculate average weekly net savings over last 30 days from simulated date"""
        thirty_days_ago = simulated_current_date - timedelta(days=30)
        
        transactions = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.date >= thirty_days_ago,
            Transaction.date <= simulated_current_date
        ).all()
        
        total_amount = sum(transaction.amount for transaction in transactions)
        weekly_amount = float(total_amount) / 4.3  # Approximate weeks in 30 days
        
        return Decimal(str(round(weekly_amount, 2)))
    
    def _calculate_avg_monthly_savings(self, user_id: str, goal: Goal, simulated_current_date: date) -> Decimal:
        """Calculate average monthly savings since goal start up to simulated date"""
        transactions = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.date >= goal.start_date,
            Transaction.date <= simulated_current_date
        ).all()
        
        if not transactions:
            return Decimal('0')
        
        total_amount = sum(transaction.amount for transaction in transactions)
        months_elapsed = max(1, (simulated_current_date - goal.start_date).days / 30)
        monthly_amount = float(total_amount) / months_elapsed
        
        return Decimal(str(round(monthly_amount, 2)))
    
    def _get_updated_metrics(self, goals: List[Goal], simulated_current_date: date) -> List[Dict[str, Any]]:
        """Get updated metrics for all goals"""
        metrics = []
        
        for goal in goals:
            days_remaining = (goal.target_date - simulated_current_date).days
            progress_pct = float(goal.current_amount) / float(goal.target_amount) * 100 if goal.target_amount > 0 else 0
            
            metrics.append({
                'goal_id': goal.id,
                'goal_name': goal.name,
                'current_amount': float(goal.current_amount),
                'target_amount': float(goal.target_amount),
                'progress_pct': progress_pct,
                'days_remaining': days_remaining,
                'status': goal.status
            })
        
        return metrics
    
    def get_user_progress_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of user's progress across all goals"""
        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}
        
        # Get all goals (both active and completed)
        all_goals = Goal.query.filter_by(user_id=user_id).all()
        active_goals = [g for g in all_goals if g.status == 'active']
        completed_goals = [g for g in all_goals if g.status == 'completed']
        
        summary = {
            'user_id': user_id,
            'last_mock_date': user.last_mock_date.isoformat() if user.last_mock_date else None,
            'total_goals': len(all_goals),
            'active_goals': len(active_goals),
            'completed_goals': len(completed_goals),
            'total_target_amount': sum(float(g.target_amount) for g in all_goals),
            'total_current_amount': sum(float(g.current_amount) for g in all_goals),
            'overall_progress': 0
        }
        
        if summary['total_target_amount'] > 0:
            summary['overall_progress'] = (summary['total_current_amount'] / summary['total_target_amount']) * 100
        
        return summary
    
    def can_generate_more_data(self, user_id: str, months_to_simulate: int = 1) -> Dict[str, Any]:
        """Check if more mock data can be generated for the user"""
        user = User.query.get(user_id)
        if not user:
            return {'can_generate': False, 'reason': 'User not found'}
        
        start_date = self._get_start_date(user, months_to_simulate)
        
        return {
            'can_generate': start_date is not None,
            'start_date': start_date.isoformat() if start_date else None,
            'last_mock_date': user.last_mock_date.isoformat() if user.last_mock_date else None,
            'today': date.today().isoformat(),
            'reason': 'No more data can be generated' if start_date is None else 'Data generation is possible'
        }
