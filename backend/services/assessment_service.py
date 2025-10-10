# Assessment Service for Risk Assessment Management

from models import db, User, Assessment
from datetime import datetime
import json
import uuid
from typing import Dict, List, Optional, Any

class AssessmentService:
    def __init__(self):
        self.questions = [
            {
                "id": "age",
                "question": "How old are you? (whole years)",
                "type": "number",
                "validation": {"min": 18, "max": 120},
                "weight": 1.0
            },
            {
                "id": "horizon",
                "question": "What is your investment time horizon in YEARS? (0–80)",
                "type": "number",
                "validation": {"min": 0, "max": 80},
                "weight": 1.2
            },
            {
                "id": "emergency_fund_months",
                "question": "Emergency fund size in MONTHS of essential expenses? (0–120)",
                "type": "number",
                "validation": {"min": 0, "max": 120},
                "weight": 0.8
            },
            {
                "id": "dependents",
                "question": "How many people rely on your income (dependents)? (0–20)",
                "type": "number",
                "validation": {"min": 0, "max": 20},
                "weight": 0.6
            },
            {
                "id": "income_stability",
                "question": "How stable is your income?",
                "type": "multiple_choice",
                "options": ["Very unstable", "Somewhat stable", "Stable", "Very stable"],
                "weight": 0.8
            },
            {
                "id": "experience",
                "question": "What is your investing experience level?",
                "type": "multiple_choice",
                "options": ["Beginner", "Some experience", "Experienced", "Advanced/Pro"],
                "weight": 0.9
            },
            {
                "id": "loss_tolerance",
                "question": "How do you feel about temporary losses (drawdowns)?",
                "type": "multiple_choice",
                "options": [
                    "I can't tolerate losses",
                    "Small dips are okay",
                    "Volatility is fine if returns are higher",
                    "I'm comfortable with big swings"
                ],
                "weight": 1.2
            },
            {
                "id": "savings_rate",
                "question": "Roughly what percent of your income do you save/invest monthly? (0–100%)",
                "type": "number",
                "validation": {"min": 0, "max": 100},
                "weight": 0.7
            },
            {
                "id": "debt_load",
                "question": "How would you describe your current debt load (relative to income)?",
                "type": "multiple_choice",
                "options": [
                    "No/low debt (<20%)",
                    "Manageable (20-35%)",
                    "Moderate (35-50%)",
                    "High (>50%)"
                ],
                "weight": 0.8
            },
            {
                "id": "liquidity_need",
                "question": "When might you need to withdraw a significant portion of this money?",
                "type": "multiple_choice",
                "options": ["< 1 year", "1–3 years", "> 3 years", "Not sure"],
                "weight": 1.0
            },
            {
                "id": "reaction_scenario",
                "question": "Your portfolio drops 20% in a month. What do you do?",
                "type": "multiple_choice",
                "options": ["Sell immediately", "Wait a bit", "Hold", "Buy more"],
                "weight": 1.3
            },
            {
                "id": "investment_objective",
                "question": "What is your primary investment objective?",
                "type": "multiple_choice",
                "options": [
                    "Capital preservation",
                    "Income",
                    "Balanced (growth + income)",
                    "Growth"
                ],
                "weight": 0.9
            }
        ]
    
    def start_assessment(self, user_id: str) -> Dict[str, Any]:
        """Start a new assessment for a user"""
        # Check if user has an incomplete assessment
        existing_assessment = Assessment.query.filter_by(
            user_id=user_id, 
            status='in_progress'
        ).first()
        
        if existing_assessment:
            # Return existing assessment
            current_question = self._get_next_question(existing_assessment.answers)
            return {
                'id': existing_assessment.id,
                'current_question': current_question,
                'answers': existing_assessment.answers
            }
        
        # Create new assessment
        assessment = Assessment(
            user_id=user_id,
            answers={},
            status='in_progress'
        )
        
        db.session.add(assessment)
        db.session.commit()
        
        # Get first question
        current_question = self._get_next_question({})
        
        return {
            'id': assessment.id,
            'current_question': current_question,
            'answers': {}
        }
    
    def process_answer(self, user_id: str, question_id: str, answer: str) -> Dict[str, Any]:
        """Process a user's answer to a question"""
        assessment = Assessment.query.filter_by(
            user_id=user_id,
            status='in_progress'
        ).first()
        
        if not assessment:
            raise ValueError("No active assessment found")
        
        # Validate answer
        question = self._get_question_by_id(question_id)
        if not question:
            raise ValueError("Invalid question ID")
        
        validated_answer = self._validate_answer(question, answer)
        if not validated_answer['valid']:
            return {
                'error': validated_answer['error'],
                'current_question': question
            }
        
        # Store answer
        assessment.answers[question_id] = validated_answer['value']
        # Force SQLAlchemy to detect the change
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(assessment, 'answers')
        db.session.commit()
        
        # Get next question
        next_question = self._get_next_question(assessment.answers)
        
        if next_question is None:
            # Assessment complete
            return {
                'message': 'Assessment completed',
                'assessment_id': assessment.id,
                'next_step': 'complete_assessment'
            }
        
        return {
            'message': 'Answer recorded',
            'current_question': next_question,
            'answers': assessment.answers
        }
    
    def update_answer(self, user_id: str, question_id: str, answer: str) -> Dict[str, Any]:
        """Update an existing answer"""
        assessment = Assessment.query.filter_by(
            user_id=user_id,
            status='in_progress'
        ).first()
        
        if not assessment:
            raise ValueError("No active assessment found")
        
        # Validate answer
        question = self._get_question_by_id(question_id)
        if not question:
            raise ValueError("Invalid question ID")
        
        validated_answer = self._validate_answer(question, answer)
        if not validated_answer['valid']:
            return {
                'error': validated_answer['error'],
                'current_question': question
            }
        
        # Update answer
        assessment.answers[question_id] = validated_answer['value']
        # Force SQLAlchemy to detect the change
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(assessment, 'answers')
        db.session.commit()
        
        return {
            'message': 'Answer updated successfully',
            'answers': assessment.answers
        }

    def complete_assessment(self, user_id: str) -> Dict[str, Any]:
        """Complete the assessment and calculate risk score"""
        assessment = Assessment.query.filter_by(
            user_id=user_id,
            status='in_progress'
        ).first()
        
        if not assessment:
            raise ValueError("No active assessment found")
        
        # Calculate risk score
        risk_score, risk_label, risk_description, individual_scores = self._calculate_risk_score(assessment.answers)
        
        # Update assessment
        assessment.risk_score = risk_score
        assessment.risk_label = risk_label
        assessment.risk_description = risk_description
        assessment.individual_scores = individual_scores
        assessment.question_weights = {q['id']: q['weight'] for q in self.questions}
        assessment.status = 'completed'
        assessment.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return {
            'message': 'Assessment completed successfully',
            'assessment': assessment.to_dict(),
            'risk_profile': {
                'score': risk_score,
                'label': risk_label,
                'description': risk_description
            }
        }
    
    def _get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        """Get question by ID"""
        for question in self.questions:
            if question['id'] == question_id:
                return question
        return None
    
    def _get_next_question(self, answers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Get the next unanswered question"""
        for question in self.questions:
            if question['id'] not in answers:
                return question
        return None
    
    def _validate_answer(self, question: Dict[str, Any], answer: str) -> Dict[str, Any]:
        """Validate user's answer"""
        if question['type'] == 'number':
            try:
                value = float(answer)
                validation = question.get('validation', {})
                
                if 'min' in validation and value < validation['min']:
                    return {'valid': False, 'error': f'Value must be at least {validation["min"]}'}
                
                if 'max' in validation and value > validation['max']:
                    return {'valid': False, 'error': f'Value must be at most {validation["max"]}'}
                
                return {'valid': True, 'value': str(value)}
            except ValueError:
                return {'valid': False, 'error': 'Please enter a valid number'}
        
        elif question['type'] == 'multiple_choice':
            options = question.get('options', [])
            if answer not in options:
                return {'valid': False, 'error': f'Please select one of: {", ".join(options)}'}
            
            return {'valid': True, 'value': answer}
        
        return {'valid': True, 'value': answer}
    
    def _calculate_risk_score(self, answers: Dict[str, str]) -> tuple:
        """Calculate risk score based on answers"""
        total_score = 0.0
        total_weight = 0.0
        individual_scores = {}
        
        for question in self.questions:
            question_id = question['id']
            if question_id not in answers:
                continue
            
            answer = answers[question_id]
            score = self._score_question(question_id, answer)
            weight = question['weight']
            
            individual_scores[question_id] = score
            total_score += score * weight
            total_weight += weight
        
        if total_weight == 0:
            risk_score = 50.0
        else:
            risk_score = round(total_score / total_weight, 2)
        
        risk_label, risk_description = self._get_risk_bucket(risk_score)
        
        return risk_score, risk_label, risk_description, individual_scores
    
    def _score_question(self, question_id: str, answer: str) -> float:
        """Score individual question based on answer"""
        scoring_functions = {
            'age': self._score_age,
            'horizon': self._score_horizon,
            'emergency_fund_months': self._score_emergency_months,
            'dependents': self._score_dependents,
            'income_stability': self._score_income_stability,
            'experience': self._score_experience,
            'loss_tolerance': self._score_loss_tolerance,
            'savings_rate': self._score_savings_rate,
            'debt_load': self._score_debt_load,
            'liquidity_need': self._score_liquidity_need,
            'reaction_scenario': self._score_reaction_scenario,
            'investment_objective': self._score_objective
        }
        
        if question_id in scoring_functions:
            return scoring_functions[question_id](answer)
        
        return 50.0  # Default score
    
    def _score_age(self, answer: str) -> float:
        age = int(float(answer))
        if age < 30: return 85.0
        if age < 40: return 70.0
        if age < 50: return 55.0
        if age < 60: return 40.0
        return 25.0
    
    def _score_horizon(self, answer: str) -> float:
        yrs = int(float(answer))
        if yrs >= 10: return 85.0
        if yrs >= 5: return 65.0
        if yrs >= 2: return 45.0
        return 25.0
    
    def _score_emergency_months(self, answer: str) -> float:
        m = int(float(answer))
        if m >= 6: return 85.0
        if m >= 3: return 70.0
        if m >= 1: return 50.0
        return 30.0
    
    def _score_dependents(self, answer: str) -> float:
        n = int(float(answer))
        if n == 0: return 85.0
        if n <= 2: return 70.0
        if n <= 4: return 50.0
        return 35.0
    
    def _score_income_stability(self, answer: str) -> float:
        stability_map = {
            "Very unstable": 30.0,
            "Somewhat stable": 50.0,
            "Stable": 70.0,
            "Very stable": 85.0
        }
        return stability_map.get(answer, 55.0)
    
    def _score_experience(self, answer: str) -> float:
        experience_map = {
            "Beginner": 25.0,
            "Some experience": 45.0,
            "Experienced": 65.0,
            "Advanced/Pro": 85.0
        }
        return experience_map.get(answer, 50.0)
    
    def _score_loss_tolerance(self, answer: str) -> float:
        tolerance_map = {
            "I can't tolerate losses": 20.0,
            "Small dips are okay": 40.0,
            "Volatility is fine if returns are higher": 70.0,
            "I'm comfortable with big swings": 90.0
        }
        return tolerance_map.get(answer, 50.0)
    
    def _score_savings_rate(self, answer: str) -> float:
        v = float(answer)
        if v >= 20: return 85.0
        if v >= 10: return 65.0
        if v >= 5: return 50.0
        return 35.0
    
    def _score_debt_load(self, answer: str) -> float:
        debt_map = {
            "No/low debt (<20%)": 85.0,
            "Manageable (20-35%)": 65.0,
            "Moderate (35-50%)": 45.0,
            "High (>50%)": 30.0
        }
        return debt_map.get(answer, 50.0)
    
    def _score_liquidity_need(self, answer: str) -> float:
        liquidity_map = {
            "< 1 year": 30.0,
            "1–3 years": 65.0,
            "> 3 years": 85.0,
            "Not sure": 50.0
        }
        return liquidity_map.get(answer, 50.0)
    
    def _score_reaction_scenario(self, answer: str) -> float:
        reaction_map = {
            "Sell immediately": 25.0,
            "Wait a bit": 45.0,
            "Hold": 70.0,
            "Buy more": 90.0
        }
        return reaction_map.get(answer, 50.0)
    
    def _score_objective(self, answer: str) -> float:
        objective_map = {
            "Capital preservation": 35.0,
            "Income": 55.0,
            "Balanced (growth + income)": 70.0,
            "Growth": 85.0
        }
        return objective_map.get(answer, 55.0)
    
    def _get_risk_bucket(self, score: float) -> tuple:
        """Convert risk score to risk bucket and description"""
        if score < 35:
            return ("Conservative", "Prefers capital preservation and lower volatility; accepts lower expected returns.")
        if score < 55:
            return ("Moderately Conservative", "Comfortable with some volatility; leans toward income and balanced strategies.")
        if score < 70:
            return ("Balanced", "Accepts meaningful ups and downs for moderate growth potential.")
        if score < 85:
            return ("Moderately Aggressive", "Comfortable with higher volatility for higher long-term growth potential.")
        return ("Aggressive", "Seeks maximum growth; comfortable with substantial volatility and drawdowns.")
