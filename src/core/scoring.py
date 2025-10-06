"""
Scoring algorithms for risk assessment questions.

This module contains all the scoring functions used to calculate
risk scores based on user responses to assessment questions.
"""

from typing import Optional


def score_age(ans: Optional[str]) -> Optional[float]:
    """Score based on user's age."""
    age = int(ans) if ans is not None else 40
    if age < 30: return 85.0
    if age < 40: return 70.0
    if age < 50: return 55.0
    if age < 60: return 40.0
    return 25.0


def score_horizon(ans: Optional[str]) -> Optional[float]:
    """Score based on investment time horizon."""
    yrs = int(ans) if ans is not None else 5
    if yrs >= 10: return 85.0
    if yrs >= 5:  return 65.0
    if yrs >= 2:  return 45.0
    return 25.0


def score_emergency_months(ans: Optional[str]) -> Optional[float]:
    """Score based on emergency fund size in months."""
    m = int(ans) if ans is not None else 3
    if m >= 6: return 85.0
    if m >= 3: return 70.0
    if m >= 1: return 50.0
    return 30.0


def score_dependents(ans: Optional[str]) -> Optional[float]:
    """Score based on number of dependents."""
    n = int(ans) if ans and ans.isdigit() else 2
    if n == 0: return 85.0
    if n <= 2: return 70.0
    if n <= 4: return 50.0
    return 35.0


def score_income_stability(ans: Optional[str]) -> Optional[float]:
    """Score based on income stability."""
    mc_map = {"choice_1": 30.0, "choice_2": 50.0, "choice_3": 70.0, "choice_4": 85.0}
    if ans in mc_map: return mc_map[ans]
    t = ans.lower() if ans else ""
    if "unstable" in t or "irregular" in t: return 35.0
    if "stable" in t or "secure" in t: return 75.0
    return 55.0


def score_experience(ans: Optional[str]) -> Optional[float]:
    """Score based on investment experience."""
    mc_map = {"choice_1": 25.0, "choice_2": 45.0, "choice_3": 65.0, "choice_4": 85.0}
    if ans in mc_map: return mc_map[ans]
    t = ans.lower() if ans else ""
    if "beginner" in t or "new" in t: return 30.0
    if "intermediate" in t or "some" in t: return 55.0
    if "advanced" in t or "expert" in t: return 80.0
    return 50.0


def score_loss_tolerance(ans: Optional[str]) -> Optional[float]:
    """Score based on loss tolerance."""
    mc_map = {"choice_1": 20.0, "choice_2": 40.0, "choice_3": 70.0, "choice_4": 90.0}
    if ans in mc_map: return mc_map[ans]
    t = ans.lower() if ans else ""
    if any(k in t for k in ["no loss", "avoid loss", "can't lose"]): return 20.0
    if any(k in t for k in ["some loss", "moderate", "dips"]): return 50.0
    if any(k in t for k in ["high risk", "aggressive", "volatility ok", "big swings"]): return 85.0
    return 50.0


def score_savings_rate(ans: Optional[str]) -> Optional[float]:
    """Score based on savings rate percentage."""
    v = float(ans) if ans is not None else 10.0
    if v >= 20: return 85.0
    if v >= 10: return 65.0
    if v >= 5:  return 50.0
    return 35.0


def score_debt_load(ans: Optional[str]) -> Optional[float]:
    """Score based on debt load relative to income."""
    mc_map = {"choice_1": 85.0, "choice_2": 65.0, "choice_3": 45.0, "choice_4": 30.0}
    if ans in mc_map: return mc_map[ans]
    t = ans.lower() if ans else ""
    if "no debt" in t or "debt-free" in t: return 85.0
    if "low" in t: return 65.0
    if "moderate" in t: return 45.0
    if "high" in t: return 30.0
    return 50.0


def score_liquidity_need(ans: Optional[str]) -> Optional[float]:
    """Score based on liquidity needs timing."""
    mc_map = {"choice_1": 30.0, "choice_2": 65.0, "choice_3": 85.0, "choice_4": 50.0}
    if ans in mc_map: return mc_map[ans]
    t = ans.lower() if ans else ""
    if any(k in t for k in [">3", "more than 3", "no liquidity need"]): return 85.0
    if any(k in t for k in ["1-3", "1–3", "within 3"]): return 65.0
    if any(k in t for k in ["<1", "less than 1", "soon"]): return 30.0
    return 50.0


def score_reaction_scenario(ans: Optional[str]) -> Optional[float]:
    """Score based on reaction to market volatility."""
    mc_map = {"choice_1": 25.0, "choice_2": 45.0, "choice_3": 70.0, "choice_4": 90.0}
    if ans in mc_map: return mc_map[ans]
    t = ans.lower() if ans else ""
    if "sell" in t: return 30.0
    if "buy more" in t or "buy" in t: return 85.0
    if "hold" in t or "stay" in t: return 70.0
    return 50.0


def score_objective(ans: Optional[str]) -> Optional[float]:
    """Score based on investment objective."""
    mc_map = {"choice_1": 35.0, "choice_2": 55.0, "choice_3": 70.0, "choice_4": 85.0}
    if ans in mc_map: return mc_map[ans]
    t = ans.lower() if ans else ""
    if "preserve" in t or "capital preservation" in t: return 35.0
    if "income" in t: return 55.0
    if "growth" in t and "income" in t: return 70.0
    if "growth" in t or "aggressive" in t: return 85.0
    return 55.0


def risk_bucket(score_pct: float) -> tuple[str, str]:
    """Convert risk score percentage to risk bucket and description."""
    if score_pct < 35:
        return ("Conservative",
                "Prefers capital preservation and lower volatility; accepts lower expected returns.")
    if score_pct < 55:
        return ("Moderately Conservative",
                "Comfortable with some volatility; leans toward income and balanced strategies.")
    if score_pct < 70:
        return ("Balanced",
                "Accepts meaningful ups and downs for moderate growth potential.")
    if score_pct < 85:
        return ("Moderately Aggressive",
                "Comfortable with higher volatility for higher long-term growth potential.")
    return ("Aggressive",
            "Seeks maximum growth; comfortable with substantial volatility and drawdowns.")
