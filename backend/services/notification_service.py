# Notification Service for Email, In-App, and Push Notifications

from models import db, User, Goal, Notification
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any
import sendgrid
from sendgrid.helpers.mail import Mail
import os

class NotificationService:
    def __init__(self):
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY', 'your-sendgrid-api-key')
        self.sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
    
    def create_notification(self, user_id: str, notification_type: str, title: str, 
                          message: str, goal_id: Optional[str] = None) -> Notification:
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            goal_id=goal_id,
            type=notification_type,
            title=title,
            message=message
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification
    
    def send_milestone_notifications(self, user_id: str, goal_id: str, progress_pct: float) -> None:
        """Send milestone notifications (25%, 50%, 75%, 100%)"""
        milestones = [25, 50, 75, 100]
        
        for milestone in milestones:
            if progress_pct >= milestone:
                # Check if notification already sent for this milestone
                existing = Notification.query.filter_by(
                    user_id=user_id,
                    goal_id=goal_id,
                    type='milestone',
                    title=f"{milestone}% Milestone Reached"
                ).first()
                
                if not existing:
                    goal = Goal.query.get(goal_id)
                    if goal:
                        title = f"🎉 {milestone}% Milestone Reached!"
                        message = f"Congratulations! You've reached {milestone}% of your goal '{goal.name}'. Keep up the great work!"
                        
                        notification = self.create_notification(
                            user_id=user_id,
                            goal_id=goal_id,
                            notification_type='milestone',
                            title=title,
                            message=message
                        )
                        
                        # Send email notification
                        self._send_email_notification(user_id, title, message)
    
    def send_deadline_reminders(self, user_id: str, goal_id: str, days_remaining: int) -> None:
        """Send deadline reminder notifications"""
        if days_remaining <= 30 and days_remaining > 0:
            goal = Goal.query.get(goal_id)
            if goal:
                if days_remaining <= 7:
                    urgency = "urgent"
                    title = f"⚠️ Goal Deadline Approaching!"
                    message = f"Your goal '{goal.name}' deadline is in {days_remaining} days. Consider adjusting your timeline or increasing your savings rate."
                elif days_remaining <= 14:
                    urgency = "moderate"
                    title = f"📅 Goal Deadline Reminder"
                    message = f"Your goal '{goal.name}' deadline is in {days_remaining} days. You're on track to meet your target!"
                else:
                    urgency = "low"
                    title = f"📊 Goal Progress Update"
                    message = f"Your goal '{goal.name}' deadline is in {days_remaining} days. Keep up the momentum!"
                
                # Check if reminder already sent for this timeframe
                existing = Notification.query.filter_by(
                    user_id=user_id,
                    goal_id=goal_id,
                    type='deadline',
                    title=title
                ).first()
                
                if not existing:
                    notification = self.create_notification(
                        user_id=user_id,
                        goal_id=goal_id,
                        notification_type='deadline',
                        title=title,
                        message=message
                    )
                    
                    # Send email notification
                    self._send_email_notification(user_id, title, message)
    
    def send_weekly_progress_update(self, user_id: str, goal_id: str, progress_data: Dict[str, Any]) -> None:
        """Send weekly progress update notifications"""
        goal = Goal.query.get(goal_id)
        if not goal:
            return
        
        # Check if weekly update already sent this week
        week_start = datetime.utcnow() - timedelta(days=7)
        existing = Notification.query.filter(
            Notification.user_id == user_id,
            Notification.goal_id == goal_id,
            Notification.type == 'weekly_update',
            Notification.created_at >= week_start
        ).first()
        
        if not existing:
            title = f"📈 Weekly Progress Update: {goal.name}"
            message = f"""
            Progress: {progress_data['progress_pct']:.1f}%
            Status: {progress_data['pacing_status'].title()}
            {progress_data['pacing_detail']}
            
            Keep up the great work toward your goal!
            """
            
            notification = self.create_notification(
                user_id=user_id,
                goal_id=goal_id,
                notification_type='weekly_update',
                title=title,
                message=message.strip()
            )
            
            # Send email notification
            self._send_email_notification(user_id, title, message)
    
    def send_recommendation_notification(self, user_id: str, recommendations: List[str], goal_id: Optional[str] = None) -> None:
        """Send recommendation notifications"""
        if not recommendations:
            return
        
        title = "💡 Personalized Recommendations"
        message = "Here are some personalized recommendations to help you achieve your financial goals:\n\n" + "\n".join(f"• {rec}" for rec in recommendations[:3])
        
        notification = self.create_notification(
            user_id=user_id,
            goal_id=goal_id,
            notification_type='recommendation',
            title=title,
            message=message
        )
        
        # Send email notification
        self._send_email_notification(user_id, title, message)
    
    def _send_email_notification(self, user_id: str, title: str, message: str) -> None:
        """Send email notification using SendGrid"""
        try:
            user = User.query.get(user_id)
            if not user or not user.email:
                return
            
            # Create email
            email = Mail(
                from_email='noreply@riskagent.com',
                to_emails=user.email,
                subject=title,
                html_content=f"""
                <html>
                <body>
                    <h2>{title}</h2>
                    <p>{message.replace(chr(10), '<br>')}</p>
                    <hr>
                    <p><small>This is an automated message from your Risk Assessment Agent.</small></p>
                </body>
                </html>
                """
            )
            
            # Send email
            response = self.sg.send(email)
            
            # Update notification status
            notification = Notification.query.filter_by(
                user_id=user_id,
                title=title
            ).order_by(Notification.created_at.desc()).first()
            
            if notification:
                notification.sent_email = True
                db.session.commit()
                
        except Exception as e:
            print(f"Error sending email notification: {e}")
    
    def get_user_notifications(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's notifications"""
        notifications = Notification.query.filter_by(user_id=user_id).order_by(
            Notification.created_at.desc()
        ).limit(limit).all()
        
        return [n.to_dict() for n in notifications]
    
    def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=user_id
        ).first()
        
        if notification:
            notification.is_read = True
            db.session.commit()
            return True
        
        return False
    
    def send_push_notification(self, user_id: str, title: str, message: str) -> None:
        """Send push notification (placeholder for FCM integration)"""
        # This would integrate with Firebase Cloud Messaging
        # For now, we'll just create an in-app notification
        self.create_notification(
            user_id=user_id,
            notification_type='push',
            title=title,
            message=message
        )
    
    def cleanup_old_notifications(self, days_old: int = 30) -> int:
        """Clean up old notifications"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        old_notifications = Notification.query.filter(
            Notification.created_at < cutoff_date
        ).all()
        
        count = len(old_notifications)
        for notification in old_notifications:
            db.session.delete(notification)
        
        db.session.commit()
        return count
