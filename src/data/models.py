"""
Data models for financial goal tracking and risk assessment.

This module contains all the dataclasses and data structures used
throughout the application.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Protocol


class Step(Enum):
    """Assessment workflow steps."""
    ASSESSMENT = "assessment"
    GOAL_SETTING = "goal_setting"
    COMPLETE = "complete"


@dataclass
class Goal:
    """Represents a financial goal with target amount and date."""
    id: str
    name: str
    target_amount: float
    target_date: date
    start_amount: float = 0.0
    start_date: Optional[date] = None


@dataclass
class UserProfile:
    """User profile containing risk assessment and financial goal."""
    user_id: str
    risk_label: str  # e.g., "Conservative", "Balanced", "Aggressive"
    goal: Goal


@dataclass
class Account:
    """Financial account with balance information."""
    id: str
    type: str  # e.g., "checking", "savings", "investment"
    balance: float


@dataclass
class Transaction:
    """Financial transaction record."""
    id: str
    date: date
    amount: float  # positive = inflow, negative = outflow
    category: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ProgressSnapshot:
    """Snapshot of progress toward a financial goal."""
    user_id: str
    as_of: datetime
    current_amount: float  # how much counts toward the goal today
    progress_pct: float  # 0..100
    pacing_status: str  # "on_track" | "ahead" | "behind"
    pacing_detail: str  # human readable ("~1.5 weeks behind target pace")
    weekly_net_savings: float  # last 7 days net inflow (sum transactions)
    savings_rate_30d: float  # avg daily net inflow * 30 (or monthly proxy)
    target_amount: float
    target_date: date
    start_amount: float
    kpis: Dict[str, float]  # room for extras
    source_hash: str  # hash for idempotency


@dataclass
class Question:
    """Risk assessment question structure."""
    id: str
    user_question: str
    choices: List[str]
    system_prompt: str
    validator: Callable[[str], tuple[bool, Optional[str], Optional[str]]]
    scorer: Callable[[Optional[str]], Optional[float]]
    weight: float = 1.0
    enabled: bool = True
    display_text: Optional[str] = None  # Store human-readable answer text
    
    def render_prompt(self) -> str:
        """Render the question as a user prompt."""
        lines = [self.user_question.strip(), ""]
        if self.choices:
            for i, c in enumerate(self.choices, start=1):
                lines.append(f"{i}) {c}")
            lines.append("5) Other (type your own answer; any clear format is fine)")
            lines.append("")
            lines.append("Reply with 1–4 or write your own answer.")
        else:
            lines.append("Please type your answer directly.")
        return "\n".join(lines)


@dataclass
class GoalValidationResult:
    """Result of goal validation."""
    is_valid: bool
    target_amount: Optional[float] = None
    target_date: Optional[date] = None
    missing_fields: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)


# Protocol definitions
class GoalsProvider(Protocol):
    """Protocol for goal suggestion providers."""
    def generate(self, profile_label: str, context: Dict[str, Any]) -> List[str]: ...


class FinancialDataSource(Protocol):
    """Protocol for financial data sources."""
    def get_profile(self, user_id: str) -> UserProfile: ...
    def get_accounts(self, user_id: str) -> List[Account]: ...
    def get_transactions(self, user_id: str, since: Optional[date] = None) -> List[Transaction]: ...
