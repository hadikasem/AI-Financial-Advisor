# LLM Service for Recommendations and Goal Suggestions

import os
import json
import requests
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from enum import Enum

class LLMProvider(Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"

class LLMService:
    def __init__(self):
        # Configuration
        self.default_provider = os.getenv('DEFAULT_LLM_PROVIDER', 'openai').lower()
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'gemma3:4b')
        self.ollama_host = os.getenv('OLLAMA_HOST', 'http://host.docker.internal:11434')
        
        # Provider availability
        self.openai_available = False
        self.ollama_available = False
        self._initialized = False
    
    def _ensure_initialized(self):
        """Ensure the service is initialized"""
        if not self._initialized:
            self.openai_available = self._check_openai_availability()
            self.ollama_available = self._check_ollama_availability()
            self._initialized = True
    
    def _check_openai_availability(self) -> bool:
        """Check if OpenAI is available"""
        if not self.openai_api_key:
            print("OpenAI API key not found")
            return False
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            # Test with a simple request
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            
            if response.choices and response.choices[0].message.content:
                print(f"OpenAI {self.openai_model} is working correctly")
                return True
            else:
                print("OpenAI test failed: No response content")
                return False
                
        except Exception as e:
            print(f"OpenAI not available: {e}")
            return False
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available via HTTP API"""
        try:
            print(f"Checking Ollama at: {self.ollama_host}")
            
            # Get list of models
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=10)
            if response.status_code != 200:
                print(f"Ollama API not available: {response.status_code}")
                return False
            
            models_data = response.json()
            model_names = [model['name'] for model in models_data.get('models', [])]
            print(f"Available Ollama models: {model_names}")
            
            # Prioritize working models
            preferred_models = ['gemma3:4b', 'llama2', 'mistral', 'codellama', 'phi', 'gpt-oss:20b']
            model_found = False
            
            for preferred_model in preferred_models:
                if preferred_model in model_names:
                    self.ollama_model = preferred_model
                    print(f"Using preferred Ollama model: {self.ollama_model}")
                    model_found = True
                    break
            
            if not model_found and model_names:
                self.ollama_model = model_names[0]
                print(f"Using first available Ollama model: {self.ollama_model}")
            
            # Test the model with a simple request
            try:
                test_payload = {
                    "model": self.ollama_model,
                    "prompt": "Hi",
                    "stream": False
                }
                test_response = requests.post(
                    f"{self.ollama_host}/api/generate",
                    json=test_payload,
                    timeout=15
                )
                
                if test_response.status_code == 200:
                    print(f"Ollama model {self.ollama_model} is working correctly")
                    return True
                else:
                    print(f"Ollama model {self.ollama_model} test failed: {test_response.status_code}")
                    return False
            except requests.Timeout:
                print(f"Ollama model {self.ollama_model} test timed out - model may be too slow")
                return False
            except Exception as test_e:
                print(f"Ollama model {self.ollama_model} test failed: {test_e}")
                return False
                
        except Exception as e:
            print(f"Ollama not available: {e}")
            return False
    
    def _get_available_provider(self) -> Optional[LLMProvider]:
        """Get the best available provider based on configuration and availability"""
        self._ensure_initialized()
        
        # If default provider is available, use it
        if self.default_provider == 'openai' and self.openai_available:
            return LLMProvider.OPENAI
        elif self.default_provider == 'ollama' and self.ollama_available:
            return LLMProvider.OLLAMA
        
        # Fallback to any available provider
        if self.openai_available:
            return LLMProvider.OPENAI
        elif self.ollama_available:
            return LLMProvider.OLLAMA
        
        return None
    
    def _call_openai(self, messages: List[Dict[str, str]], max_tokens: int = 1000) -> str:
        """Call OpenAI API"""
        try:
            import openai
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            else:
                raise Exception("No response content from OpenAI")
                
        except Exception as e:
            print(f"OpenAI API call failed: {e}")
            raise
    
    def _call_ollama(self, prompt: str, max_tokens: int = 1000) -> str:
        """Call Ollama API"""
        try:
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens
                }
            }
            
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                raise Exception(f"Ollama API request failed: {response.status_code}")
                
        except Exception as e:
            print(f"Ollama API call failed: {e}")
            raise
    
    def _make_llm_request(self, system_prompt: str, user_content: str, max_tokens: int = 1000) -> str:
        """Make a request to the best available LLM provider"""
        provider = self._get_available_provider()
        
        if not provider:
            return "I'm sorry, no AI service is currently available. Please try again later."
        
        try:
            if provider == LLMProvider.OPENAI:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
                return self._call_openai(messages, max_tokens)
            else:  # OLLAMA
                prompt = f"System: {system_prompt}\n\nUser: {user_content}"
                return self._call_ollama(prompt, max_tokens)
                
        except Exception as e:
            print(f"LLM request failed with {provider.value}: {e}")
            
            # Try fallback provider
            if provider == LLMProvider.OPENAI and self.ollama_available:
                print("Falling back to Ollama")
                try:
                    prompt = f"System: {system_prompt}\n\nUser: {user_content}"
                    return self._call_ollama(prompt, max_tokens)
                except Exception as fallback_e:
                    print(f"Ollama fallback also failed: {fallback_e}")
            elif provider == LLMProvider.OLLAMA and self.openai_available:
                print("Falling back to OpenAI")
                try:
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ]
                    return self._call_openai(messages, max_tokens)
                except Exception as fallback_e:
                    print(f"OpenAI fallback also failed: {fallback_e}")
            
            return "I'm sorry, I encountered an error while processing your request. Please try again later."
    
    def get_help_response(self, question: str, context: str = "") -> str:
        """Get LLM response for help questions"""
        system_prompt = "You are a helpful financial assistant. Provide clear, accurate, and helpful answers to financial questions."
        user_prompt = f"Question: {question}\nContext: {context}\n\nPlease provide a helpful answer."
        
        return self._make_llm_request(system_prompt, user_prompt)
    
    def get_recommendations(self, user_id: str, goal_id: Optional[str] = None) -> List[str]:
        """Get personalized recommendations for a user"""
        provider = self._get_available_provider()
        print(f"DEBUG: LLM Provider available: {provider}")
        if not provider:
            raise RuntimeError("LLM is not available. Cannot generate personalized recommendations.")
        
        try:
            # Import database models only when needed
            from models import User, Assessment, Goal, ProgressSnapshot, Recommendation, db
            
            # Check if we have stored recommendations
            stored_recommendation = Recommendation.query.filter_by(
                user_id=user_id,
                goal_id=goal_id
            ).order_by(Recommendation.updated_at.desc()).first()
            
            if stored_recommendation:
                print(f"DEBUG: Returning stored recommendations for user {user_id}, goal {goal_id}")
                return stored_recommendation.recommendations
            
            # No stored recommendations, generate new ones
            print(f"DEBUG: No stored recommendations found, generating new ones for user {user_id}, goal {goal_id}")
            return self._generate_and_save_recommendations(user_id, goal_id)
            
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            raise RuntimeError(f"Failed to generate recommendations: {str(e)}")
    
    def _generate_and_save_recommendations(self, user_id: str, goal_id: Optional[str] = None) -> List[str]:
        """Generate new recommendations and save them to the database"""
        try:
            # Import database models only when needed
            from models import User, Assessment, Goal, ProgressSnapshot, Recommendation, db
            
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
                    context_data = {
                        'goal_id': goal_id,
                        'goal_name': goal.name,
                        'progress_pct': float(progress.progress_pct),
                        'pacing_status': progress.pacing_status,
                        'risk_profile': risk_profile
                    }
                else:
                    recommendations = self._generate_general_recommendations(risk_profile, assessment, user_id)
                    context_data = {
                        'goal_id': goal_id,
                        'goal_name': goal.name,
                        'risk_profile': risk_profile
                    }
            else:
                recommendations = self._generate_general_recommendations(risk_profile)
                context_data = {
                    'risk_profile': risk_profile
                }
            
            # Save recommendations to database
            recommendation_record = Recommendation(
                user_id=user_id,
                goal_id=goal_id,
                recommendations=recommendations,
                context_data=context_data
            )
            
            db.session.add(recommendation_record)
            db.session.commit()
            
            return recommendations
            
        except Exception as e:
            print(f"Error generating and saving recommendations: {e}")
            raise RuntimeError(f"Failed to generate recommendations: {str(e)}")
    
    def update_recommendations(self, user_id: str, goal_id: Optional[str] = None) -> List[str]:
        """Update recommendations based on current progress"""
        try:
            # Import database models only when needed
            from models import User, Assessment, Goal, ProgressSnapshot, Recommendation, db
            
            # Get user data
            user = User.query.get(user_id)
            if not user:
                return []
            
            # Get user's risk profile
            assessment = Assessment.query.filter_by(user_id=user_id, status='completed').first()
            risk_profile = assessment.risk_label if assessment else "Balanced"
            
            # Generate new recommendations based on current progress
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
                    context_data = {
                        'goal_id': goal_id,
                        'goal_name': goal.name,
                        'progress_pct': float(progress.progress_pct),
                        'pacing_status': progress.pacing_status,
                        'risk_profile': risk_profile
                    }
                else:
                    recommendations = self._generate_general_recommendations(risk_profile, assessment, user_id)
                    context_data = {
                        'goal_id': goal_id,
                        'goal_name': goal.name,
                        'risk_profile': risk_profile
                    }
            else:
                recommendations = self._generate_general_recommendations(risk_profile)
                context_data = {
                    'risk_profile': risk_profile
                }
            
            # Update or create recommendation record
            existing_recommendation = Recommendation.query.filter_by(
                user_id=user_id,
                goal_id=goal_id
            ).first()
            
            if existing_recommendation:
                # Update existing recommendation
                existing_recommendation.recommendations = recommendations
                existing_recommendation.context_data = context_data
                existing_recommendation.updated_at = datetime.utcnow()
            else:
                # Create new recommendation
                recommendation_record = Recommendation(
                    user_id=user_id,
                    goal_id=goal_id,
                    recommendations=recommendations,
                    context_data=context_data
                )
                db.session.add(recommendation_record)
            
            db.session.commit()
            
            return recommendations
            
        except Exception as e:
            print(f"Error updating recommendations: {e}")
            raise RuntimeError(f"Failed to update recommendations: {str(e)}")
    
    def generate_goal_suggestions(self, user_id: str, risk_profile: str) -> List[str]:
        """Generate personalized goal suggestions based on user's comprehensive profile"""
        provider = self._get_available_provider()
        if not provider:
            raise RuntimeError("LLM is not available. Cannot generate goal suggestions.")
        
        try:
            # Import database models only when needed
            from models import User, Assessment, Goal
            
            # Get user context
            user = User.query.get(user_id)
            assessment = Assessment.query.filter_by(user_id=user_id, status='completed').first()
            
            # Get user's previous goals (completed and ongoing)
            previous_goals = Goal.query.filter_by(user_id=user_id).order_by(Goal.created_at.desc()).all()
            
            # Format previous goals for the prompt
            formatted_previous_goals = ""
            if previous_goals:
                formatted_previous_goals = "Goals you already have:\n"
                for goal in previous_goals:
                    status_text = "✅ Completed" if goal.status == 'completed' else "🔄 Ongoing"
                    formatted_previous_goals += f"- {goal.name} ({goal.category}): ${float(goal.target_amount):,.0f} by {goal.target_date}, Status: {status_text}\n"
            else:
                formatted_previous_goals = "No previous goals."
            
            # Build comprehensive user profile
            assessment_details = ""
            if assessment:
                answers = assessment.answers
                assessment_details = f"""
Age: {answers.get('age', 'Not specified')} years old
Investment Time Horizon: {answers.get('horizon', 'Not specified')} years
Emergency Fund: {answers.get('emergency_fund_months', 'Not specified')} months of expenses
Dependents: {answers.get('dependents', 'Not specified')} people
Income Stability: {answers.get('income_stability', 'Not specified')}
Investment Experience: {answers.get('experience', 'Not specified')}
Loss Tolerance: {answers.get('loss_tolerance', 'Not specified')}
Monthly Savings Rate: {answers.get('savings_rate', 'Not specified')}%
Debt Load: {answers.get('debt_load', 'Not specified')}
Liquidity Need: {answers.get('liquidity_need', 'Not specified')}
Market Drop Reaction: {answers.get('reaction_scenario', 'Not specified')}
Investment Objective: {answers.get('investment_objective', 'Not specified')}
"""
            else:
                assessment_details = "No assessment data available."
            
            # Generate suggestions using LLM
            system_prompt = (
                "You are a financial planning assistant. Generate exactly 10 specific, "
                "personalized, actionable financial goal suggestions based on the user's comprehensive financial profile. "
                "Consider their assessment answers, risk profile, savings capacity, and previous goals. "
                "Each goal should include a specific amount and timeline. "
                "Be concrete and realistic. Avoid suggesting goals similar to ones they already have. "
                "Format each goal as a single line. "
                "IMPORTANT: Do not include numbering (1., 2., etc.) in your response. "
                "Each goal should be on a separate line without any numbering. "
                f"Use dates from {datetime.now().strftime('%B %Y')} onwards. Do not use past dates."
            )
            
            user_prompt = f"""
Generate 10 personalized financial goal suggestions for a user with:

USER FINANCIAL PROFILE:
Risk Profile: {risk_profile}
{assessment_details}

USER'S GOAL HISTORY:
{formatted_previous_goals}

Based on the user's comprehensive financial profile and their goal history, generate 10 diverse, personalized financial goal suggestions that:
1. Match their risk tolerance and financial capacity
2. Consider their previous goal interests and patterns
3. Cover different categories (emergency fund, retirement, vacation, education, home purchase, etc.)
4. Include specific amounts and realistic timelines
5. Avoid suggesting goals too similar to ones they already have

Provide diverse goals across different categories. Make sure the suggestions are practical and aligned with their financial situation.

CRITICAL: All dates must be from {datetime.now().strftime('%B %Y')} onwards. 
Current date is {datetime.now().strftime('%B %d, %Y')}.
"""
            
            response_text = self._make_llm_request(system_prompt, user_prompt, max_tokens=1500)
            
            # Parse response
            suggestions = []
            for line in response_text.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and len(line) > 10:
                    suggestions.append(line)
            
            return suggestions[:10] if suggestions else []
            
        except Exception as e:
            print(f"Error generating goal suggestions: {e}")
            raise RuntimeError(f"Failed to generate goal suggestions: {str(e)}")
    
    def _generate_goal_specific_recommendations(self, goal, progress, risk_profile: str) -> List[str]:
        """Generate recommendations specific to a goal's progress"""
        try:
            print(f"DEBUG: Generating goal-specific recommendations for goal: {goal.name}, progress: {float(progress.progress_pct)}%, risk: {risk_profile}")
            system_prompt = (
                "You are a financial coach. Based on the goal progress data, provide 3-5 "
                "specific, actionable recommendations to help the user achieve their goal. "
                "Be practical and realistic. Each recommendation should be 1-2 sentences. "
                "IMPORTANT: Do not include numbering (1., 2., etc.) in your response. "
                "Each recommendation should be on a separate line without any numbering."
            )
            
            user_prompt = f"""
            Goal: {goal.name}
            Category: {goal.category}
            Target Amount: ${float(goal.target_amount):,.2f}
            Target Date: {goal.target_date}
            Current Progress: {float(progress.progress_pct):.1f}%
            Pacing Status: {progress.pacing_status}
            Pacing Detail: {progress.pacing_detail}
            Risk Profile: {risk_profile}
            
            Provide specific recommendations to help achieve this goal.
            """
            
            print(f"DEBUG: Making LLM request for goal-specific recommendations")
            response_text = self._make_llm_request(system_prompt, user_prompt)
            print(f"DEBUG: LLM response received: {response_text[:100]}...")
            
            # Parse recommendations
            recommendations = []
            for line in response_text.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Clean up formatting (remove numbering, bullets, etc.)
                if line[0].isdigit() and ('.' in line[:3] or ')' in line[:3] or '-' in line[:3]):
                    # Remove numbering (e.g., "1) ", "1. ", "1- ")
                    if '. ' in line[:3]:
                        line = line.split('. ', 1)[1]
                    elif ') ' in line[:3]:
                        line = line.split(') ', 1)[1]
                    elif '- ' in line[:3]:
                        line = line.split('- ', 1)[1]
                        # Also remove "o " if present after the dash
                        if line.startswith('o '):
                            line = line[2:]
                elif line.startswith('- '):
                    line = line[2:]
                elif line.startswith('o '):
                    line = line[2:]
                
                if line and len(line) > 20:
                    recommendations.append(line)
            
            print(f"DEBUG: Parsed {len(recommendations)} goal-specific recommendations")
            return recommendations[:5] if recommendations else []
            
        except Exception as e:
            print(f"Error generating goal-specific recommendations: {e}")
            raise RuntimeError(f"Failed to generate goal-specific recommendations: {str(e)}")
    
    def _generate_general_recommendations(self, risk_profile: str, assessment=None, user_id: str = None) -> List[str]:
        """Generate personalized financial recommendations with full user context"""
        try:
            print(f"DEBUG: Generating personalized recommendations for risk profile: {risk_profile}")
            
            # Enhanced system prompt
            system_prompt = (
                "You are an expert financial advisor. Based on the user's detailed financial assessment, "
                "provide 5 personalized, actionable financial recommendations. "
                "Consider their age, income stability, savings habits, debt situation, and investment goals. "
                "Make each recommendation specific and relevant to their unique financial situation. "
                "Be practical and realistic. "
                "IMPORTANT: Do not include numbering (1., 2., etc.) in your response. "
                "Each recommendation should be on a separate line without any numbering."
            )
            
            # Build detailed user context from assessment answers
            user_context = ""
            
            if assessment and hasattr(assessment, 'answers'):
                answers = assessment.answers
                
                user_context = "USER FINANCIAL PROFILE:\n"
                user_context += f"Risk Profile: {risk_profile}\n"
                user_context += f"Risk Score: {assessment.risk_score}\n\n"
                
                user_context += "ASSESSMENT DETAILS:\n"
                
                # Age
                if 'age' in answers:
                    user_context += f"Age: {answers['age']} years old\n"
                
                # Investment horizon
                if 'horizon' in answers:
                    user_context += f"Investment Time Horizon: {answers['horizon']} years\n"
                
                # Emergency fund
                if 'emergency_fund_months' in answers:
                    user_context += f"Emergency Fund: {answers['emergency_fund_months']} months of expenses\n"
                
                # Dependents
                if 'dependents' in answers:
                    user_context += f"Dependents: {answers['dependents']} people\n"
                
                # Income stability
                if 'income_stability' in answers:
                    user_context += f"Income Stability: {answers['income_stability']}\n"
                
                # Investment experience
                if 'experience' in answers:
                    user_context += f"Investment Experience: {answers['experience']}\n"
                
                # Loss tolerance
                if 'loss_tolerance' in answers:
                    user_context += f"Loss Tolerance: {answers['loss_tolerance']}\n"
                
                # Savings rate
                if 'savings_rate' in answers:
                    user_context += f"Monthly Savings Rate: {answers['savings_rate']}%\n"
                
                # Debt load
                if 'debt_load' in answers:
                    user_context += f"Debt Load: {answers['debt_load']}\n"
                
                # Liquidity need
                if 'liquidity_need' in answers:
                    user_context += f"Potential Withdrawal Need: {answers['liquidity_need']}\n"
                
                # Reaction to market drops
                if 'reaction_scenario' in answers:
                    user_context += f"Market Drop Reaction: {answers['reaction_scenario']}\n"
                
                # Investment objective
                if 'investment_objective' in answers:
                    user_context += f"Investment Objective: {answers['investment_objective']}\n"
                
                user_context += f"\nRisk Description: {assessment.risk_description or 'No additional description'}\n"
            else:
                # Fallback if no assessment data
                user_context = f"Risk Profile: {risk_profile}\n"
            
            # Enhanced user prompt
            user_prompt = f"""
Based on the following detailed financial assessment, provide 5 personalized financial recommendations:

{user_context}

Please provide specific, actionable recommendations that are tailored to this user's unique financial situation.
Consider their age, income stability, savings capacity, debt situation, and investment goals.
Be practical and realistic with your suggestions.
"""
            
            print(f"DEBUG: Making LLM request with personalized context")
            response_text = self._make_llm_request(system_prompt, user_prompt, max_tokens=1500)
            print(f"DEBUG: LLM response received: {response_text[:200]}...")
            
            # Parse recommendations
            recommendations = []
            for line in response_text.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Clean up formatting (remove numbering, bullets, etc.)
                if line[0].isdigit() and ('.' in line[:3] or ')' in line[:3] or '-' in line[:3]):
                    # Remove numbering (e.g., "1) ", "1. ", "1- ")
                    if '. ' in line[:3]:
                        line = line.split('. ', 1)[1]
                    elif ') ' in line[:3]:
                        line = line.split(') ', 1)[1]
                    elif '- ' in line[:3]:
                        line = line.split('- ', 1)[1]
                        # Also remove "o " if present after the dash
                        if line.startswith('o '):
                            line = line[2:]
                elif line.startswith('- '):
                    line = line[2:]
                elif line.startswith('o '):
                    line = line[2:]
                
                if line and len(line) > 20:
                    recommendations.append(line)
            
            print(f"DEBUG: Parsed {len(recommendations)} recommendations")
            return recommendations[:5] if recommendations else []
            
        except Exception as e:
            print(f"Error generating general recommendations: {e}")
            raise RuntimeError(f"Failed to generate general recommendations: {str(e)}")
    
    def explain_financial_term(self, term: str) -> str:
        """Explain a financial term using LLM"""
        provider = self._get_available_provider()
        if not provider:
            return f"Sorry, I cannot explain '{term}' right now. Please consult a financial advisor or search online."
        
        try:
            system_prompt = (
                "You are a helpful financial advisor. Explain financial terms clearly and concisely. "
                "Provide a brief, easy-to-understand explanation with a simple example if helpful."
            )
            
            user_prompt = f"Please explain the financial term: {term}"
            
            return self._make_llm_request(system_prompt, user_prompt)
            
        except Exception as e:
            return f"Sorry, I cannot explain '{term}' right now. Please consult a financial advisor."
    
    def get_available_models(self) -> List[str]:
        """Get list of available models for debugging"""
        models = []
        
        if self.openai_available:
            models.append(f"OpenAI: {self.openai_model}")
        
        if self.ollama_available:
            try:
                response = requests.get(f"{self.ollama_host}/api/tags", timeout=10)
                if response.status_code == 200:
                    models_data = response.json()
                    ollama_models = [model['name'] for model in models_data.get('models', [])]
                    models.extend([f"Ollama: {model}" for model in ollama_models])
            except Exception as e:
                print(f"Error getting Ollama models: {e}")
        
        return models
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        self._ensure_initialized()
        
        return {
            'default_provider': self.default_provider,
            'openai_available': self.openai_available,
            'openai_model': self.openai_model,
            'ollama_available': self.ollama_available,
            'ollama_model': self.ollama_model,
            'ollama_host': self.ollama_host,
            'current_provider': self._get_available_provider().value if self._get_available_provider() else None
        }
    
    def generate_personalized_advice(self, user_id: str, goal_context: dict) -> str:
        """Generate personalized financial advice for a specific goal"""
        provider = self._get_available_provider()
        if not provider:
            return "Personalized advice is currently unavailable. Please try again later."
        
        try:
            # Import models
            from models import User, Assessment, Goal, Transaction, Account
            from datetime import timedelta
            
            # Get full user context
            user = User.query.get(user_id)
            assessment = Assessment.query.filter_by(user_id=user_id, status='completed').first()
            goal_id = goal_context.get('goal_id')  # If available
            
            # Prepare basic goal details
            goal_name = goal_context.get('goal_name', 'your goal')
            goal_category = goal_context.get('goal_category', 'general')
            current_amount = float(goal_context.get('current_amount', 0))
            target_amount = float(goal_context.get('target_amount', 0))
            progress_percentage = float(goal_context.get('progress_percentage', 0))
            timeline_progress = float(goal_context.get('timeline_progress', 0))
            days_remaining = int(goal_context.get('days_remaining', 0))
            user_risk_profile = goal_context.get('user_risk_profile', 'Balanced')
            savings_rate = float(goal_context.get('savings_rate', 10))
            
            # Get ALL user's transactions for this goal in last 30 days
            thirty_days_ago = date.today() - timedelta(days=30)
            
            # Query all transactions for this goal in the last 30 days
            account = None
            if goal_id:
                goal_obj = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
                if goal_obj and goal_obj.account_id:
                    account = Account.query.get(goal_obj.account_id)
            
            recent_transactions = []
            if account:
                recent_transactions = Transaction.query.filter(
                    Transaction.account_id == account.id,
                    Transaction.user_id == user_id,
                    Transaction.date >= thirty_days_ago
                ).order_by(Transaction.date.desc()).all()
            
            # Convert to list of dicts
            transactions_list = []
            for tx in recent_transactions:
                transactions_list.append({
                    'description': tx.description or 'Transaction',
                    'amount': float(tx.amount),
                    'category': tx.category or 'Other',
                    'date': tx.date.isoformat(),
                    'type': tx.transaction_type
                })
            
            # Get top 5 highest transactions
            top_transactions = sorted(transactions_list, key=lambda x: abs(x['amount']), reverse=True)[:5]
            
            # Get bottom 5 lowest transactions (smallest amounts)
            bottom_transactions = sorted(transactions_list, key=lambda x: abs(x['amount']))[:5]
            
            # Get all assessment details
            assessment_details = ""
            if assessment:
                answers = assessment.answers
                assessment_details = f"""
Age: {answers.get('age', 'Not specified')} years old
Investment Time Horizon: {answers.get('horizon', 'Not specified')} years
Emergency Fund: {answers.get('emergency_fund_months', 'Not specified')} months
Dependents: {answers.get('dependents', 'Not specified')} people
Income Stability: {answers.get('income_stability', 'Not specified')}
Investment Experience: {answers.get('experience', 'Not specified')}
Loss Tolerance: {answers.get('loss_tolerance', 'Not specified')}
Monthly Savings Rate: {savings_rate}%
Debt Load: {answers.get('debt_load', 'Not specified')}
Liquidity Need: {answers.get('liquidity_need', 'Not specified')}
Market Drop Reaction: {answers.get('reaction_scenario', 'Not specified')}
Investment Objective: {answers.get('investment_objective', 'Not specified')}
"""
            
            # Create enhanced system prompt
            system_prompt = (
                "You are a personal financial advisor with access to the user's complete financial profile. "
                "Generate specific, actionable advice based on their actual transaction history, goal progress, "
                "and comprehensive assessment data. Be very specific with numbers, percentages, and concrete recommendations. "
                "IMPORTANT: Format your response as a numbered list of recommendations (1., 2., 3., etc.) "
                "with each recommendation on a separate line. Be concise but actionable (5-7 recommendations)."
            )
            
            user_prompt = f"""
USER FINANCIAL PROFILE:
Risk Profile: {user_risk_profile}
Savings Rate: {savings_rate}% of income

ASSESSMENT DETAILS:
{assessment_details}

CURRENT GOAL DETAILS:
Goal: {goal_name} ({goal_category})
Current Amount: ${current_amount:,.0f}
Target Amount: ${target_amount:,.0f}
Progress: {progress_percentage:.1f}%
Timeline Progress: {timeline_progress:.1f}%
Days Remaining: {days_remaining}

ALL TRANSACTIONS (Last 30 days):
Total Transactions: {len(transactions_list)}
{chr(10).join([f"{i+1}. {tx['description']}: ${tx['amount']:,.2f} ({tx['category']}) on {tx['date']}" for i, tx in enumerate(transactions_list)]) if transactions_list else "No transactions in last 30 days"}

Top 5 Highest Transactions:
{chr(10).join([f"{i+1}. {tx['description']}: ${tx['amount']:,.2f} ({tx['category']}) on {tx['date']}" for i, tx in enumerate(top_transactions)]) if top_transactions else "No high-value transactions"}

Bottom 5 Lowest Transactions:
{chr(10).join([f"{i+1}. {tx['description']}: ${tx['amount']:,.2f} ({tx['category']}) on {tx['date']}" for i, tx in enumerate(bottom_transactions)]) if bottom_transactions else "No low-value transactions"}

ANALYSIS REQUIRED:
1. Analyze spending patterns from top and bottom transactions
2. Compare timeline progress ({timeline_progress:.1f}%) vs amount progress ({progress_percentage:.1f}%)
3. Calculate exactly how much they need to save per month to reach their goal
4. Identify specific spending categories they can reduce
5. Consider their full assessment profile (age, experience, risk tolerance, etc.)

Generate 5-7 specific, actionable recommendations as a numbered list that:
- Reference their actual spending patterns
- Provide specific monthly savings targets
- Suggest concrete spending reductions
- Use their real transaction data
- Give exact numbers and percentages
- Consider their full financial assessment profile
"""
            
            # Generate advice using LLM
            if provider == LLMProvider.OPENAI:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=800,
                    temperature=0.7
                )
                advice = response.choices[0].message.content.strip()
            else:
                # Fallback for other providers - generate numbered list
                remaining_amount = float(target_amount) - float(current_amount)
                monthly_target = remaining_amount / max(int(days_remaining) / 30, 1) if int(days_remaining) > 0 else remaining_amount
                
                if progress_percentage > timeline_progress:
                    advice = f"1. Great progress! You're ahead by {progress_percentage - timeline_progress:.1f}%. Save ${monthly_target:,.0f} monthly to reach your goal.\n2. Increase your savings rate from {int(savings_rate)}% to {min(int(savings_rate) + 5, 30)}% to maintain momentum.\n3. Review your top spending categories and reduce by 10-15%."
                elif progress_percentage < timeline_progress:
                    advice = f"1. You're behind by {timeline_progress - progress_percentage:.1f}%. Increase monthly savings to ${monthly_target:,.0f}.\n2. Reduce discretionary spending by 15-20% to catch up.\n3. Consider optimizing your {len(transactions_list)} recent transactions to increase savings capacity."
                else:
                    advice = f"1. You're on track! Maintain saving ${monthly_target:,.0f} monthly.\n2. Your {int(savings_rate)}% savings rate is working well.\n3. Continue monitoring your {len(transactions_list)} recent transactions to optimize spending."
            
            return advice
            
        except Exception as e:
            print(f"Error generating personalized advice: {str(e)}")
            # More specific fallback advice as numbered list
            remaining_amount = float(target_amount) - float(current_amount)
            monthly_target = remaining_amount / max(int(days_remaining) / 30, 1) if int(days_remaining) > 0 else remaining_amount
            return f"1. Based on {progress_percentage:.1f}% progress toward {goal_name}, save ${monthly_target:,.0f} monthly.\n2. Review your budget to increase savings rate from {int(savings_rate)}% to {min(int(savings_rate) + 5, 30)}%.\n3. Track spending patterns to identify areas for improvement."
    