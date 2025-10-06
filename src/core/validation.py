"""
Validation functions for user input and goal validation.

This module contains all validation functions used to validate
user responses and financial goals.
"""

import re
from typing import Optional, Tuple


def text_to_number(text: str) -> Optional[int]:
    """Convert text like 'twenty eight' to 28, or extract numbers from mixed text."""
    text = text.strip().lower()
    
    # First try direct number extraction
    nums = re.findall(r"-?\d+", text)
    if nums:
        return int(nums[0])
    
    # Word-to-number mapping
    word_to_num = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
        'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
        'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
        'eighty': 80, 'ninety': 90, 'hundred': 100
    }
    
    # Handle compound numbers like "twenty eight"
    words = text.split()
    if len(words) >= 2:
        try:
            # Look for patterns like "twenty eight", "thirty five", etc.
            for i in range(len(words) - 1):
                if words[i] in ['twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']:
                    if words[i + 1] in word_to_num:
                        tens = word_to_num[words[i]]
                        ones = word_to_num[words[i + 1]]
                        if ones < 10:  # Only single digits for ones place
                            return tens + ones
        except:
            pass
    
    # Handle single words
    if text in word_to_num:
        return word_to_num[text]
    
    return None


def parse_int(s: str) -> Optional[int]:
    """Enhanced integer parsing that handles both numbers and text."""
    try:
        # First try text-to-number conversion
        text_num = text_to_number(s)
        if text_num is not None:
            return text_num
        
        # Fallback to regex extraction
        nums = re.findall(r"-?\d+", s.strip())
        return int(nums[0]) if nums else None
    except Exception:
        return None


def parse_float(s: str) -> Optional[float]:
    """Enhanced float parsing that handles both numbers and text."""
    try:
        # First try text-to-number conversion
        text_num = text_to_number(s)
        if text_num is not None:
            return float(text_num)
        
        # Fallback to regex extraction
        nums = re.findall(r"-?\d+(?:\.\d+)?", s.strip())
        return float(nums[0]) if nums else None
    except Exception:
        return None


