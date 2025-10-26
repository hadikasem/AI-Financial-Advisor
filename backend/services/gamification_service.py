# Gamification Service for Risk Assessment and Goal Tracking App

from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from models import db, User, Goal
import json

class GamificationService:
    """Service for handling gamification features like milestones and streaks"""
    
    def __init__(self):
        self.milestones = [
            {"level": "🥉 First Goal", "amount": 1000, "points": 10},
            {"level": "🥈 Goal Crusher", "amount": 5000, "points": 25},
            {"level": "🥇 Savings Master", "amount": 10000, "points": 50},
            {"level": "💎 Financial Wizard", "amount": 25000, "points": 100},
            {"level": "🏆 Legendary Saver", "amount": 50000, "points": 200}
        ]
        
        self.level_thresholds = {
            "Bronze": 0,
            "Silver": 100,
            "Gold": 250,
            "Diamond": 500,
            "Legendary": 1000
        }
    
    def check_milestones(self, user_id: str, goal_amount: float) -> Dict[str, Any]:
        """Check if user has achieved any new milestones"""
        user = User.query.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        
        achieved_milestones = []
        new_milestones = []
        
        # Check each milestone
        for milestone in self.milestones:
            if goal_amount >= milestone["amount"]:
                # Check if this milestone was already achieved
                if not self._is_milestone_achieved(user, milestone):
                    new_milestones.append(milestone)
                    self._award_points(user, milestone["points"])
                
                achieved_milestones.append(milestone)
        
        # Update user level based on total points
        self._update_user_level(user)
        
        try:
            db.session.commit()
            return {
                "success": True,
                "achieved_milestones": achieved_milestones,
                "new_milestones": new_milestones,
                "total_points": user.total_points,
                "level": user.level
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    def update_streak(self, user_id: str) -> Dict[str, Any]:
        """Update user's streak based on activity"""
        user = User.query.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        
        today = date.today()
        
        # If no last activity date, start streak
        if not user.last_activity_date:
            user.current_streak = 1
            user.last_activity_date = today
            streak_bonus = 0
        else:
            days_since_last_activity = (today - user.last_activity_date).days
            
            if days_since_last_activity == 1:
                # Consecutive day - increment streak
                user.current_streak += 1
                streak_bonus = min(user.current_streak * 2, 20)  # Bonus points for streaks
            elif days_since_last_activity == 0:
                # Same day - no change
                streak_bonus = 0
            else:
                # Streak broken - reset
                user.current_streak = 1
                streak_bonus = 0
            
            user.last_activity_date = today
        
        # Award streak bonus points
        if streak_bonus > 0:
            self._award_points(user, streak_bonus)
        
        # Update user level
        self._update_user_level(user)
        
        try:
            db.session.commit()
            return {
                "success": True,
                "current_streak": user.current_streak,
                "streak_bonus": streak_bonus,
                "total_points": user.total_points,
                "level": user.level
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    def simulate_next_day_streak(self, user_id: str) -> Dict[str, Any]:
        """
        Simulate streak as if user logged in the next day (for testing)
        This advances last_activity_date by 1 day to test streak logic
        """
        user = User.query.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Get the current last_activity_date, or use today if none
        if not user.last_activity_date:
            # First time - start with today
            user.last_activity_date = date.today()
            user.current_streak = 1
            streak_bonus = 0
        else:
            # Simulate "next day" - add 1 day to last_activity_date
            user.last_activity_date += timedelta(days=1)
            
            # Check if this represents consecutive days
            # Since we're advancing by 1 day, this simulates consecutive login
            user.current_streak += 1
            streak_bonus = min(user.current_streak * 2, 20)  # Bonus points for streaks
        
        # Award streak bonus points
        if streak_bonus > 0:
            self._award_points(user, streak_bonus)
        
        # Update user level
        self._update_user_level(user)
        
        try:
            db.session.commit()
            return {
                "success": True,
                "current_streak": user.current_streak,
                "streak_bonus": streak_bonus,
                "total_points": user.total_points,
                "level": user.level,
                "simulated_date": user.last_activity_date.isoformat(),
                "message": f"Streak simulated for {user.last_activity_date}"
            }
        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}
    
    def get_user_gamification_data(self, user_id: str) -> Dict[str, Any]:
        """Get all gamification data for a user"""
        user = User.query.get(user_id)
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Get user's goals to calculate total saved
        goals = Goal.query.filter_by(user_id=user_id).all()
        total_saved = sum(float(goal.current_amount) for goal in goals)
        
        # Calculate next milestone
        next_milestone = None
        for milestone in self.milestones:
            if total_saved < milestone["amount"]:
                next_milestone = milestone
                break
        
        # Calculate next level
        next_level = None
        current_points = user.total_points
        for level, threshold in self.level_thresholds.items():
            if current_points < threshold:
                next_level = {"name": level, "points_needed": threshold - current_points}
                break
        
        return {
            "success": True,
            "current_streak": user.current_streak,
            "total_points": user.total_points,
            "level": user.level,
            "total_saved": total_saved,
            "next_milestone": next_milestone,
            "next_level": next_level,
            "achieved_milestones": [m for m in self.milestones if total_saved >= m["amount"]]
        }
    
    def _is_milestone_achieved(self, user: User, milestone: Dict[str, Any]) -> bool:
        """Check if user has already achieved this milestone"""
        # For now, we'll assume milestones are achieved if user has enough points
        # In a more complex system, you'd store achieved milestones separately
        return user.total_points >= milestone["points"]
    
    def _award_points(self, user: User, points: int) -> None:
        """Award points to user"""
        user.total_points += points
    
    def _update_user_level(self, user: User) -> None:
        """Update user's level based on total points"""
        current_points = user.total_points
        
        # Find the highest level the user qualifies for
        for level, threshold in reversed(list(self.level_thresholds.items())):
            if current_points >= threshold:
                user.level = level
                break
    
    def get_leaderboard(self, limit: int = 10) -> Dict[str, Any]:
        """Get leaderboard of top users by points"""
        try:
            top_users = User.query.filter_by(is_active=True)\
                .order_by(User.total_points.desc())\
                .limit(limit)\
                .all()
            
            leaderboard = []
            for i, user in enumerate(top_users, 1):
                leaderboard.append({
                    "rank": i,
                    "username": user.username,
                    "level": user.level,
                    "total_points": user.total_points,
                    "current_streak": user.current_streak
                })
            
            return {
                "success": True,
                "leaderboard": leaderboard
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
