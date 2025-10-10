
# LLM Service for Recommendations and Goal Suggestions

from models import db, User, Goal, Assessment, ProgressSnapshot
from datetime import datetime
import json
import ollama
from typing import Dict, List, Optional, Any

class LLMService:
    def __init__(self):
        self.model = "gpt-oss:20b"
        self.ollama_available = self._check_ollama_availability()
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available"""
        try:
            models = ollama.list()
            # Check if our model is available
            model_names = [model['name'] for model in models.get('models', [])]
            print(f"Available models: {model_names}")
            
            if 'gpt-oss:20b' not in model_names:
                print(f"Warning: Model 'gpt-oss:20b' not found. Available models: {model_names}")
                # Try alternative model names
                if 'gpt-oss' in str(model_names):
                    for model in models.get('models', []):
                        if 'gpt-oss' in model['name']:
                            self.model = model['name']
                            print(f"Using alternative model: {self.model}")
                            break
                else:
                    # If no gpt-oss models found, try other common models
                    common_models = ['llama2', 'mistral', 'codellama', 'phi']
                    for common_model in common_models:
                        if common_model in model_names:
                            self.model = common_model
                            print(f"Using fallback model: {self.model}")
                            break
            return True
        except Exception as e:
            print(f"Ollama not available: {e}")
            return False
    
    def get_help_response(self, question: str, context: str = "") -> str:
        """Get LLM response for help questions"""
        if not self.ollama_available:
            return "I'm sorry, the AI assistant is currently unavailable. Please try again later."
        
        try:
            system_prompt = (
                "You are a helpful financial advisor explaining terms clearly. "
                "Answer the user's question about the financial term or concept. "
                "Be concise but thorough. After explaining, mention that they can continue with their assessment. "
                "If they're asking about a specific question from the assessment, reference that context."
            )
            
            user_content = question
            if context:
                user_content = f"{question}\n\nContext: {context}"
            
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            )
            
            return response['message']['content']
            
        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                # Try alternative models
                return self._try_alternative_model(system_prompt, user_content)
            else:
                return f"I'm sorry, I couldn't process your question. Error: {error_msg}"

    def _try_alternative_model(self, system_prompt: str, user_content: str) -> str:
        """Try alternative models if the current one fails"""
        available_models = self.get_available_models()
        for model_name in available_models:
            try:
                print(f"Trying model: {model_name}")
                response = ollama.chat(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ]
                )
                # If successful, update the current model
                self.model = model_name
                print(f"Successfully switched to model: {model_name}")
                return response['message']['content']
            except Exception as e:
                print(f"Model {model_name} failed: {e}")
                continue
        
        return "I'm sorry, none of the available AI models are working at the moment. Please try again later."

    def get_available_models(self) -> List[str]:
        """Get list of available models for debugging"""
        try:
            models = ollama.list()
            return [model['name'] for model in models.get('models', [])]
        except Exception:
            return []

    def generate_goal_suggestions(self, risk_label: str, request_more: bool = False) -> List[str]:
        """Generate goal suggestions based on risk profile"""
        if not self.ollama_available:
            return self._get_fallback_goal_suggestions()
        
        try:
            system_prompt = (
                "You are a financial planning assistant. Suggest exactly 8 "
                "concise, specific, time-aware goal options suitable for the user. "
                "Be concrete: include amounts, durations or a month/year where relevant. "
                "If proposing assets/sectors, add the current month/year and a brief risk note. "
                "Do NOT guarantee returns; use cautious phrasing. "
                "Output as 8 separate lines; no numbering, no explanations."
            )
            
            user_content = f"As of {datetime.now().strftime('%B %Y')}, propose 8 goal options for a user with {risk_label} risk profile. Only list the goal titles, one per line."
            
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            )
            
            text = response['message']['content'].strip()
            lines = [l.strip("-• \n\r\t") for l in text.splitlines() if l.strip()]
            
            # Ensure we have at least 8 suggestions
            if len(lines) < 8:
                fallback_suggestions = self._get_fallback_goal_suggestions()
                lines.extend(fallback_suggestions[len(lines):])
            
            return lines[:8]
            
        except Exception as e:
            return self._get_fallback_goal_suggestions()
    
    def _get_fallback_goal_suggestions(self) -> List[str]:
        """Fallback goal suggestions when LLM is unavailable"""
        return [
            "Emergency Fund (3-6 months of expenses)",
            "Retirement Savings (15% of income)",
            "Home Down Payment (20% of home value)",
            "Debt Payoff (High-interest debt first)",
            "Education Fund (College savings)",
            "Vacation Fund (Annual travel budget)",
            "Car Purchase (New or used vehicle)",
            "Investment Portfolio (Diversified assets)"
        ]

    def get_recommendations(self, user_id: str, goal_id: Optional[str] = None) -> List[str]:
        """Get personalized recommendations for a user"""
        if not self.ollama_available:
            return self._get_fallback_recommendations()
        
        try:
            # Get user data
            user = User.query.get(user_id)
            if not user:
                return []
            
            # Get user's risk profile
            assessment = Assessment.query.filter_by(user_id=user_id, status='completed').first()
            risk_profile = assessment.risk_label if assessment else "Balanced"
            
            # Get goal data
            if goal_id:
                goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
                if not goal:
                    return []
                
                # Get latest progress
                progress = ProgressSnapshot.query.filter_by(
                    user_id=user_id, 
                    goal_id=goal_id
                ).order_by(ProgressSnapshot.as_of.desc()).first()
                
                if progress:
                    recommendations = self._generate_goal_specific_recommendations(goal, progress, risk_profile)
                else:
                    recommendations = self._generate_general_recommendations(risk_profile)
            else:
                recommendations = self._generate_general_recommendations(risk_profile)
            
            return recommendations
            
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return self._get_fallback_recommendations()
    
    def generate_goal_suggestions(self, user_id: str, risk_profile: str) -> List[str]:
        """Generate goal suggestions based on user's risk profile"""
        if not self.ollama_available:
            return self._get_fallback_goal_suggestions(risk_profile)
        
        try:
            # Get user context
            user = User.query.get(user_id)
            assessment = Assessment.query.filter_by(user_id=user_id, status='completed').first()
            
            context = {
                'risk_profile': risk_profile,
                'user_age': assessment.answers.get('age', '30') if assessment else '30',
                'income_stability': assessment.answers.get('income_stability', 'Stable') if assessment else 'Stable',
                'savings_rate': assessment.answers.get('savings_rate', '10') if assessment else '10'
            }
            
            # Generate suggestions using LLM
            system_prompt = (
                "You are a financial planning assistant. Generate exactly 10 specific, "
                "actionable financial goal suggestions based on the user's risk profile and context. "
                "Each goal should include a specific amount and timeline. "
                "Be concrete and realistic. Format each goal as a single line."
            )
            
            user_prompt = f"""
            Generate 10 financial goal suggestions for a user with:
            - Risk Profile: {context['risk_profile']}
            - Age: {context['user_age']} years old
            - Income Stability: {context['income_stability']}
            - Monthly Savings Rate: {context['savings_rate']}%
            
            Provide diverse goals across different categories like emergency fund, retirement, 
            vacation, education, home purchase, etc. Include specific amounts and timelines.
            """
            
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Parse response
            suggestions = []
            for line in response['message']['content'].split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and len(line) > 10:
                    suggestions.append(line)
            
            return suggestions[:10] if suggestions else self._get_fallback_goal_suggestions(risk_profile)
            
        except Exception as e:
            print(f"Error generating goal suggestions: {e}")
            return self._get_fallback_goal_suggestions(risk_profile)
    
    def _generate_goal_specific_recommendations(self, goal: Goal, progress: ProgressSnapshot, risk_profile: str) -> List[str]:
        """Generate recommendations specific to a goal's progress"""
        try:
            system_prompt = (
                "You are a financial coach. Based on the goal progress data, provide 3-5 "
                "specific, actionable recommendations to help the user achieve their goal. "
                "Be practical and realistic. Each recommendation should be 1-2 sentences."
            )
            
            user_prompt = f"""
            Goal: {goal.name}
            Category: {goal.category}
            Target Amount: ${goal.target_amount:,.2f}
            Target Date: {goal.target_date}
            Current Progress: {progress.progress_pct:.1f}%
            Pacing Status: {progress.pacing_status}
            Pacing Detail: {progress.pacing_detail}
            Risk Profile: {risk_profile}
            
            Provide specific recommendations to help achieve this goal.
            """
            
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Parse recommendations
            recommendations = []
            for line in response['message']['content'].split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and len(line) > 20:
                    recommendations.append(line)
            
            return recommendations[:5] if recommendations else self._get_fallback_recommendations()
            
        except Exception as e:
            print(f"Error generating goal-specific recommendations: {e}")
            return self._get_fallback_recommendations()
    
    def _generate_general_recommendations(self, risk_profile: str) -> List[str]:
        """Generate general financial recommendations"""
        try:
            system_prompt = (
                "You are a financial advisor. Provide 5 general financial recommendations "
                "based on the user's risk profile. Be practical and actionable."
            )
            
            user_prompt = f"Provide general financial recommendations for someone with a {risk_profile} risk profile."
            
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Parse recommendations
            recommendations = []
            for line in response['message']['content'].split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and len(line) > 20:
                    recommendations.append(line)
            
            return recommendations[:5] if recommendations else self._get_fallback_recommendations()
            
        except Exception as e:
            print(f"Error generating general recommendations: {e}")
            return self._get_fallback_recommendations()
    
    def _get_fallback_recommendations(self) -> List[str]:
        """Fallback recommendations when LLM is not available"""
        return [
            "Consider increasing your monthly savings by 5-10% to accelerate goal achievement",
            "Review your spending categories to identify areas for cost reduction",
            "Set up automatic transfers to your savings account on payday",
            "Consider diversifying your investments based on your risk tolerance",
            "Regularly review and adjust your goals based on life changes"
        ]
    
    def _get_fallback_goal_suggestions(self, risk_profile: str) -> List[str]:
        """Fallback goal suggestions when LLM is not available"""
        base_suggestions = [
            "Build emergency fund of $10,000 by December 2025",
            "Save $5,000 for vacation by June 2025",
            "Contribute $6,000 to Roth IRA by April 2025",
            "Save $20,000 for home down payment by December 2026",
            "Pay off $15,000 credit card debt by September 2025",
            "Save $2,000 for car maintenance fund by March 2025",
            "Invest $3,000 in index funds by May 2025",
            "Save $8,000 for children's education by December 2027",
            "Build $25,000 emergency fund by December 2025",
            "Save $12,000 for home renovation by August 2026"
        ]
        
        # Adjust suggestions based on risk profile
        if risk_profile == "Conservative":
            return base_suggestions[:8]  # Focus on safer goals
        elif risk_profile == "Aggressive":
            return base_suggestions[2:] + ["Invest $10,000 in growth stocks by June 2025"]  # More investment-focused
        else:
            return base_suggestions
    
    def explain_financial_term(self, term: str) -> str:
        """Explain a financial term using LLM"""
        if not self.ollama_available:
            return f"Sorry, I cannot explain '{term}' right now. Please consult a financial advisor or search online."
        
        try:
            system_prompt = (
                "You are a helpful financial advisor. Explain financial terms clearly and concisely. "
                "Provide a brief, easy-to-understand explanation with a simple example if helpful."
            )
            
            user_prompt = f"Please explain the financial term: {term}"
            
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            return response['message']['content']
            
        except Exception as e:
            return f"Sorry, I cannot explain '{term}' right now. Please consult a financial advisor."
