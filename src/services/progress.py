"""
Progress tracking calculations for financial goals.

This module contains the ProgressCalculator class and related utilities
for computing progress metrics toward financial goals.
"""

import hashlib
from datetime import date, datetime, timedelta
from typing import List, Tuple

from ..data.models import UserProfile, Account, Transaction, ProgressSnapshot, Goal


class ProgressCalculator:
    """Calculates progress metrics for financial goals."""
    
    @staticmethod
    def compute_current_amount(accounts: List[Account]) -> float:
        """
        Compute current amount available toward the goal.
        
        For Phase 1, simply sum balances of all accounts.
        Later we'll filter/tag which accounts count toward each goal.
        
        Args:
            accounts: List of user's financial accounts
            
        Returns:
            Total balance across all accounts
        """
        return sum(account.balance for account in accounts)
    
    @staticmethod
    def compute_weekly_net(transactions: List[Transaction], as_of: date) -> float:
        """
        Compute net savings over the last 7 days.
        
        Args:
            transactions: List of all transactions
            as_of: Reference date for the calculation
            
        Returns:
            Net amount (positive = savings, negative = spending) over last 7 days
        """
        cutoff_date = as_of - timedelta(days=7)
        weekly_transactions = [
            t for t in transactions 
            if t.date >= cutoff_date and t.date <= as_of
        ]
        return sum(t.amount for t in weekly_transactions)
    
    @staticmethod
    def compute_savings_rate_30d(transactions: List[Transaction], as_of: date) -> float:
        """
        Compute monthly savings rate based on last 30 days.
        
        Args:
            transactions: List of all transactions
            as_of: Reference date for the calculation
            
        Returns:
            Monthly net savings proxy (30-day net amount)
        """
        cutoff_date = as_of - timedelta(days=30)
        monthly_transactions = [
            t for t in transactions 
            if t.date >= cutoff_date and t.date <= as_of
        ]
        return sum(t.amount for t in monthly_transactions)
    
    @staticmethod
    def compute_pacing(goal: Goal, start_amount: float, current_amount: float, today: date) -> Tuple[str, str]:
        """
        Compute pacing status and detail for goal progress.
        
        Linear pacing: from start_amount at T0 to target_amount at goal.target_date.
        Compute expected fraction complete by time elapsed.
        Compare to actual fraction ((current - start) / (target - start)).
        Convert diff to "weeks ahead/behind".
        
        Args:
            goal: The financial goal
            start_amount: Starting amount for the goal
            current_amount: Current amount saved
            today: Current date
            
        Returns:
            Tuple of (status_code, friendly_detail)
        """
        # Calculate time progress
        total_days = (goal.target_date - today).days
        if total_days <= 0:
            # Goal date has passed
            if current_amount >= goal.target_amount:
                return "ahead", "Goal completed on time!"
            else:
                return "behind", "Goal date has passed - consider extending timeline"
        
        # Calculate expected progress based on time elapsed
        if goal.start_date is None:
            # Fallback: assume goal started 6 months ago if no start date
            goal_start_date = today - timedelta(days=180)
        else:
            goal_start_date = goal.start_date
        
        # Calculate actual time progress
        total_goal_days = (goal.target_date - goal_start_date).days
        if total_goal_days <= 0:
            time_progress = 1.0  # Goal time has passed
        else:
            elapsed_days = (today - goal_start_date).days
            time_progress = max(0.0, min(1.0, elapsed_days / total_goal_days))
        
        # Calculate actual progress
        total_needed = goal.target_amount - start_amount
        if total_needed <= 0:
            return "ahead", "Goal already achieved!"
        
        actual_progress = (current_amount - start_amount) / total_needed
        
        # Compare actual vs expected
        progress_diff = actual_progress - time_progress
        
        # Convert to weeks (rough approximation)
        weeks_diff = progress_diff * (total_days / 7)
        
        if abs(weeks_diff) < 0.5:
            return "on_track", "On track with target pace"
        elif weeks_diff > 0:
            weeks_ahead = int(weeks_diff)
            return "ahead", f"~{weeks_ahead} weeks ahead of target pace"
        else:
            weeks_behind = int(abs(weeks_diff))
            return "behind", f"~{weeks_behind} weeks behind target pace"
    
    @classmethod
    def snapshot(cls, profile: UserProfile, accounts: List[Account], 
                transactions: List[Transaction], now: datetime) -> ProgressSnapshot:
        """
        Create a progress snapshot for the given profile and data.
        
        Args:
            profile: User profile with goal information
            accounts: User's financial accounts
            transactions: User's transaction history
            now: Current timestamp
            
        Returns:
            Complete progress snapshot
        """
        today = now.date()
        current_amount = cls.compute_current_amount(accounts)
        weekly_net = cls.compute_weekly_net(transactions, today)
        savings_rate_30d = cls.compute_savings_rate_30d(transactions, today)
        
        # Calculate progress percentage
        goal = profile.goal
        total_needed = goal.target_amount - goal.start_amount
        if total_needed <= 0:
            progress_pct = 100.0
        else:
            progress_pct = max(0.0, min(100.0, 
                ((current_amount - goal.start_amount) / total_needed) * 100.0))
        
        # Calculate pacing
        pacing_status, pacing_detail = cls.compute_pacing(
            goal, goal.start_amount, current_amount, today)
        
        # Create source hash for idempotency
        source_data = f"{len(accounts)}_{len(transactions)}_{current_amount}"
        source_hash = hashlib.md5(source_data.encode()).hexdigest()[:8]
        
        # Additional KPIs
        kpis = {
            "total_accounts": len(accounts),
            "total_transactions": len(transactions),
            "avg_daily_net_7d": weekly_net / 7.0,
            "avg_daily_net_30d": savings_rate_30d / 30.0,
        }
        
        return ProgressSnapshot(
            user_id=profile.user_id,
            as_of=now,
            current_amount=current_amount,
            progress_pct=progress_pct,
            pacing_status=pacing_status,
            pacing_detail=pacing_detail,
            weekly_net_savings=weekly_net,
            savings_rate_30d=savings_rate_30d,
            target_amount=goal.target_amount,
            target_date=goal.target_date,
            start_amount=goal.start_amount,
            kpis=kpis,
            source_hash=source_hash
        )


def render_bar(pct: float, width: int = 30) -> str:
    """
    Render an ASCII progress bar.
    
    Args:
        pct: Progress percentage (0-100)
        width: Width of the progress bar in characters
        
    Returns:
        ASCII progress bar string
    """
    pct = max(0.0, min(100.0, pct))
    filled = int(round((pct / 100.0) * width))
    return "[" + "#" * filled + "-" * (width - filled) + f"] {pct:.1f}%"
