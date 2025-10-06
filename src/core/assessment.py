"""
Risk assessment core logic and agent implementation.

This module contains the main RiskAssessmentAgent class and related
functionality for conducting financial risk assessments.
"""

import json
import os
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Callable, Dict, List, Optional, Tuple, Any

from ..data.models import (
    Step, Question, GoalsProvider, 
    GoalValidationResult, UserProfile, Goal
)
from ..core.validation import (
    validate_age, validate_years, validate_months, validate_pct,
    validate_nonneg_int, validate_mc_or_text_with_display,
    is_question, is_continuation_request, is_deletion_request,
    extract_goal_numbers, is_explanation_request, extract_explanation_goal_number,
    is_done_phrase
)
from ..core.scoring import (
    score_age, score_horizon, score_emergency_months, score_dependents,
    score_income_stability, score_experience, score_loss_tolerance,
    score_savings_rate, score_debt_load, score_liquidity_need,
    score_reaction_scenario, score_objective, risk_bucket
)
from ..services.llm import call_llm, LiveLLMGoalsProvider, LLM_UNAVAILABLE_MSG
from ..services.goal_validation import GoalValidator


# System prompts for LLM
SYSTEM_AGE = "Ask ONLY age in whole years. Validate 0–120."
SYSTEM_HORIZON = "Ask ONLY time horizon in whole YEARS (0–80)."
SYSTEM_EMERGENCY = "Ask ONLY emergency fund size in MONTHS (0–120)."
SYSTEM_DEPENDENTS = "Ask ONLY number of dependents (0–20)."
SYSTEM_INCOME_STAB = "Ask ONLY about income stability. Options: 1) Very unstable 2) Somewhat stable 3) Stable 4) Very stable"
SYSTEM_EXPERIENCE = "Ask ONLY about experience. Options: 1) Beginner 2) Some experience 3) Experienced 4) Advanced/Pro"
SYSTEM_LOSS_TOL = "Ask ONLY loss tolerance. Options: 1) Can't tolerate losses 2) Small dips OK 3) Volatility fine 4) Big swings OK"
SYSTEM_SAVINGS_RATE = "Ask ONLY monthly savings rate in % (0–100)."
SYSTEM_DEBT_LOAD = "Ask ONLY debt load vs income. Options: 1) No/low 2) Manageable 3) Moderate 4) High"
SYSTEM_LIQ_NEED = "Ask ONLY liquidity need timing. Options: 1) <1y 2) 1–3y 3) >3y 4) Not sure"
SYSTEM_REACTION = "Ask ONLY: Portfolio drops 20% in a month—what do you do? Options: 1) Sell 2) Wait 3) Hold 4) Buy more"
SYSTEM_OBJECTIVE = "Ask ONLY primary investment objective. Options: 1) Capital preservation 2) Income 3) Balanced 4) Growth"
FINANCE_QA_SYSTEM = (
    "You are a concise, neutral explainer of personal-finance terms. "
    "Answer briefly with a tiny example if useful. Avoid personalized advice."
)


