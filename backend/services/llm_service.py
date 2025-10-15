# LLM Service for Recommendations and Goal Suggestions

import os
import json
import requests
from datetime import datetime
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
            print("WARNING: No LLM provider available, using fallback recommendations")
            return self._get_fallback_recommendations()
        
        try:
            # Import database models only when needed
            from models import User, Assessment, Goal, ProgressSnapshot, Recommendation
            
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
            return self._get_fallback_recommendations()
    
    def _generate_and_save_recommendations(self, user_id: str, goal_id: Optional[str] = None) -> List[str]:
        """Generate new recommendations and save them to the database"""
        try:
            # Import database models only when needed
            from models import User, Assessment, Goal, ProgressSnapshot, Recommendation
            
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
                        'progress_pct': progress.progress_pct,
                        'pacing_status': progress.pacing_status,
                        'risk_profile': risk_profile
                    }
                else:
                    recommendations = self._generate_general_recommendations(risk_profile)
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
            return self._get_fallback_recommendations()
    
    def update_recommendations(self, user_id: str, goal_id: Optional[str] = None) -> List[str]:
        """Update recommendations based on current progress"""
        try:
            # Import database models only when needed
            from models import User, Assessment, Goal, ProgressSnapshot, Recommendation
            
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
                        'progress_pct': progress.progress_pct,
                        'pacing_status': progress.pacing_status,
                        'risk_profile': risk_profile
                    }
                else:
                    recommendations = self._generate_general_recommendations(risk_profile)
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
            return self._get_fallback_recommendations()
    
    def generate_goal_suggestions(self, user_id: str, risk_profile: str) -> List[str]:
        """Generate goal suggestions based on user's risk profile"""
        provider = self._get_available_provider()
        if not provider:
            return self._get_fallback_goal_suggestions(risk_profile)
        
        try:
            # Import database models only when needed
            from models import User, Assessment
            
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
                "Be concrete and realistic. Format each goal as a single line. "
                "IMPORTANT: Do not include numbering (1., 2., etc.) in your response. "
                "Each goal should be on a separate line without any numbering. "
                f"Use dates from {datetime.now().strftime('%B %Y')} onwards. Do not use past dates."
            )
            
            user_prompt = f"""
            Generate 10 financial goal suggestions for a user with:
            - Risk Profile: {context['risk_profile']}
            - Age: {context['user_age']} years old
            - Income Stability: {context['income_stability']}
            - Monthly Savings Rate: {context['savings_rate']}%
            
            Provide diverse goals across different categories like emergency fund, retirement, 
            vacation, education, home purchase, etc. Include specific amounts and timelines.
            
            CRITICAL: All dates must be from {datetime.now().strftime('%B %Y')} onwards. 
            Current date is {datetime.now().strftime('%B %d, %Y')}.
            """
            
            response_text = self._make_llm_request(system_prompt, user_prompt)
            
            # Parse response
            suggestions = []
            for line in response_text.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and len(line) > 10:
                    suggestions.append(line)
            
            return suggestions[:10] if suggestions else self._get_fallback_goal_suggestions(risk_profile)
            
        except Exception as e:
            print(f"Error generating goal suggestions: {e}")
            return self._get_fallback_goal_suggestions(risk_profile)
    
    def _generate_goal_specific_recommendations(self, goal, progress, risk_profile: str) -> List[str]:
        """Generate recommendations specific to a goal's progress"""
        try:
            print(f"DEBUG: Generating goal-specific recommendations for goal: {goal.name}, progress: {progress.progress_pct}%, risk: {risk_profile}")
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
            Target Amount: ${goal.target_amount:,.2f}
            Target Date: {goal.target_date}
            Current Progress: {progress.progress_pct:.1f}%
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
            return recommendations[:5] if recommendations else self._get_fallback_recommendations()
            
        except Exception as e:
            print(f"Error generating goal-specific recommendations: {e}")
            return self._get_fallback_recommendations()
    
    def _generate_general_recommendations(self, risk_profile: str) -> List[str]:
        """Generate general financial recommendations"""
        try:
            print(f"DEBUG: Generating general recommendations for risk profile: {risk_profile}")
            system_prompt = (
                "You are a financial advisor. Provide 5 general financial recommendations "
                "based on the user's risk profile. Be practical and actionable. "
                "IMPORTANT: Do not include numbering (1., 2., etc.) in your response. "
                "Each recommendation should be on a separate line without any numbering."
            )
            
            user_prompt = f"Provide general financial recommendations for someone with a {risk_profile} risk profile."
            
            print(f"DEBUG: Making LLM request for general recommendations")
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
            
            print(f"DEBUG: Parsed {len(recommendations)} recommendations")
            return recommendations[:5] if recommendations else self._get_fallback_recommendations()
            
        except Exception as e:
            print(f"Error generating general recommendations: {e}")
            return self._get_fallback_recommendations()
    
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
    
    def _get_fallback_recommendations(self) -> List[str]:
        """Fallback recommendations when LLM is not available"""
        print("WARNING: Using fallback recommendations - LLM may not be available")
        return [
            "Consider increasing your monthly savings by 5-10% to accelerate goal achievement",
            "Review your spending categories to identify areas for cost reduction", 
            "Set up automatic transfers to your savings account on payday",
            "Consider diversifying your investments based on your risk tolerance",
            "Regularly review and adjust your goals based on life changes"
        ]
    
    def _get_fallback_goal_suggestions(self, risk_profile: str) -> List[str]:
        """Fallback goal suggestions when LLM is not available"""
        current_year = datetime.now().year
        next_year = current_year + 1
        
        base_suggestions = [
            f"Build emergency fund of $10,000 by December {current_year}",
            f"Save $5,000 for vacation by June {next_year}",
            f"Contribute $6,000 to Roth IRA by April {next_year}",
            f"Save $20,000 for home down payment by December {next_year + 1}",
            f"Pay off $15,000 credit card debt by September {next_year}",
            f"Save $2,000 for car maintenance fund by March {next_year}",
            f"Invest $3,000 in index funds by May {next_year}",
            f"Save $8,000 for children's education by December {next_year + 2}",
            f"Build $25,000 emergency fund by December {next_year}",
            f"Save $12,000 for home renovation by August {next_year + 1}"
        ]
        
        # Adjust suggestions based on risk profile
        if risk_profile == "Conservative":
            return base_suggestions[:8]  # Focus on safer goals
        elif risk_profile == "Aggressive":
            return base_suggestions[2:] + [f"Invest $10,000 in growth stocks by June {next_year}"]  # More investment-focused
        else:
            return base_suggestions