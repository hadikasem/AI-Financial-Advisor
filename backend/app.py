# Main Flask Application for Risk Assessment and Goal Tracking API

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json
import uuid
from typing import Dict, List, Optional, Any
import re

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-string')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost/risk_agent_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import models first to get the db instance
from models import db, User, Assessment, Goal, ProgressSnapshot, Transaction, Account, Notification, GoalCategory

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
CORS(app)

# Import services
from services.assessment_service import AssessmentService
from services.goal_service import GoalService
from services.progress_service import ProgressService
from services.notification_service import NotificationService
from services.llm_service import LLMService

# Initialize services
assessment_service = AssessmentService()
goal_service = GoalService()
progress_service = ProgressService()
notification_service = NotificationService()
llm_service = LLMService()

# Password validation
def validate_password(password):
    """Validate password meets requirements: min 8 chars, upper, lower, special char"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is valid"

# Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'full_name', 'username', 'phone']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate password
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already taken'}), 400
        
        # Create new user
        user = User(
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            full_name=data['full_name'],
            username=data['username'],
            phone=data['phone']
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'username': user.username
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'username': user.username
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assessment/start', methods=['POST'])
@jwt_required()
def start_assessment():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Start new assessment
        assessment = assessment_service.start_assessment(user_id)
        
        return jsonify({
            'message': 'Assessment started',
            'assessment_id': assessment['id'],
            'current_question': assessment['current_question'],
            'answers': assessment.get('answers', {})
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assessment/answer', methods=['POST'])
@jwt_required()
def answer_question():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('question_id') or not data.get('answer'):
            return jsonify({'error': 'Question ID and answer required'}), 400
        
        # Process answer
        result = assessment_service.process_answer(
            user_id, 
            data['question_id'], 
            data['answer']
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assessment/complete', methods=['POST'])
@jwt_required()
def complete_assessment():
    try:
        user_id = get_jwt_identity()
        
        # Complete assessment and calculate risk score
        result = assessment_service.complete_assessment(user_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/goals', methods=['GET'])
@jwt_required()
def get_goals():
    try:
        user_id = get_jwt_identity()
        goals = goal_service.get_user_goals(user_id)
        
        return jsonify({'goals': goals}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/goals', methods=['POST'])
@jwt_required()
def create_goal():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate goal data
        required_fields = ['name', 'target_amount', 'target_date', 'category']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create goal
        goal = goal_service.create_goal(user_id, data)
        
        return jsonify({
            'message': 'Goal created successfully',
            'goal': goal
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/goals/<goal_id>', methods=['DELETE'])
@jwt_required()
def delete_goal(goal_id):
    try:
        user_id = get_jwt_identity()
        
        # Delete goal
        goal_service.delete_goal(user_id, goal_id)
        
        return jsonify({'message': 'Goal deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/update', methods=['POST'])
@jwt_required()
def update_progress():
    try:
        user_id = get_jwt_identity()
        
        # Update progress with smart time-based simulation
        result = progress_service.update_progress(user_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/<goal_id>', methods=['GET'])
@jwt_required()
def get_progress(goal_id):
    try:
        user_id = get_jwt_identity()
        
        # Get progress for specific goal
        progress = progress_service.get_progress(user_id, goal_id)
        
        return jsonify({'progress': progress}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    try:
        user_id = get_jwt_identity()
        goal_id = request.args.get('goal_id')
        
        # Get recommendations
        recommendations = llm_service.get_recommendations(user_id, goal_id)
        
        return jsonify({'recommendations': recommendations}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'username': user.username,
                'phone': user.phone,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/goals/categories', methods=['GET'])
def get_goal_categories():
    """Get predefined goal categories"""
    categories = [category.value for category in GoalCategory]
    return jsonify({'categories': categories}), 200

@app.route('/api/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    try:
        user_id = get_jwt_identity()
        notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(20).all()
        
        return jsonify({
            'notifications': [n.to_dict() for n in notifications]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/<notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    try:
        user_id = get_jwt_identity()
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({'message': 'Notification marked as read'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
