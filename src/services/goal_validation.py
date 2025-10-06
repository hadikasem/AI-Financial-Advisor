"""
Goal validation service for financial goal tracking.

This module provides validation for financial goals to ensure they have
complete target amount and target date information before being marked as active.
"""

import re
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple, Any

from ..data.models import GoalValidationResult


class GoalValidator:
    """Validates financial goals for completeness and logical consistency."""
    
    def __init__(self):
        """Initialize the goal validator."""
        self.min_amount = 100.0  # Minimum reasonable goal amount
        self.max_amount = 10000000.0  # Maximum reasonable goal amount
        self.min_years = 0.1  # Minimum 1.2 months
        self.max_years = 50.0  # Maximum 50 years
    
    def validate_goal(self, goal_text: str) -> GoalValidationResult:
        """
        Validate a financial goal for completeness and logical consistency.
        
        Args:
            goal_text: The goal text to validate
            
        Returns:
            GoalValidationResult with validation status and extracted information
        """
        result = GoalValidationResult(is_valid=True)
        
        # Extract target amount
        amount_result = self._extract_target_amount(goal_text)
        if amount_result is None:
            result.missing_fields.append("target_amount")
            result.is_valid = False
        else:
            result.target_amount = amount_result
            # Validate amount is reasonable
            if not self._is_reasonable_amount(amount_result):
                result.validation_errors.append(f"Target amount ${amount_result:,.2f} is not reasonable (should be between ${self.min_amount:,.2f} and ${self.max_amount:,.2f})")
                result.is_valid = False
        
        # Extract target date
        date_result = self._extract_target_date(goal_text)
        if date_result is None:
            result.missing_fields.append("target_date")
            result.is_valid = False
        else:
            result.target_date = date_result
            # Validate date is reasonable
            if not self._is_reasonable_date(date_result):
                result.validation_errors.append(f"Target date {date_result} is not reasonable (should be between 1 month and 50 years from now)")
                result.is_valid = False
        
        # If both amount and date are present, validate they make sense together
        if result.target_amount and result.target_date:
            if not self._validate_amount_date_consistency(result.target_amount, result.target_date):
                result.validation_errors.append("Target amount and date combination seems unrealistic (very high amount in very short time)")
                result.is_valid = False
        
        return result
    
    def _extract_target_amount(self, goal_text: str) -> Optional[float]:
        """
        Extract target amount from goal text.
        
        Args:
            goal_text: The goal text to parse
            
        Returns:
            Extracted amount as float, or None if not found
        """
        # Look for $X,XXX patterns
        amount_patterns = [
            r'\$([0-9,]+(?:\.[0-9]{2})?)',  # $1,000.00 or $1000
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*dollars?',  # 1,000 dollars
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*USD',  # 1,000 USD
            r'(\d+(?:\.\d{2})?)\$',  # 4000$ (no space) - put this before the space version
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*\$',  # 2500 $ or 1,000 $ (with space)
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, goal_text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '')
                    return float(amount_str)
                except ValueError:
                    continue
        
        # Look for word-based amounts
        word_amounts = self._extract_word_amounts(goal_text)
        if word_amounts:
            return word_amounts
        
        return None
    
    def _extract_word_amounts(self, goal_text: str) -> Optional[float]:
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
    
    def _extract_target_date(self, goal_text: str) -> Optional[date]:
        """
        Extract target date from goal text.
        
        Args:
            goal_text: The goal text to parse
            
        Returns:
            Extracted date as date object, or None if not found
        """
        today = date.today()
        
        # Look for specific date patterns
        date_patterns = [
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})',  # Abbreviated months
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
        ]
        
        month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
            'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9,
            'oct': 10, 'nov': 11, 'dec': 12
        }
        
        for pattern in date_patterns:
            match = re.search(pattern, goal_text, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) == 2:  # Month Year format
                        month_name = match.group(1).lower()
                        year = int(match.group(2))
                        month = month_map.get(month_name)
                        if month:
                            return date(year, month, 1)
                    elif len(match.groups()) == 3:  # MM/DD/YYYY or YYYY-MM-DD format
                        if '/' in match.group(0):  # MM/DD/YYYY
                            month, day, year = map(int, match.groups())
                        else:  # YYYY-MM-DD
                            year, month, day = map(int, match.groups())
                        return date(year, month, day)
                except (ValueError, KeyError):
                    continue
        
        # Look for relative time patterns
        relative_date = self._extract_relative_date(goal_text, today)
        if relative_date:
            return relative_date
        
        return None
    
    def _extract_relative_date(self, goal_text: str, base_date: date) -> Optional[date]:
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
    
    def _is_reasonable_amount(self, amount: float) -> bool:
        """Check if the amount is within reasonable bounds."""
        return self.min_amount <= amount <= self.max_amount
    
    def _is_reasonable_date(self, target_date: date) -> bool:
        """Check if the date is within reasonable bounds."""
        today = date.today()
        years_diff = (target_date - today).days / 365.25
        
        return self.min_years <= years_diff <= self.max_years
    
    def _validate_amount_date_consistency(self, amount: float, target_date: date) -> bool:
        """Validate that amount and date make sense together."""
        today = date.today()
        years_diff = (target_date - today).days / 365.25
        
        # Very rough heuristic: if saving more than $100k per year, it might be unrealistic
        if years_diff > 0:
            annual_savings_needed = amount / years_diff
            return annual_savings_needed <= 200000  # $200k per year max
        
        return True
    
    def generate_single_field_prompt(self, goal_text: str, validation_result: GoalValidationResult) -> str:
        """
        Generate a prompt asking for only the first missing field.
        
        Args:
            goal_text: The original goal text
            validation_result: The validation result
            
        Returns:
            Formatted prompt asking for the first missing field only
        """
        if validation_result.is_valid:
            return f"✅ Goal validated: '{goal_text}' with target amount ${validation_result.target_amount:,.2f} and target date {validation_result.target_date}"
        
        # Ask for the first missing field only
        if "target_amount" in validation_result.missing_fields:
            return (
                f"❌ Your goal '{goal_text}' needs a target amount.\n\n"
                f"💰 Please specify how much you want to save (e.g., $4,000, 5k, 1 million, 2500$).\n"
                f"Examples: $20,000, 50k, 1.5 million, 5000$, 10,000 dollars"
            )
        elif "target_date" in validation_result.missing_fields:
            return (
                f"❌ Your goal '{goal_text}' needs a target date.\n\n"
                f"📅 Please specify when you want to achieve this goal (e.g., Dec 2026, June 2027, in 2 years).\n"
                f"Examples: December 2026, June 2027, in 3 years, by 2025, next year"
            )
        
        # If there are validation errors but no missing fields
        if validation_result.validation_errors:
            error_msg = "\n".join(f"• {error}" for error in validation_result.validation_errors)
            return f"❌ Your goal '{goal_text}' has some issues:\n\n{error_msg}\n\nPlease provide a valid goal."
        
        return f"❌ Your goal '{goal_text}' is missing required information."
    
    def generate_validation_prompt(self, goal_text: str, validation_result: GoalValidationResult) -> str:
        """
        Generate a user-friendly prompt asking for missing information.
        
        Args:
            goal_text: The original goal text
            validation_result: The validation result
            
        Returns:
            Formatted prompt asking for missing information
        """
        if validation_result.is_valid:
            return f"✅ Goal validated: '{goal_text}' with target amount ${validation_result.target_amount:,.2f} and target date {validation_result.target_date}"
        
        prompt_parts = [f"❌ Your goal '{goal_text}' is missing required information:"]
        
        if "target_amount" in validation_result.missing_fields:
            prompt_parts.append("• Please specify the target amount (e.g., $20,000, 50k, 1 million)")
        
        if "target_date" in validation_result.missing_fields:
            prompt_parts.append("• Please specify the target date (e.g., June 2027, in 2 years, by 2025)")
        
        if validation_result.validation_errors:
            prompt_parts.append("\n⚠️ Additional issues:")
            for error in validation_result.validation_errors:
                prompt_parts.append(f"• {error}")
        
        prompt_parts.append("\nPlease provide the missing information to complete your goal.")
        
        return "\n".join(prompt_parts)
    
    def validate_goals_batch(self, goals: List[str]) -> Dict[str, GoalValidationResult]:
        """
        Validate multiple goals at once.
        
        Args:
            goals: List of goal texts to validate
            
        Returns:
            Dictionary mapping goal text to validation result
        """
        results = {}
        for goal in goals:
            results[goal] = self.validate_goal(goal)
        return results
