"""
Data source implementations for financial goal tracking.

This module implements the FinancialDataSource protocol with
mock data for Phase 1 development and testing.
"""

import json
import os
from datetime import date
from typing import Optional, List
from .models import FinancialDataSource, UserProfile, Account, Transaction, Goal


class MockDataSource:
    """Mock data source that reads from JSON files for Phase 1 development."""
    
    def __init__(self, data_root: str, user_id: str):
        """
        Initialize mock data source.
        
        Args:
            data_root: Root directory containing mock data
            user_id: User identifier
        """
        self.data_root = data_root
        self.user_id = user_id
        self.mock_data_path = os.path.join(data_root, "mock", user_id)
    
    def get_profile(self, user_id: str) -> UserProfile:
        """Load user profile from mock data."""
        profile_path = os.path.join(self.mock_data_path, "profile.json")
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Profile data not found at {profile_path}. "
                f"Please create mock data files in {self.mock_data_path}/"
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in profile data: {e}")
        
        # Parse goal data
        goal_data = data["goal"]
        goal = Goal(
            id=goal_data["id"],
            name=goal_data["name"],
            target_amount=float(goal_data["target_amount"]),
            target_date=date.fromisoformat(goal_data["target_date"]),
            start_amount=float(goal_data.get("start_amount", 0.0)),
            start_date=date.fromisoformat(goal_data["start_date"]) if goal_data.get("start_date") else None
        )
        
        return UserProfile(
            user_id=data["user_id"],
            risk_label=data["risk_label"],
            goal=goal
        )
    
    def get_accounts(self, user_id: str) -> List[Account]:
        """Load user accounts from mock data."""
        accounts_path = os.path.join(self.mock_data_path, "accounts.json")
        
        try:
            with open(accounts_path, 'r', encoding='utf-8') as f:
                accounts_data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Accounts data not found at {accounts_path}. "
                f"Please create mock data files in {self.mock_data_path}/"
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in accounts data: {e}")
        
        accounts = []
        for account_data in accounts_data:
            account = Account(
                id=account_data["id"],
                type=account_data["type"],
                balance=float(account_data["balance"])
            )
            accounts.append(account)
        
        return accounts
    
    def get_transactions(self, user_id: str, since: Optional[date] = None) -> List[Transaction]:
        """Load user transactions from mock data, optionally filtered by date."""
        transactions_path = os.path.join(self.mock_data_path, "transactions.json")
        
        try:
            with open(transactions_path, 'r', encoding='utf-8') as f:
                transactions_data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Transactions data not found at {transactions_path}. "
                f"Please create mock data files in {self.mock_data_path}/"
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in transactions data: {e}")
        
        transactions = []
        for txn_data in transactions_data:
            txn_date = date.fromisoformat(txn_data["date"])
            
            # Apply date filter if specified
            if since is not None and txn_date < since:
                continue
            
            transaction = Transaction(
                id=txn_data["id"],
                date=txn_date,
                amount=float(txn_data["amount"]),
                category=txn_data.get("category"),
                description=txn_data.get("description")
            )
            transactions.append(transaction)
        
        return transactions