class RiskAssessmentAgent:
    """Main risk assessment agent for conducting financial assessments."""
    
    def __init__(self, 
                 question_toggles: Optional[Dict[str, bool]] = None,
                 llm_fn: Callable[[List[Dict[str, str]]], str] = call_llm,
                 goals_provider: Optional[GoalsProvider] = None):
        """Initialize the risk assessment agent."""
        self.question_toggles = question_toggles or {
            "age": True, "horizon": True, "emergency_fund_months": True, "dependents": True,
            "income_stability": True, "experience": True, "loss_tolerance": True, "savings_rate": True,
            "debt_load": True, "liquidity_need": True, "reaction_scenario": True, "investment_objective": True,
        }
        self.llm_fn = llm_fn
        self.goals_provider = goals_provider or LiveLLMGoalsProvider(llm_fn)
        
        self.step = Step.ASSESSMENT
        self.idx = 0
        self.answers: Dict[str, str] = {}
        self._questions: List[Question] = []
        self._weights_sum: float = 0.0
        self.risk_score_pct: Optional[float] = None
        self.risk_label: Optional[str] = None
        self.selected_goals: List[str] = []
        self._last_question: Optional[Question] = None
        self._current_goal_suggestions: List[str] = []
        self._current_goal_page: int = 0
        self._total_goals_shown: int = 0
        self._all_goals_shown: List[str] = []
        self.goal_validator = GoalValidator()
        self.pending_goal_validation: Optional[Tuple[str, GoalValidationResult]] = None
        
        # Data tracking fields
        self.user_id = f"user_{uuid.uuid4().hex[:8]}"
        self.session_id = f"session_{uuid.uuid4().hex[:8]}"
        self.created_timestamp = datetime.now(timezone.utc).isoformat()
        self.deleted_goals: List[Dict[str, Any]] = []
        self.clarifications_count = 0
        self.goals_explained_count = 0
        
        self._initialize_questions()
    
    def _initialize_questions(self):
        """Initialize the assessment questions."""
        self._questions = [
            Question("age", "How old are you? (whole years)", [], SYSTEM_AGE, validate_age, score_age, 1.0, self.question_toggles.get("age", True)),
            Question("horizon", "What is your investment time horizon in YEARS? (0–80)", [], SYSTEM_HORIZON, validate_years, score_horizon, 1.2, self.question_toggles.get("horizon", True)),
            Question("emergency_fund_months", "Emergency fund size in MONTHS of essential expenses? (0–120)", [], SYSTEM_EMERGENCY, validate_months, score_emergency_months, 0.8, self.question_toggles.get("emergency_fund_months", True)),
            Question("dependents", "How many people rely on your income (dependents)? (0–20)", [], SYSTEM_DEPENDENTS, lambda t: validate_nonneg_int(t, 20), score_dependents, 0.6, self.question_toggles.get("dependents", True)),
            Question("income_stability", "How stable is your income?", ["Very unstable", "Somewhat stable", "Stable", "Very stable"], SYSTEM_INCOME_STAB, lambda t: validate_mc_or_text_with_display(t, ["Very unstable", "Somewhat stable", "Stable", "Very stable"], 4), score_income_stability, 0.8, self.question_toggles.get("income_stability", True)),
            Question("experience", "What is your investing experience level?", ["Beginner", "Some experience", "Experienced", "Advanced/Pro"], SYSTEM_EXPERIENCE, lambda t: validate_mc_or_text_with_display(t, ["Beginner", "Some experience", "Experienced", "Advanced/Pro"], 4), score_experience, 0.9, self.question_toggles.get("experience", True)),
            Question("loss_tolerance", "How do you feel about temporary losses (drawdowns)?", ["I can't tolerate losses", "Small dips are okay", "Volatility is fine if returns are higher", "I'm comfortable with big swings"], SYSTEM_LOSS_TOL, lambda t: validate_mc_or_text_with_display(t, ["I can't tolerate losses", "Small dips are okay", "Volatility is fine if returns are higher", "I'm comfortable with big swings"], 4), score_loss_tolerance, 1.2, self.question_toggles.get("loss_tolerance", True)),
            Question("savings_rate", "Roughly what percent of your income do you save/invest monthly? (0–100%)", [], SYSTEM_SAVINGS_RATE, validate_pct, score_savings_rate, 0.7, self.question_toggles.get("savings_rate", True)),
            Question("debt_load", "How would you describe your current debt load (relative to income)?", ["No/low debt (<20%)", "Manageable (20-35%)", "Moderate (35-50%)", "High (>50%)"], SYSTEM_DEBT_LOAD, lambda t: validate_mc_or_text_with_display(t, ["No/low debt (<20%)", "Manageable (20-35%)", "Moderate (35-50%)", "High (>50%)"], 4), score_debt_load, 0.8, self.question_toggles.get("debt_load", True)),
            Question("liquidity_need", "When might you need to withdraw a significant portion of this money?", ["< 1 year", "1–3 years", "> 3 years", "Not sure"], SYSTEM_LIQ_NEED, lambda t: validate_mc_or_text_with_display(t, ["< 1 year", "1–3 years", "> 3 years", "Not sure"], 4), score_liquidity_need, 1.0, self.question_toggles.get("liquidity_need", True)),
            Question("reaction_scenario", "Your portfolio drops 20% in a month. What do you do?", ["Sell immediately", "Wait a bit", "Hold", "Buy more"], SYSTEM_REACTION, lambda t: validate_mc_or_text_with_display(t, ["Sell immediately", "Wait a bit", "Hold", "Buy more"], 4), score_reaction_scenario, 1.3, self.question_toggles.get("reaction_scenario", True)),
            Question("investment_objective", "What is your primary investment objective?", ["Capital preservation", "Income", "Balanced (growth + income)", "Growth"], SYSTEM_OBJECTIVE, lambda t: validate_mc_or_text_with_display(t, ["Capital preservation", "Income", "Balanced (growth + income)", "Growth"], 4), score_objective, 0.9, self.question_toggles.get("investment_objective", True)),
        ]
        self._weights_sum = sum(q.weight for q in self._questions if q.enabled) or 1.0
    
    def _ensure_llm(self) -> Optional[str]:
        """Check if LLM is available."""
        try:
            _ = self.llm_fn([{"role":"system","content":"Reply with OK only."},{"role":"user","content":"OK?"}]).strip()
            return None
        except Exception:
            return LLM_UNAVAILABLE_MSG
    
    def start(self) -> str:
        """Start a new assessment."""
        err = self._ensure_llm()
        if err: return err
        self.step = Step.ASSESSMENT
        self.idx = 0
        self.answers.clear()
        self.risk_score_pct = None
        self.risk_label = None
        self.selected_goals.clear()
        return self.next_bot_message()
    
    def next_bot_message(self) -> str:
        """Get the next bot message in the assessment flow."""
        err = self._ensure_llm()
        if err: return err
        if self.step == Step.ASSESSMENT:
            q = self._next_enabled_question()
            if not q:
                self._compute_risk()
                self.step = Step.GOAL_SETTING
                return self._render_risk_result() + "\n\n" + self._render_goal_intro()
            self._last_question = q
            return q.render_prompt()
        if self.step == Step.GOAL_SETTING:
            return self._render_goal_intro()
        return "All done! Type 'restart' to do another assessment."
    
    def receive_user_message(self, text: str) -> str:
        """Process a user message and return the bot's response."""
        t = (text or "").strip()
        if t.lower() in {"restart", "retry", "check"}:
            return self.start()
        err = self._ensure_llm()
        if err: return err
        
        # Handle continuation requests after explanations
        if is_continuation_request(t) and self._last_question and self.step == Step.ASSESSMENT:
            return self._last_question.render_prompt()
        
        # Handle questions about unclear terms
        if is_question(t) and self.step != Step.COMPLETE:
            self.clarifications_count += 1
            try:
                system_prompt = (
                    "You are a helpful financial advisor explaining terms clearly. "
                    "Answer the user's question about the financial term or concept. "
                    "Be concise but thorough. After explaining, mention that they can continue with their assessment. "
                    "If they're asking about a specific question from the assessment, reference that context."
                )
                
                context = ""
                if self._last_question:
                    context = f"\n\nContext: The user is currently being asked: '{self._last_question.user_question}'"
                
                ans = self.llm_fn([
                    {"role":"system","content":system_prompt},
                    {"role":"user","content":t + context}
                ])
                return f"{ans}\n\n(You can now continue with your assessment. Type 'continue' or just answer the question.)"
            except Exception:
                return LLM_UNAVAILABLE_MSG
        
        # Handle assessment step
        if self.step == Step.ASSESSMENT:
            q = self._next_enabled_question()
            if not q:
                self._compute_risk()
                self.step = Step.GOAL_SETTING
                return self._render_risk_result() + "\n\n" + self._render_goal_intro()
            
            # Validate the user's input
            try:
                ok, norm, display_text, err_msg = q.validator(t)
                if ok:
                    q.display_text = display_text
            except ValueError:
                ok, norm, err_msg = q.validator(t)
                if ok:
                    q.display_text = norm
            
            if not ok:
                if q.choices:
                    options = "\n".join(f"{i}) {c}" for i, c in enumerate(q.choices, start=1))
                    return (
                        f"{err_msg}\n\n"
                        f"Options:\n{options}\n"
                        f"(Or type a clear alternative in your own words.)\n"
                        f"If you need clarification about any term, just ask!"
                    )
                else:
                    return f"{err_msg}\n\nTry again: {q.user_question}\n(You can also type numbers as words like 'twenty eight' or ask for clarification.)"
            
            # Store the answer and move to next question
            self.answers[q.id] = norm or t
            self.idx += 1
            return self.next_bot_message()
        
        # Handle goal setting step
        if self.step == Step.GOAL_SETTING:
            return self._handle_goal_selection(t)
        
        return "All done! Type 'restart' to do another assessment."
    
    def _next_enabled_question(self) -> Optional[Question]:
        """Get the next enabled question."""
        while self.idx < len(self._questions):
            q = self._questions[self.idx]
            if q.enabled: return q
            self.idx += 1
        return None
    
    def _compute_risk(self) -> None:
        """Compute the risk score based on answers."""
        total = 0.0
        for q in self._questions:
            if not q.enabled: continue
            ans = self.answers.get(q.id)
            pts = q.scorer(ans)
            if pts is None: continue
            total += (pts * q.weight)
        self.risk_score_pct = round(total / self._weights_sum, 2)
        label, _ = risk_bucket(self.risk_score_pct)
        self.risk_label = label
    
    def _render_risk_result(self) -> str:
        """Render the risk assessment result."""
        label, desc = risk_bucket(self.risk_score_pct or 0.0)
        return (
            f"✅ Risk Profile Assessment Complete!\n"
            f"Your risk score: **{self.risk_score_pct}%** → **{label}**\n"
            f"{desc}"
        )
    
    def _render_goal_intro(self) -> str:
        """Render the goal setting introduction."""
        try:
            suggestions = self.goals_provider.generate(self.risk_label or "Balanced", self._goal_context())
            self._current_goal_suggestions = suggestions
            self._current_goal_page = 0
            self._total_goals_shown = len(suggestions)
            self._all_goals_shown = suggestions.copy()
        except Exception:
            return LLM_UNAVAILABLE_MSG
        lines = "\n".join(f"{i+1}) {g}" for i, g in enumerate(suggestions))
        return (
            "🎯 Goal Setting\n"
            "Do you have a specific goal in mind, or would you like suggestions based on your profile?\n"
            "- Type your goal (free text), OR\n"
            "- Type numbers to pick from the suggestions below (e.g., 1,3), OR\n"
            "- Type 'more suggestions' or 'more goals' to get additional options, OR\n"
            "- Type 'explain goal 1' or 'elaborate on 3' to get more details, OR\n"
            "- Type 'delete 1,3' or 'remove 2' to delete selected goals, OR\n"
            "- Type any 'done' phrase when finished (e.g., done / end / finished / I'm done).\n\n"
            f"Suggested goals for {self.risk_label or 'Balanced'}:\n{lines}"
        )
    
    def _goal_context(self) -> Dict[str, Any]:
        """Get context for goal generation."""
        return {"risk_score_pct": self.risk_score_pct, "answers": self.answers}
    
    def _classify_goal_with_llm(self, goal_text: str) -> bool:
        """Classify if text is a valid financial goal using LLM."""
        sys = {"role":"system","content":
               "You are a validator. Decide if the user's phrase describes a concrete financial goal "
               "(e.g., saving/investing/debt payoff/retirement/home/education/purchase fund). "
               "Answer strictly with 'YES' or 'NO'—no other text."}
        usr = {"role":"user","content":f"Phrase: {goal_text}"}
        out = self.llm_fn([sys, usr]).strip().upper()
        return bool(re.match(r"^YES\b", out))
    
    def _handle_goal_validation_completion(self, text: str) -> str:
        """Handle completion of goal validation by user providing missing information."""
        goal_text, validation_result = self.pending_goal_validation
        
        # Try to parse the user's response as additional goal information
        enhanced_goal = f"{goal_text} {text.strip()}"
        
        # Re-validate the enhanced goal
        new_validation = self.goal_validator.validate_goal(enhanced_goal)
        
        if new_validation.is_valid:
            # Goal is now complete, add it to selected goals
            self.selected_goals.append(enhanced_goal)
            self.pending_goal_validation = None
            
            current_goals = self._render_selected_goals()
            return (
                f"✅ Added goal: {enhanced_goal}\n\n"
                f"📋 Your current goals:\n{current_goals}\n\n"
                "Add more goals, type numbers, or any done phrase to finish."
            )
        else:
            # Check if the new input actually improved the validation
            improved = False
            if validation_result.target_amount is None and new_validation.target_amount is not None:
                improved = True
            if validation_result.target_date is None and new_validation.target_date is not None:
                improved = True
            
            if improved:
                # The input was valid and improved the goal, update pending validation
                self.pending_goal_validation = (enhanced_goal, new_validation)
                return self.goal_validator.generate_single_field_prompt(enhanced_goal, new_validation)
            else:
                # The input was invalid or didn't improve the goal, keep original goal text
                return self.goal_validator.generate_single_field_prompt(goal_text, validation_result)
    
    def _handle_goal_selection(self, text: str) -> str:
        """Handle goal selection logic."""
        # Check if we're waiting for goal validation completion
        if self.pending_goal_validation:
            return self._handle_goal_validation_completion(text)
        
        if is_done_phrase(text):
            self.step = Step.COMPLETE
            if not self.selected_goals:
                return "No goals selected. You can type a goal now, or 'restart' to begin again."
            return self._render_summary()
        
        t = text.strip().lower()
        
        # Handle goal explanation requests
        if is_explanation_request(t):
            goal_number = extract_explanation_goal_number(text)
            if goal_number is None:
                return "Please specify which goal to explain by number (e.g., 'explain goal 1' or 'elaborate on 3')."
            return self._explain_goal(goal_number)
        
        # Handle goal deletion requests
        if is_deletion_request(t):
            goal_numbers = extract_goal_numbers(text)
            if not goal_numbers:
                return "Please specify which goal(s) to delete by number (e.g., 'delete 1' or 'remove 1,3')."
            
            deleted_goals = []
            # Sort in descending order to avoid index shifting issues
            for num in sorted(goal_numbers, reverse=True):
                if 1 <= num <= len(self.selected_goals):
                    deleted_goals.append(self.selected_goals.pop(num - 1))
            
            if deleted_goals:
                # Track deleted goals
                for goal in deleted_goals:
                    self.deleted_goals.append({
                        "id": f"goal_deleted_{len(self.deleted_goals) + 1}",
                        "text": goal,
                        "deleted_timestamp": datetime.now(timezone.utc).isoformat(),
                        "status": "deleted"
                    })
                
                deleted_list = "\n".join(f"{i+1}) {g}" for i, g in enumerate(deleted_goals))
                remaining_goals = self._render_selected_goals()
                return (
                    f"✅ Deleted goal(s):\n{deleted_list}\n\n"
                    f"📋 Your current goals:\n{remaining_goals}\n\n"
                    "Continue selecting goals, type 'more suggestions' for additional options, or type 'done' when finished."
                )
            else:
                return f"No valid goals to delete. You have {len(self.selected_goals)} goals. Use numbers 1-{len(self.selected_goals)}."
        
        # Handle requests for more suggestions
        suggestion_indicators = [
            "more suggestions", "more goals", "more options", "need more", "additional",
            "other suggestions", "different suggestions", "new suggestions", "another set",
            "show more", "give me more", "i need more", "more please", "suggest more",
            "any other", "what else", "other ideas", "different goals", "new goals",
            "more choices", "other options", "different options", "additional options"
        ]
        if any(phrase in t for phrase in suggestion_indicators):
            try:
                new_suggestions = self.goals_provider.generate(self.risk_label or "Balanced", self._goal_context())
                self._current_goal_page += 1
                self._all_goals_shown.extend(new_suggestions)
                start_num = self._total_goals_shown + 1
                lines = "\n".join(f"{start_num + i}) {g}" for i, g in enumerate(new_suggestions))
                self._total_goals_shown += len(new_suggestions)
                return (
                    f"Here are more goal suggestions (page {self._current_goal_page + 1}):\n\n"
                    f"{lines}\n\n"
                    "Choose by number(s), add your own goal, type 'delete X' to remove goals, or type 'more suggestions' for additional options."
                )
            except Exception:
                return LLM_UNAVAILABLE_MSG
        
        # Handle requests to see current suggestions again
        if t in ("yes", "suggest", "y", "show options", "show suggestions"):
            if self._current_goal_suggestions:
                lines = "\n".join(f"{i+1}) {g}" for i, g in enumerate(self._current_goal_suggestions))
                return (
                    f"Current goal suggestions ({len(self._current_goal_suggestions)} options):\n\n"
                    f"{lines}\n\n"
                    "Choose by number(s), add your own goal, or type 'more suggestions' for additional options."
                )
            else:
                return self._render_goal_intro()
        
        if t in ("no", "n"):
            return "Okay—please type your goal in your own words, or type 'suggest' to see ideas."

        added: List[str] = []
        
        # Handle number selections from all goals shown (continuous numbering)
        nums = re.findall(r"\d+", t)
        if nums and len(t.split()) <= 3 and all(word.isdigit() or word in [',', 'and', '&'] for word in t.split()):
            for n in nums:
                i = int(n) - 1
                if 0 <= i < len(self._all_goals_shown):
                    g = self._all_goals_shown[i]
                    try:
                        if self._classify_goal_with_llm(g):
                            if g not in self.selected_goals:
                                self.selected_goals.append(g)
                                added.append(g)
                    except Exception:
                        return LLM_UNAVAILABLE_MSG
                else:
                    return f"Goal #{n} is not available. Choose from 1-{len(self._all_goals_shown)} or type 'more suggestions' for additional goals."

        # Handle custom goal text
        if not added and not any(word.isdigit() for word in t.split() if word not in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']):
            try:
                if self._classify_goal_with_llm(text.strip()):
                    # Validate the custom goal
                    validation_result = self.goal_validator.validate_goal(text.strip())
                    if validation_result.is_valid:
                        if text.strip() not in self.selected_goals:
                            self.selected_goals.append(text.strip())
                            added.append(text.strip())
                    else:
                        # Goal needs more information
                        self.pending_goal_validation = (text.strip(), validation_result)
                        return self.goal_validator.generate_single_field_prompt(text.strip(), validation_result)
            except Exception:
                return LLM_UNAVAILABLE_MSG
        else:
            # Handle multiple custom goals separated by delimiters
            raw_parts = [s.strip() for s in re.split(r"[;\n]| and ", text) if s.strip()]
            raw_parts = [r for r in raw_parts if not (r.isdigit() and len(r) <= 2) and not is_done_phrase(r)]
            for r in raw_parts:
                try:
                    if self._classify_goal_with_llm(r):
                        # Validate each goal
                        validation_result = self.goal_validator.validate_goal(r)
                        if validation_result.is_valid:
                            if r not in self.selected_goals:
                                self.selected_goals.append(r)
                                added.append(r)
                        else:
                            # Goal needs more information
                            self.pending_goal_validation = (r, validation_result)
                            return self.goal_validator.generate_single_field_prompt(r, validation_result)
                except Exception:
                    return LLM_UNAVAILABLE_MSG

        if added:
            current_goals = self._render_selected_goals()
            return (
                f"✅ Added goals: {', '.join(added)}\n\n"
                f"📋 Your current goals:\n{current_goals}\n\n"
                "Add more goals, type numbers, or any done phrase to finish."
            )
        else:
            # Check if user might be asking for more suggestions
            if any(word in t for word in ["suggestions", "goals", "options", "choices", "more", "other", "different", "new"]):
                return ("It sounds like you want more suggestions! Type 'more suggestions' or 'other options' to get additional goal ideas. "
                        f"Or choose from the current options by number (1-{len(self._all_goals_shown)}).")
            else:
                return ("I didn't catch a valid financial goal. "
                        "Choose by number(s), type a clear goal, or type 'more suggestions' for additional options. "
                        "You can also type a done phrase to finish.")

    def _render_selected_goals(self) -> str:
        """Render the currently selected goals as a numbered list."""
        if not self.selected_goals:
            return "No goals selected yet."
        return "\n".join(f"{i+1}) {g}" for i, g in enumerate(self.selected_goals))

    def _explain_goal(self, goal_number: int) -> str:
        """Explain a specific goal using the LLM."""
        if not self.selected_goals:
            return "No goals selected yet."
        
        if not (1 <= goal_number <= len(self.selected_goals)):
            return f"Goal #{goal_number} is not available. You have {len(self.selected_goals)} goals. Use numbers 1-{len(self.selected_goals)}."
        
        goal_text = self.selected_goals[goal_number - 1]
        
        try:
            # Track goal explanation
            self.goals_explained_count += 1
            
            system_prompt = (
                "You are a financial advisor explaining investment goals. "
                "Provide a detailed explanation of the financial goal, including: "
                "1. What the goal involves and why it's important "
                "2. Potential strategies to achieve it "
                "3. Timeline considerations "
                "4. Risk factors to consider "
                "5. Any relevant financial planning tips "
                "Be specific, helpful, and educational. Keep it concise but thorough."
            )
            
            explanation = self.llm_fn([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please explain this financial goal: {goal_text}"}
            ])
            
            return (
                f"📋 **Goal #{goal_number}**: {goal_text}\n\n"
                f"💡 **Explanation**:\n{explanation}\n\n"
                f"📋 Your current goals:\n{self._render_selected_goals()}\n\n"
                "Continue selecting goals, type 'delete X' to remove goals, or type 'done' when finished."
            )
        except Exception:
            return LLM_UNAVAILABLE_MSG

    def _render_summary(self) -> str:
        """Render the final summary and save data."""
        # Save user data
        filepath = self._save_user_data()
        
        goals = "\n".join(f"• {g}" for g in self.selected_goals) or "None"
        return ("🧾 Summary\n"
                f"- Risk Score: {self.risk_score_pct}% ({self.risk_label})\n"
                f"- Selected Goals:\n{goals}\n\n"
                f"📁 Your data has been saved to: {filepath}\n"
                "Thank you! Type 'restart' to run the assessment again.")

    def _get_data_directory(self) -> str:
        """Get the data directory, create if it doesn't exist."""
        data_dir = "user_data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        return data_dir

    def _save_user_data(self) -> str:
        """Save user data to JSON file."""
        # Prepare the data structure
        user_data = {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": {
                "created": self._format_timestamp(datetime.fromisoformat(self.created_timestamp.replace('Z', '+00:00'))),
                "last_updated": self._format_timestamp(datetime.now(timezone.utc)),
                "assessment_completed": self._format_timestamp(datetime.now(timezone.utc)) if self.step == Step.COMPLETE else None
            },
            "assessment_data": {
                "risk_profile": {
                    "score_percentage": self.risk_score_pct,
                    "label": self.risk_label,
                    "description": self._get_risk_description()
                },
                "answers": self._format_answers_with_display_text(),
                "individual_scores": self._get_individual_scores(),
                "question_weights": self._get_question_weights()
            },
            "goals": {
                "selected_goals": self._format_selected_goals(),
                "deleted_goals": self.deleted_goals.copy(),
                "total_goals_considered": len(self._all_goals_shown),
                "suggestion_pages_viewed": self._current_goal_page + 1
            },
            "session_metadata": {
                "questions_asked": len(self.answers),
                "questions_skipped": 0,
                "clarifications_requested": self.clarifications_count,
                "goals_explained": self.goals_explained_count,
                "total_session_duration_minutes": self._get_session_duration(),
                "llm_model_used": "gpt-oss:20b",
                "version": "1.0.0"
            },
            "progress_tracking": {
                "assessment_stage": "completed" if self.step != Step.ASSESSMENT else "in_progress",
                "goal_setting_stage": "completed" if self.step == Step.COMPLETE else "in_progress",
                "next_review_date": self._get_next_review_date(),
                "milestones": [],
                "notes": []
            }
        }
        
        # Save to file
        data_dir = self._get_data_directory()
        filename = f"{self.user_id}_{self.session_id}.json"
        filepath = os.path.join(data_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, indent=2, ensure_ascii=False)
        
        return filepath

    def _get_risk_description(self) -> str:
        """Get risk profile description."""
        if self.risk_score_pct is None:
            return "Not assessed"
        _, desc = risk_bucket(self.risk_score_pct)
        return desc

    def _get_individual_scores(self) -> Dict[str, float]:
        """Get individual question scores."""
        scores = {}
        for q in self._questions:
            if q.enabled and q.id in self.answers:
                score = q.scorer(self.answers[q.id])
                if score is not None:
                    scores[q.id] = score
        return scores

    def _get_question_weights(self) -> Dict[str, float]:
        """Get question weights."""
        weights = {}
        for q in self._questions:
            if q.enabled:
                weights[q.id] = q.weight
        return weights

    def _format_selected_goals(self) -> List[Dict[str, Any]]:
        """Format selected goals for JSON storage."""
        goals = []
        for i, goal_text in enumerate(self.selected_goals):
            goal_data = {
                "id": f"goal_{i+1}",
                "text": goal_text,
                "source": "custom",  # Default to custom
                "added_timestamp": self._format_timestamp(datetime.now(timezone.utc)),
                "status": "active"
            }
            
            # Try to determine if it came from suggestions
            if hasattr(self, '_all_goals_shown'):
                for j, suggested_goal in enumerate(self._all_goals_shown):
                    if suggested_goal == goal_text:
                        goal_data["source"] = "suggestion"
                        goal_data["suggestion_number"] = j + 1
                        break
            
            goals.append(goal_data)
        return goals

    def _get_session_duration(self) -> int:
        """Get session duration in minutes."""
        start_time = datetime.fromisoformat(self.created_timestamp.replace('Z', '+00:00'))
        end_time = datetime.now(timezone.utc)
        duration = end_time - start_time
        return int(duration.total_seconds() / 60)

    def _get_next_review_date(self) -> str:
        """Get next review date (30 days from now)."""
        next_date = datetime.now(timezone.utc) + timedelta(days=30)
        return self._format_timestamp(next_date)

    def _format_timestamp(self, dt: datetime) -> str:
        """Format timestamp to clean format without timezone and reduced precision."""
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]  # Remove last 3 digits of microseconds

    def _format_answers_with_display_text(self) -> Dict[str, str]:
        """Format answers using display text when available."""
        formatted_answers = {}
        for q in self._questions:
            if q.enabled and q.id in self.answers:
                if hasattr(q, 'display_text') and q.display_text:
                    formatted_answers[q.id] = q.display_text
                else:
                    formatted_answers[q.id] = self.answers[q.id]
        return formatted_answers
