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
# Initialize LLM service lazily to avoid database context issues
llm_service = None

def get_llm_service():
    """Get LLM service instance, creating it if needed"""
    global llm_service
    if llm_service is None:
        llm_service = LLMService()
        # Force initialization
        llm_service._ensure_initialized()
    return llm_service

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

def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return True, "Phone number is optional"
    
    # Remove all non-digit characters for validation
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's a reasonable phone number length (7-15 digits)
    if len(digits_only) < 7 or len(digits_only) > 15:
        return False, "Phone number must be between 7 and 15 digits"
    
    # Check if it contains only valid phone characters
    if not re.match(r'^[\d\s\-\+\(\)\.]+$', phone):
        return False, "Phone number contains invalid characters"
    
    return True, "Phone number is valid"

# Routes
@app.route('/api/test/llm', methods=['POST'])
def test_llm():
    """Test LLM service without authentication"""
    try:
        data = request.get_json()
        question = data.get('question', 'What is a stock?')
        
        # Get LLM service
        llm = get_llm_service()
        
        # Get provider status
        provider_status = llm.get_provider_status()
        available_models = llm.get_available_models()
        
        # Test LLM response
        answer = llm.get_help_response(question, "Test context")
        
        return jsonify({
            'provider_status': provider_status,
            'available_models': available_models,
            'answer': answer
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'full_name', 'username']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate password
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Validate phone number (optional)
        phone = data.get('phone', '')
        if phone:
            is_valid_phone, phone_message = validate_phone(phone)
            if not is_valid_phone:
                return jsonify({'error': phone_message}), 400
        
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
            phone=phone
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

@app.route('/api/assessment/question/<question_id>', methods=['GET'])
@jwt_required()
def get_question(question_id):
    try:
        question = assessment_service._get_question_by_id(question_id)
        if not question:
            return jsonify({'error': 'Question not found'}), 404
        
        return jsonify({'question': question}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assessment/update-answer', methods=['POST'])
@jwt_required()
def update_answer():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        question_id = data.get('question_id')
        answer = data.get('answer')
        
        if not question_id or not answer:
            return jsonify({'error': 'Question ID and answer are required'}), 400
        
        # Update the answer
        result = assessment_service.update_answer(user_id, question_id, answer)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assessment/current', methods=['GET'])
@jwt_required()
def get_current_assessment():
    """Get the user's current assessment (completed or in progress)"""
    try:
        user_id = get_jwt_identity()
        
        # Get the most recent completed assessment
        completed_assessment = Assessment.query.filter_by(
            user_id=user_id,
            status='completed'
        ).order_by(Assessment.completed_at.desc()).first()
        
        if completed_assessment:
            return jsonify({
                'assessment': completed_assessment.to_dict(),
                'risk_profile': {
                    'score': completed_assessment.risk_score,
                    'label': completed_assessment.risk_label,
                    'description': completed_assessment.risk_description
                },
                'status': 'completed'
            }), 200
        
        # Check for in-progress assessment
        in_progress_assessment = Assessment.query.filter_by(
            user_id=user_id,
            status='in_progress'
        ).order_by(Assessment.created_at.desc()).first()
        
        if in_progress_assessment:
            current_question = assessment_service._get_next_question(in_progress_assessment.answers)
            return jsonify({
                'assessment': in_progress_assessment.to_dict(),
                'current_question': current_question,
                'status': 'in_progress'
            }), 200
        
        # No assessment found
        return jsonify({
            'assessment': None,
            'status': 'none'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assessment/retake', methods=['POST'])
@jwt_required()
def retake_assessment():
    """Start a new assessment (retake) for the user"""
    try:
        user_id = get_jwt_identity()
        
        # Mark any existing in-progress assessment as cancelled
        existing_in_progress = Assessment.query.filter_by(
            user_id=user_id,
            status='in_progress'
        ).all()
        
        for assessment in existing_in_progress:
            assessment.status = 'cancelled'
        
        # Start a new assessment
        assessment = assessment_service.start_assessment(user_id)
        
        return jsonify({
            'message': 'New assessment started',
            'assessment_id': assessment['id'],
            'current_question': assessment['current_question'],
            'answers': assessment.get('answers', {})
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/llm/debug', methods=['GET'])
@jwt_required()
def llm_debug():
    try:
        # Get LLM service and provider status
        llm = get_llm_service()
        provider_status = llm.get_provider_status()
        available_models = llm.get_available_models()
        
        return jsonify({
            'provider_status': provider_status,
            'available_models': available_models
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/llm/help', methods=['POST'])
@jwt_required()
def llm_help():
    try:
        data = request.get_json()
        question = data.get('question', '')
        context = data.get('context', '')
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        # Get LLM response
        llm = get_llm_service()
        answer = llm.get_help_response(question, context)
        
        return jsonify({'answer': answer}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/llm/provider', methods=['GET', 'POST'])
@jwt_required()
def llm_provider():
    try:
        if request.method == 'POST':
            # Switch provider
            data = request.get_json()
            new_provider = data.get('provider', '').lower()
            
            if new_provider not in ['openai', 'ollama']:
                return jsonify({'error': 'Provider must be "openai" or "ollama"'}), 400
            
            # Update environment variable (this will require app restart to take effect)
            os.environ['DEFAULT_LLM_PROVIDER'] = new_provider
            
            # Reinitialize LLM service
            global llm_service
            llm_service = None
            llm = get_llm_service()
            
            return jsonify({
                'message': f'Provider switched to {new_provider}. Restart required for full effect.',
                'provider_status': llm.get_provider_status()
            }), 200
        else:
            # Get current provider status
            llm = get_llm_service()
            return jsonify({
                'provider_status': llm.get_provider_status()
            }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/goals/suggestions', methods=['GET', 'POST'])
@jwt_required()
def get_goal_suggestions():
    try:
        user_id = get_jwt_identity()
        
        if request.method == 'POST':
            # Generate more suggestions
            data = request.get_json()
            request_more = data.get('request_more', False)
            existing_suggestions = data.get('existing_suggestions', [])
            
            # Check if we've reached the maximum limit
            if len(existing_suggestions) >= 100:
                return jsonify({'error': 'Maximum number of suggested goals reached (100).'}), 400
            
            suggestions = goal_service.generate_goal_suggestions(
                user_id, 
                request_more=request_more, 
                existing_suggestions=existing_suggestions
            )
        else:
            # Get existing suggestions
            suggestions = goal_service.get_goal_suggestions(user_id)
        
        return jsonify({'suggestions': suggestions}), 200
        
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
        llm = get_llm_service()
        recommendations = llm.get_recommendations(user_id, goal_id)
        
        return jsonify({'recommendations': recommendations}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommendations/update', methods=['POST'])
@jwt_required()
def update_recommendations():
    """Update recommendations based on current progress"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        goal_id = data.get('goal_id')
        
        # Update recommendations
        llm = get_llm_service()
        recommendations = llm.update_recommendations(user_id, goal_id)
        
        return jsonify({'recommendations': recommendations}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommendations/debug', methods=['GET'])
@jwt_required()
def debug_recommendations():
    """Debug endpoint to check recommendation generation"""
    try:
        user_id = get_jwt_identity()
        goal_id = request.args.get('goal_id')
        
        # Get LLM service debug info
        llm = get_llm_service()
        debug_info = llm.get_debug_info()
        
        # Check stored recommendations
        from models import Recommendation
        stored_recommendation = Recommendation.query.filter_by(
            user_id=user_id,
            goal_id=goal_id
        ).order_by(Recommendation.updated_at.desc()).first()
        
        return jsonify({
            'llm_debug': debug_info,
            'stored_recommendation': stored_recommendation.to_dict() if stored_recommendation else None,
            'user_id': user_id,
            'goal_id': goal_id
        }), 200
        
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