def validate_age(text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate age input."""
    raw = text.strip()
    n = parse_int(raw)
    if n is None:
        return False, None, f'"{raw}" isn\'t a number. Please enter your age in whole years (0–120). Example: 34'
    if n < 0:
        return False, None, f"You entered {n}, which is negative. Age must be 0–120. Example: 34"
    if n > 120:
        return False, None, f"You entered {n}, which exceeds 120. Enter 0–120. Example: 34"
    return True, str(n), None


def validate_years(text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate years input."""
    raw = text.strip()
    n = parse_int(raw)
    if n is None:
        return False, None, f'"{raw}" isn\'t a number. Enter your time horizon in whole years (0–80). Example: 7'
    if n < 0:
        return False, None, f"You entered {n}, which is negative. Enter 0–80 years. Example: 7"
    if n > 80:
        return False, None, f"You entered {n}, which exceeds 80. Enter 0–80 years. Example: 7"
    return True, str(n), None


def validate_months(text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate months input."""
    raw = text.strip()
    n = parse_int(raw)
    if n is None:
        return False, None, f'"{raw}" isn\'t a number. Enter months (0–120). Example: 6'
    if n < 0:
        return False, None, f"You entered {n}, which is negative. Enter months 0–120. Example: 6"
    if n > 120:
        return False, None, f"You entered {n}, which exceeds 120. Enter months 0–120. Example: 6"
    return True, str(n), None


def validate_nonneg_int(text: str, upper: int = 20) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate non-negative integer input."""
    raw = text.strip()
    n = parse_int(raw)
    if n is None:
        return False, None, f'"{raw}" isn\'t a number. Enter a whole number between 0 and {upper}. Example: 2'
    if n < 0:
        return False, None, f"You entered {n}, which is negative. Enter 0–{upper}. Example: 2"
    if n > upper:
        return False, None, f"You entered {n}, which is above {upper}. Enter 0–{upper}. Example: 2"
    return True, str(n), None


def validate_pct(text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate percentage input."""
    raw = text.strip()
    v = parse_float(raw)
    if v is None:
        return False, None, "That's not a number. Enter a percentage between 0 and 100 (no % sign needed). Example: 15"
    if v < 0:
        return False, None, f"You entered {v}, which is negative. Enter 0–100. Example: 15"
    if v > 100:
        return False, None, f"You entered {v}, which exceeds 100. Enter 0–100. Example: 15"
    return True, f"{v}", None


def validate_mc_or_text(text: str, allowed: int = 4) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate multiple choice or text input."""
    t = text.strip()
    if t.isdigit():
        idx = int(t)
        if 1 <= idx <= allowed:
            return True, f"choice_{idx}", None
    if len(t) == 0:
        return False, None, "Please choose 1–4 or type a clear answer."
    return True, t, None


def validate_mc_or_text_with_display(text: str, choices: list[str], allowed: int = 4) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """Validate multiple choice or text input and return both normalized value and display text."""
    t = text.strip()
    if t.isdigit():
        idx = int(t)
        if 1 <= idx <= allowed:
            choice_text = choices[idx - 1] if idx <= len(choices) else f"Choice {idx}"
            return True, f"choice_{idx}", choice_text, None
    if len(t) == 0:
        return False, None, None, "Please choose 1–4 or type a clear answer."
    return True, t, t, None  # Custom text - use as both normalized and display


def is_question(text: str) -> bool:
    """Check if text is a question."""
    if not text: return False
    t = text.strip().lower()
    if "?" in t: return True
    starters = (
        "what is", "what's", "explain", "how do", "how does", "why ",
        "when ", "where ", "which ", "define ", "difference between",
        "tell me about", "meaning of", "clarify "
    )
    return any(t.startswith(s) for s in starters)


def is_continuation_request(text: str) -> bool:
    """Check if user wants to continue after getting an explanation."""
    if not text: return False
    t = text.strip().lower()
    continuation_phrases = (
        "yes", "ok", "okay", "continue", "proceed", "go on", "next",
        "yes continue", "ok continue", "let's continue", "please continue",
        "what are the options", "show me the options", "what are my choices",
        "i understand", "got it", "clear", "now i know", "i see"
    )
    return any(t.startswith(phrase) for phrase in continuation_phrases)


def is_deletion_request(text: str) -> bool:
    """Check if user wants to delete goals."""
    if not text: return False
    t = text.strip().lower()
    deletion_indicators = (
        "delete", "remove", "drop", "cancel", "unselect", "clear"
    )
    return any(indicator in t for indicator in deletion_indicators)


def extract_goal_numbers(text: str) -> list[int]:
    """Extract goal numbers from deletion requests like 'delete 1,3' or 'remove goals 1 and 3'."""
    # Find all numbers in the text
    numbers = re.findall(r'\d+', text)
    return [int(n) for n in numbers if int(n) > 0]


def is_explanation_request(text: str) -> bool:
    """Check if user wants to explain a specific goal."""
    if not text: return False
    t = text.strip().lower()
    explanation_indicators = (
        "explain", "elaborate", "more info", "details", "tell me about", 
        "what is", "describe", "clarify", "break down"
    )
    return any(indicator in t for indicator in explanation_indicators)


def extract_explanation_goal_number(text: str) -> Optional[int]:
    """Extract goal number from explanation requests like 'explain goal 12' or 'elaborate on 16'."""
    # Find numbers in the text
    numbers = re.findall(r'\d+', text)
    if numbers:
        return int(numbers[0])  # Return the first number found
    return None


def is_done_phrase(text: str) -> bool:
    """Check if text indicates user is done with goal selection."""
    t = (text or "").strip().lower()
    patterns = [
    r"\bdone\b", r"\bfinish\b", r"\bfinished\b", r"\bend\b",
    r"\bi'?m done\b", r"\bthat'?s it\b", r"\ball set\b",
    r"\bno more\b", r"\bstop\b", r"\bquit\b", r"\bexit\b",
    r"\bthat's all\b", r"\benough\b", r"\bno further goals\b"
    ]
    return any(re.search(p, t) for p in patterns)
