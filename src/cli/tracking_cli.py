"""
Command-line interface for goal tracking.

This module provides the CLI for tracking progress toward financial goals.
"""

import argparse
import json
import os
import re
import sys
from datetime import date, datetime
from typing import Optional, List, Dict, Any

from ..data.sources import MockDataSource
from ..data.models import UserProfile, Goal
from ..services.progress import ProgressCalculator, render_bar
from ..services.llm import RecommendationProvider


def load_goals_from_assessment(assessment_file: str) -> List[Dict[str, Any]]:
    """Load goals from a risk assessment JSON file."""
    with open(assessment_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    goals = []
    for goal_data in data['goals']['selected_goals']:
        if goal_data['status'] == 'active':
            goals.append(goal_data)
    
    return goals


def extract_goal_info(goal_text: str) -> Dict[str, Any]:
    """Extract target amount and date from goal text using improved patterns."""
    # Extract amount using improved patterns
    amount_patterns = [
        r'\$([0-9,]+(?:\.[0-9]{2})?)',  # $1,000.00 or $1000
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*dollars?',  # 1,000 dollars
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*USD',  # 1,000 USD
        r'(\d+(?:\.\d{2})?)\$',  # 4000$ (no space) - put this before the space version
        r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*\$',  # 2500 $ or 1,000 $ (with space)
    ]
    
    target_amount = None
    for pattern in amount_patterns:
        match = re.search(pattern, goal_text, re.IGNORECASE)
        if match:
            try:
                amount_str = match.group(1).replace(',', '')
                target_amount = float(amount_str)
                break
            except ValueError:
                continue
    
    # Look for word-based amounts
    if target_amount is None:
        word_amounts = _extract_word_amounts(goal_text)
        if word_amounts:
            target_amount = word_amounts
    
    # Default fallback
    if target_amount is None:
        target_amount = 10000
    
    # Extract date using improved patterns
    today = date.today()
    
    # Look for specific date patterns
    date_patterns = [
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})',  # Abbreviated months
        r'(\d{1,2})/(\d{1,2})/(\d{4})',
        r'(\d{4})-(\d{1,2})-(\d{1,2})',
        r'(?<!\d)(\d{4})(?!\d|\s*\$)',  # Year only (like "2028") - avoid matching amounts
    ]
    
    month_map = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
        'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9,
        'oct': 10, 'nov': 11, 'dec': 12
    }
    
    target_date = None
    for pattern in date_patterns:
        match = re.search(pattern, goal_text, re.IGNORECASE)
        if match:
            try:
                if len(match.groups()) == 2:  # Month Year format
                    month_name = match.group(1).lower()
                    year = int(match.group(2))
                    month = month_map.get(month_name)
                    if month:
                        target_date = date(year, month, 1)
                        break
                elif len(match.groups()) == 3:  # MM/DD/YYYY or YYYY-MM-DD format
                    if '/' in match.group(0):  # MM/DD/YYYY
                        month, day, year = map(int, match.groups())
                    else:  # YYYY-MM-DD
                        year, month, day = map(int, match.groups())
                    target_date = date(year, month, day)
                    break
                elif len(match.groups()) == 1:  # Year only format
                    year = int(match.group(1))
                    # Use current month and day for year-only dates
                    target_date = date(year, today.month, today.day)
                    break
            except (ValueError, KeyError):
                continue
    
    # Look for relative time patterns
    if target_date is None:
        target_date = _extract_relative_date(goal_text, today)
    
    # Default fallback
    if target_date is None:
        target_date = date(2026, 12, 31)
    
    return {
        "target_amount": target_amount,
        "target_date": target_date.isoformat()
    }


