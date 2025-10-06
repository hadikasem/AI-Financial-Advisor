"""
LLM integration service for risk assessment and recommendations.

This module provides LLM functionality for generating goal suggestions
and financial recommendations.
"""

from typing import Callable, Dict, List, Any
from datetime import datetime, timezone


# LLM Configuration
OLLAMA_MODEL = "gpt-oss:20b"

LLM_UNAVAILABLE_MSG = (
    "⚠️ LLM is currently unavailable. The assessment is paused. "
    "Please ensure your LLM is running (e.g., `ollama serve` and model loaded) "
    "and try again by sending 'retry'."
)


def call_llm(messages: List[Dict[str, str]]) -> str:
    """Call the LLM with the given messages."""
    import ollama  # strict: raises if not available  # pyright: ignore[reportMissingImports]
    res = ollama.chat(model=OLLAMA_MODEL, messages=messages)
    return res["message"]["content"]


class LiveLLMGoalsProvider:
    """Goal suggestion provider using LLM."""
    
    def __init__(self, llm_fn: Callable[[List[Dict[str, str]]], str] = call_llm):
        self.llm_fn = llm_fn
    
    def generate(self, profile_label: str, context: Dict[str, Any]) -> List[str]:
        """Generate goal suggestions based on user profile and context."""
        now = datetime.now(timezone.utc)
        as_of = now.strftime("%B %Y")
        sys = {"role": "system", "content":
               "You are a financial planning assistant. Suggest exactly 10 "
               "concise, specific, time-aware goal options suitable for the user. "
               "Be concrete: include amounts, durations or a month/year where relevant. "
               "If proposing assets/sectors, add the current month/year and a brief risk note. "
               "Do NOT guarantee returns; use cautious phrasing. "
               "Output as 10 separate lines; no numbering, no explanations."}
        usr = {"role": "user", "content":
               f"As of {as_of}, propose 10 goal options for a user with profile: {profile_label}.\n"
               f"Context from assessment: {context}\n"
               "Only list the goal titles, one per line."}
        text = self.llm_fn([sys, usr]).strip()
        lines = [l.strip("-• \n\r\t") for l in text.splitlines() if l.strip()]
        if len(lines) < 10:
            raise RuntimeError("LLM did not return enough goal options.")
        out: List[str] = []
        for l in lines:
            if l and l not in out:
                out.append(l)
            if len(out) == 10:
                break
        if len(out) < 10:
            raise RuntimeError("LLM returned insufficient distinct goal options.")
        return out


class RecommendationProvider:
    """Provides financial recommendations using LLM only."""
    
    def __init__(self, llm_fn: Callable[[List[Dict[str, str]]], str] = call_llm):
        self.llm_fn = llm_fn
        self.llm_available = self._check_llm_availability()
        if not self.llm_available:
            raise RuntimeError("LLM is not available. Cannot generate recommendations without LLM access.")
    
    def _check_llm_availability(self) -> bool:
        """Check if LLM is available by trying to call it."""
        try:
            _ = self.llm_fn([{"role":"system","content":"Reply with OK only."},{"role":"user","content":"OK?"}]).strip()
            return True
        except Exception:
            return False
    
    def generate(self, profile, snap, top_categories: List[str] = None, max_items: int = 5) -> List[str]:
        """
        Generate financial recommendations based on user profile and progress.
        
        Args:
            profile: User profile with risk assessment and goal
            snap: Current progress snapshot
            top_categories: Optional list of spending categories to focus on
            max_items: Maximum number of recommendations to return
            
        Returns:
            List of recommendation strings
            
        Raises:
            RuntimeError: If LLM is not available
        """
        if not self.llm_available:
            raise RuntimeError("LLM is not available. Cannot generate recommendations.")
        
        return self._generate_llm_recommendations(profile, snap, max_items)
    
    def _generate_llm_recommendations(self, profile, snap, max_items: int) -> List[str]:
        """Generate recommendations using LLM."""
        try:
            import json
            # Prepare compact JSON for LLM
            snapshot_data = {
                "risk_label": profile.risk_label,
                "target_amount": snap.target_amount,
                "target_date": snap.target_date.isoformat(),
                "progress_pct": round(snap.progress_pct, 1),
                "weekly_net_savings": round(snap.weekly_net_savings, 2),
                "savings_rate_30d": round(snap.savings_rate_30d, 2),
                "pacing_detail": snap.pacing_detail,
                "current_amount": round(snap.current_amount, 2),
                "pacing_status": snap.pacing_status
            }
            
            system_prompt = (
                "You are a concise financial coach. Based on the snapshot, "
                "give 3-5 actionable, safe, specific suggestions (amounts/percentages/dates "
                "where possible). No promises, no market timing. Each item ≤ 2 lines."
            )
            
            user_content = f"Financial snapshot: {json.dumps(snapshot_data, indent=2)}"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            response = self.llm_fn(messages)
            return self._parse_llm_response(response, max_items)
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate LLM recommendations: {e}")
    
    def _parse_llm_response(self, response: str, max_items: int) -> List[str]:
        """
        Parse LLM response into list of recommendations.
        
        Args:
            response: Raw LLM response text
            max_items: Maximum number of items to return
            
        Returns:
            List of parsed recommendation strings
        """
        lines = response.strip().split('\n')
        recommendations = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for lines starting with numbers or "- "
            if (line[0].isdigit() and ('.' in line[:3] or ')' in line[:3])) or line.startswith('- '):
                # Clean up the line
                if line[0].isdigit():
                    # Remove numbering (e.g., "1) " or "1. ")
                    if '. ' in line[:3]:
                        line = line.split('. ', 1)[1]
                    elif ') ' in line[:3]:
                        line = line.split(') ', 1)[1]
                elif line.startswith('- '):
                    line = line[2:]
                
                if line.strip():
                    recommendations.append(line.strip())
                
                if len(recommendations) >= max_items:
                    break
        
        # If parsing failed, raise error instead of fallback
        if not recommendations:
            raise RuntimeError("Failed to parse LLM response into recommendations")
        
        return recommendations[:max_items]
