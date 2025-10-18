# Goal Service for Goal Management

from models import db, User, Goal, GoalCategory
from datetime import datetime, date
import json
import uuid
from typing import Dict, List, Optional, Any

class GoalService:
    def __init__(self):
        self.predefined_categories = [category.value for category in GoalCategory]
    
    def get_user_goals(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all goals for a user (both active and completed)"""
        goals = Goal.query.filter_by(user_id=user_id).filter(Goal.status.in_(['active', 'completed'])).all()
        return [goal.to_dict() for goal in goals]
    
    def create_goal(self, user_id: str, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new goal for a user"""
        # Validate category
        if goal_data['category'] not in self.predefined_categories:
            raise ValueError(f"Invalid category. Must be one of: {', '.join(self.predefined_categories)}")
        
        # Parse target date
        if isinstance(goal_data['target_date'], str):
            target_date = datetime.fromisoformat(goal_data['target_date']).date()
        else:
            target_date = goal_data['target_date']
        
        # Create goal
        goal = Goal(
            user_id=user_id,
            name=goal_data['name'],
            description=goal_data.get('description', ''),
            category=goal_data['category'],
            target_amount=float(goal_data['target_amount']),
            target_date=target_date,
            start_amount=float(goal_data.get('start_amount', 0.0)),
            start_date=date.today(),
            current_amount=float(goal_data.get('start_amount', 0.0))
        )
        
        db.session.add(goal)
        db.session.commit()
        
        return goal.to_dict()
    
    def delete_goal(self, user_id: str, goal_id: str) -> None:
        """Delete a goal (soft delete by setting status to deleted)"""
        goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
        
        if not goal:
            raise ValueError("Goal not found")
        
        goal.status = 'deleted'
        goal.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_goal_progress(self, user_id: str, goal_id: str, current_amount: float) -> Dict[str, Any]:
        """Update the current amount for a goal"""
        goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
        
        if not goal:
            raise ValueError("Goal not found")
        
        goal.current_amount = current_amount
        goal.updated_at = datetime.utcnow()
        db.session.commit()
        
        return goal.to_dict()
    
    def get_goal_by_id(self, user_id: str, goal_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific goal by ID"""
        goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
        
        if not goal:
            return None
        
        return goal.to_dict()
    
    def get_goals_by_category(self, user_id: str, category: str) -> List[Dict[str, Any]]:
        """Get goals filtered by category"""
        goals = Goal.query.filter_by(
            user_id=user_id, 
            category=category, 
            status='active'
        ).all()
        
        return [goal.to_dict() for goal in goals]
    
    def get_goal_categories(self) -> List[str]:
        """Get all predefined goal categories"""
        return self.predefined_categories
    
    def calculate_goal_progress(self, goal: Goal) -> Dict[str, Any]:
        """Calculate progress metrics for a goal"""
        total_needed = float(goal.target_amount) - float(goal.start_amount)
        
        if total_needed <= 0:
            progress_pct = 100.0
        else:
            progress_pct = max(0.0, min(100.0, 
                ((float(goal.current_amount) - float(goal.start_amount)) / total_needed) * 100.0))
        
        # Calculate days remaining
        today = date.today()
        days_remaining = (goal.target_date - today).days
        
        # Calculate daily target
        if days_remaining > 0:
            daily_target = total_needed / days_remaining
        else:
            daily_target = 0.0
        
        return {
            'progress_pct': progress_pct,
            'days_remaining': days_remaining,
            'daily_target': daily_target,
            'total_needed': total_needed,
            'current_amount': float(goal.current_amount),
            'target_amount': float(goal.target_amount),
            'start_amount': float(goal.start_amount)
        }
    
    def get_goal_suggestions(self, user_id: str) -> List[str]:
        """Get goal suggestions for a user based on their risk profile"""
        return self.generate_goal_suggestions(user_id, request_more=False)
    
    def generate_goal_suggestions(self, user_id: str, request_more: bool = False, existing_suggestions: List[str] = None) -> List[str]:
        """Generate new goal suggestions using LLM"""
        # Import LLM service lazily to avoid initialization issues
        try:
            from .llm_service import LLMService
            llm_service = LLMService()
            
            # Get user's risk profile
            from models import Assessment
            assessment = Assessment.query.filter_by(user_id=user_id, status='completed').first()
            
            if assessment:
                risk_label = assessment.risk_label or "Balanced"
                
                if request_more and existing_suggestions:
                    # Generate additional suggestions to append
                    new_suggestions = llm_service.generate_goal_suggestions(user_id, risk_label)
                    # Combine existing and new suggestions
                    combined_suggestions = existing_suggestions + new_suggestions
                    return combined_suggestions
                else:
                    # Generate fresh suggestions
                    return llm_service.generate_goal_suggestions(user_id, risk_label)
            else:
                return self._get_default_goal_suggestions()
        except Exception as e:
            print(f"Error generating goal suggestions: {e}")
            return self._get_default_goal_suggestions()
    
    def _get_default_goal_suggestions(self) -> List[str]:
        """Get default goal suggestions when no assessment is available"""
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
    
    def check_goal_completion_status(self, goal: Goal, simulated_current_date: date = None) -> Dict[str, Any]:
        """Check if goal is completed or target date reached"""
        if simulated_current_date is None:
            simulated_current_date = date.today()
        
        # Check if goal is already completed
        if goal.status == 'completed':
            return {
                'status': 'completed',
                'message': 'Goal already completed',
                'goal': goal.to_dict()
            }
        
        # Check if target amount is reached
        if goal.current_amount >= goal.target_amount:
            # Mark as completed
            goal.status = 'completed'
            goal.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Calculate how early it was completed
            days_early = (goal.target_date - simulated_current_date).days
            return {
                'status': 'completed',
                'message': f'Congratulations! You achieved your goal {abs(days_early)} days early!',
                'days_early': days_early,
                'goal': goal.to_dict()
            }
        
        # Check if target date is reached but amount not achieved
        if simulated_current_date >= goal.target_date:
            remaining_amount = float(goal.target_amount) - float(goal.current_amount)
            return {
                'status': 'target_date_reached',
                'message': f'Target date reached but goal not completed. You still need ${remaining_amount:,.2f}',
                'remaining_amount': remaining_amount,
                'goal': goal.to_dict()
            }
        
        # Goal is still active
        return {
            'status': 'active',
            'message': 'Goal is still in progress',
            'goal': goal.to_dict()
        }
    
    def extend_goal_target_date(self, user_id: str, goal_id: str, new_target_date: date) -> Dict[str, Any]:
        """Extend the target date for a goal"""
        goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
        
        if not goal:
            raise ValueError("Goal not found")
        
        if goal.status != 'active':
            raise ValueError("Only active goals can be extended")
        
        if new_target_date <= goal.target_date:
            raise ValueError("New target date must be after current target date")
        
        # Update the goal
        goal.target_date = new_target_date
        goal.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {
            'message': 'Goal target date extended successfully',
            'goal': goal.to_dict()
        }