def _extract_word_amounts(goal_text: str) -> Optional[float]:
    """Extract amounts written in words."""
    text = goal_text.lower()
    
    # Word-to-number mapping for common amounts
    word_to_num = {
        'thousand': 1000, 'k': 1000,
        'million': 1000000, 'm': 1000000,
        'billion': 1000000000, 'b': 1000000000,
        'hundred': 100,
        'ten': 10, 'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50,
        'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90
    }
    
    # Look for patterns like "twenty thousand", "5 million", etc.
    patterns = [
        r'(\d+)\s*(thousand|k|million|m|billion|b)',
        r'(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)\s*(thousand|k)',
        r'(ten|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)\s*(thousand|k)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                if match.group(1).isdigit():
                    number = int(match.group(1))
                else:
                    number = word_to_num.get(match.group(1), 0)
                
                multiplier = word_to_num.get(match.group(2), 1)
                return float(number * multiplier)
            except (ValueError, KeyError):
                continue
    
    return None


def _extract_relative_date(goal_text: str, base_date: date) -> Optional[date]:
    """Extract relative dates like 'in 2 years', 'next year', etc."""
    text = goal_text.lower()
    
    # Look for patterns like "in X years", "in X months", "by next year"
    patterns = [
        r'in\s+(\d+)\s+years?',
        r'in\s+(\d+)\s+months?',
        r'by\s+next\s+year',
        r'by\s+(\d{4})',
        r'in\s+(\d{4})',  # "in 2025" format
        r'within\s+(\d+)\s+years?',
        r'within\s+(\d+)\s+months?',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                if 'next year' in text:
                    return date(base_date.year + 1, base_date.month, base_date.day)
                elif 'years' in text:
                    years = int(match.group(1))
                    return date(base_date.year + years, base_date.month, base_date.day)
                elif 'months' in text:
                    months = int(match.group(1))
                    # Simple month addition (not perfect but good enough)
                    new_year = base_date.year + (months // 12)
                    new_month = base_date.month + (months % 12)
                    if new_month > 12:
                        new_year += 1
                        new_month -= 12
                    return date(new_year, new_month, base_date.day)
                elif 'by' in text and match.group(1).isdigit():
                    year = int(match.group(1))
                    return date(year, base_date.month, base_date.day)
                elif 'in' in text and match.group(1).isdigit() and len(match.group(1)) == 4:
                    # "in 2025" format
                    year = int(match.group(1))
                    return date(year, base_date.month, base_date.day)
            except (ValueError, OverflowError):
                continue
    
    return None


def create_goal_profile(goal_data: Dict[str, Any], user_id: str, risk_label: str) -> Dict[str, Any]:
    """Create a profile for a specific goal."""
    # Extract target amount and date from goal text using improved parsing
    goal_text = goal_data['text']
    goal_info = extract_goal_info(goal_text)
    
    target_amount = goal_info['target_amount']
    target_date = date.fromisoformat(goal_info['target_date'])
    
    return {
        "user_id": user_id,
        "risk_label": risk_label,
        "goal": {
            "id": goal_data['id'],
            "name": goal_text,
            "target_amount": target_amount,
            "target_date": target_date.isoformat(),
            "start_amount": 0.0
        }
    }


def save_snapshot(snapshot, output_path: str) -> None:
    """Save progress snapshot to JSON file."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Convert snapshot to dictionary for JSON serialization
    snapshot_dict = {
        "user_id": snapshot.user_id,
        "as_of": snapshot.as_of.isoformat(),
        "current_amount": snapshot.current_amount,
        "progress_pct": snapshot.progress_pct,
        "pacing_status": snapshot.pacing_status,
        "pacing_detail": snapshot.pacing_detail,
        "weekly_net_savings": snapshot.weekly_net_savings,
        "savings_rate_30d": snapshot.savings_rate_30d,
        "target_amount": snapshot.target_amount,
        "target_date": snapshot.target_date.isoformat(),
        "start_amount": snapshot.start_amount,
        "kpis": snapshot.kpis,
        "source_hash": snapshot.source_hash
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(snapshot_dict, f, indent=2, ensure_ascii=False)


def print_dashboard(profile: UserProfile, snapshot, recommendations: List[str], goal_name: str = None) -> None:
    """Print a compact CLI dashboard with progress and recommendations."""
    print(f"\n{'='*60}")
    if goal_name:
        print(f"Financial Goal Tracker - {profile.user_id} - {goal_name}")
    else:
        print(f"Financial Goal Tracker - {profile.user_id}")
    print(f"Goal: {profile.goal.name}")
    print(f"Risk Profile: {profile.risk_label}")
    print(f"{'='*60}")
    
    # Progress bar
    print(f"\nProgress: {render_bar(snapshot.progress_pct)}")
    
    # KPIs
    print(f"\nKey Metrics:")
    print(f"  Current Amount:    ${snapshot.current_amount:,.2f}")
    print(f"  Target Amount:     ${snapshot.target_amount:,.2f}")
    print(f"  Target Date:       {snapshot.target_date}")
    print(f"  Pacing Status:     {snapshot.pacing_status.title()}")
    print(f"  Pacing Detail:     {snapshot.pacing_detail}")
    print(f"  Weekly Net:        ${snapshot.weekly_net_savings:,.2f}")
    print(f"  30d Savings Rate:  ${snapshot.savings_rate_30d:,.2f}")
    
    # Recommendations
    if recommendations:
        print(f"\nRecommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}) {rec}")
    
    print(f"\n{'='*60}")


def track_single_goal(user_id: str, data_root: str, since_date: Optional[date] = None, 
                     output_path: Optional[str] = None) -> None:
    """Track progress for a single goal using mock data."""
    print(f"Single Goal Financial Tracker - {user_id}")
    print("=" * 60)
    
    try:
        # Initialize data source
        data_source = MockDataSource(data_root, user_id)
        
        # Load data
        print(f"Loading data for user: {user_id}")
        profile = data_source.get_profile(user_id)
        accounts = data_source.get_accounts(user_id)
        transactions = data_source.get_transactions(user_id, since_date)
        
        print(f"Loaded {len(accounts)} accounts and {len(transactions)} transactions")
        
        # Calculate progress
        now = datetime.now()
        snapshot = ProgressCalculator.snapshot(profile, accounts, transactions, now)
        
        # Generate output path if not specified
        if output_path:
            final_output_path = output_path
        else:
            timestamp = now.strftime("%Y-%m-%dT%H-%M-%S")
            final_output_path = os.path.join(
                data_root, "data", "users", user_id, 
                "progress", f"{timestamp}.json"
            )
        
        # Save snapshot
        save_snapshot(snapshot, final_output_path)
        print(f"Snapshot saved to: {final_output_path}")
        
        # Generate recommendations
        try:
            recommender = RecommendationProvider()
            recommendations = recommender.generate(profile, snapshot)
        except Exception as e:
            print(f"Error: Could not generate recommendations: {e}")
            sys.exit(1)
        
        # Print dashboard
        print_dashboard(profile, snapshot, recommendations)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nTo create mock data, place the following files:")
        print(f"  {data_root}/mock_data/{user_id}/profile.json")
        print(f"  {data_root}/mock_data/{user_id}/accounts.json")
        print(f"  {data_root}/mock_data/{user_id}/transactions.json")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def track_multiple_goals(assessment_file: str, user_id: str, data_root: str = ".") -> None:
    """Track progress for all goals from a risk assessment."""
    print(f"Multi-Goal Financial Tracker - {user_id}")
    print("=" * 60)
    
    # Load goals from assessment
    try:
        goals = load_goals_from_assessment(assessment_file)
        print(f"Found {len(goals)} active goals from assessment")
    except Exception as e:
        print(f"Error loading assessment file: {e}")
        return
    
    # Load user data
    data_source = MockDataSource(data_root, user_id)
    try:
        accounts = data_source.get_accounts(user_id)
        transactions = data_source.get_transactions(user_id)
        print(f"Loaded {len(accounts)} accounts and {len(transactions)} transactions")
    except Exception as e:
        print(f"Error loading financial data: {e}")
        return
    
    # Initialize recommender
    try:
        recommender = RecommendationProvider()
    except Exception as e:
        print(f"Error: LLM not available: {e}")
        sys.exit(1)
    
    now = datetime.now()
    
    for i, goal_data in enumerate(goals, 1):
        print(f"\n{'='*60}")
        print(f"GOAL {i}: {goal_data['text']}")
        print(f"{'='*60}")
        
        # Create profile for this goal
        risk_label = "Balanced"  # Default, could be loaded from assessment
        profile_data = create_goal_profile(goal_data, user_id, risk_label)
        
        # Create a temporary profile object
        goal_obj = Goal(
            id=profile_data['goal']['id'],
            name=profile_data['goal']['name'],
            target_amount=profile_data['goal']['target_amount'],
            target_date=date.fromisoformat(profile_data['goal']['target_date']),
            start_amount=profile_data['goal']['start_amount']
        )
        profile = UserProfile(
            user_id=profile_data['user_id'],
            risk_label=profile_data['risk_label'],
            goal=goal_obj
        )
        
        # Calculate progress
        snapshot = ProgressCalculator.snapshot(profile, accounts, transactions, now)
        
        # Display progress
        print(f"Progress: {render_bar(snapshot.progress_pct)}")
        print(f"\nKey Metrics:")
        print(f"  Current Amount:    ${snapshot.current_amount:,.2f}")
        print(f"  Target Amount:     ${snapshot.target_amount:,.2f}")
        print(f"  Target Date:       {snapshot.target_date}")
        print(f"  Pacing Status:     {snapshot.pacing_status.title()}")
        print(f"  Pacing Detail:     {snapshot.pacing_detail}")
        print(f"  Weekly Net:        ${snapshot.weekly_net_savings:,.2f}")
        print(f"  30d Savings Rate:  ${snapshot.savings_rate_30d:,.2f}")
        
        # Generate recommendations
        try:
            recommendations = recommender.generate(profile, snapshot)
            if recommendations:
                print(f"\nRecommendations:")
                for j, rec in enumerate(recommendations, 1):
                    print(f"  {j}) {rec}")
        except Exception as e:
            print(f"\nRecommendations: (Error generating: {e})")
    
    print(f"\n{'='*60}")
    print("Multi-Goal Tracking Complete")
    print(f"{'='*60}")


def main():
    """Main CLI entry point for unified goal tracking."""
    parser = argparse.ArgumentParser(
        description="Unified financial goal tracking system supporting both single and multiple goals"
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--single", 
        action="store_true", 
        help="Track a single goal using mock data"
    )
    mode_group.add_argument(
        "--multi", 
        action="store_true", 
        help="Track multiple goals from risk assessment file"
    )
    
    # Common arguments
    parser.add_argument(
        "--user-id", 
        required=True, 
        help="User identifier"
    )
    parser.add_argument(
        "--data-root", 
        default="./data", 
        help="Root directory containing data (default: ./data)"
    )
    parser.add_argument(
        "--since", 
        type=str,
        help="ISO date to limit transactions window (e.g., 2024-01-01)"
    )
    parser.add_argument(
        "--out", 
        type=str,
        help="Path to write snapshot JSON (single mode only)"
    )
    
    # Multi-mode specific arguments
    parser.add_argument(
        "--assessment-file", 
        type=str,
        help="Path to risk assessment JSON file (required for multi mode)"
    )
    
    args = parser.parse_args()
    
    # Parse since date if provided
    since_date = None
    if args.since:
        since_date = date.fromisoformat(args.since)
    
    # Validate arguments based on mode
    if args.multi and not args.assessment_file:
        print("Error: --assessment-file is required for multi mode")
        sys.exit(1)
    
    if args.single and args.assessment_file:
        print("Warning: --assessment-file is ignored in single mode")
    
    if args.out and args.multi:
        print("Warning: --out is ignored in multi mode")
    
    # Execute based on mode
    if args.single:
        track_single_goal(
            user_id=args.user_id,
            data_root=args.data_root,
            since_date=since_date,
            output_path=args.out
        )
    elif args.multi:
        track_multiple_goals(
            assessment_file=args.assessment_file,
            user_id=args.user_id,
            data_root=args.data_root
        )


if __name__ == "__main__":
    main()
