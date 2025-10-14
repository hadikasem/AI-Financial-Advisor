# Main Streamlit Application for Risk Assessment and Goal Tracking

import streamlit as st
import requests
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, date, timedelta
import time
import os
from typing import Dict, List, Optional, Any

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000/api")
SESSION_STATE_KEY = "user_session"

# Page configuration
st.set_page_config(
    page_title="Risk Assessment & Goal Tracking",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .goal-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .progress-bar {
        background-color: #e0e0e0;
        border-radius: 10px;
        overflow: hidden;
        height: 20px;
        margin: 0.5rem 0;
    }
    .progress-fill {
        background-color: #1f77b4;
        height: 100%;
        transition: width 0.3s ease;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .notification {
        background-color: #e8f4fd;
        border: 1px solid #1f77b4;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .nav-item {
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        border-radius: 0.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
        border: none;
        background: none;
        width: 100%;
        text-align: left;
        font-size: 1rem;
    }
    .nav-item:hover {
        background-color: #f0f2f6;
    }
    .nav-item.active {
        background-color: #1f77b4;
        color: white;
    }
    .nav-item.active:hover {
        background-color: #1565c0;
    }
    .assessment-results {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 1rem;
        border: 2px solid #1f77b4;
        margin: 1rem 0;
    }
    .risk-score-display {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin: 1rem 0;
    }
    .risk-category {
        font-size: 1.5rem;
        font-weight: bold;
        text-align: center;
        margin: 0.5rem 0;
    }
    .suggestions-box {
        background-color: #e8f4fd;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize session state variables"""
    if SESSION_STATE_KEY not in st.session_state:
        st.session_state[SESSION_STATE_KEY] = {
            'authenticated': False,
            'user': None,
            'access_token': None,
            'current_assessment': None,
            'current_goals': [],
            'notifications': [],
            'current_page': 'Dashboard',
            'assessment_completed': None,
        'help_chat_open': False,
        'help_chat_messages': [],
        'help_questions_count': 0,
        'current_question_id': None,
        'answered_questions': [],
        'current_question_index': 0,
        'goal_suggestions_visible': True,
        'prefilled_goal': None,
        'cached_goal_suggestions': None
        }

def display_help_chat(question_id: str, question_text: str):
    """Display collapsible help chat box"""
    session = st.session_state[SESSION_STATE_KEY]
    
    # Check if we need to reset chat for new question
    if session.get('current_question_id') != question_id:
        session['help_chat_messages'] = []
        session['help_questions_count'] = 0
        session['current_question_id'] = question_id
    
    # Help chat toggle button
    if st.button("❓ Get Help", key=f"help_{question_id}"):
        session['help_chat_open'] = not session['help_chat_open']
        st.rerun()
    
    # Display chat interface if open
    if session.get('help_chat_open', False):
        st.info("💡 Ask any questions about financial terms or concepts!")
    
    # Display chat if open
    if session.get('help_chat_open', False):
        st.markdown("---")
        
        # Display chat messages
        chat_messages = session.get('help_chat_messages', [])
        if chat_messages:
            st.subheader("💬 Help Chat")
            for i, msg in enumerate(chat_messages):
                if msg['role'] == 'user':
                    st.markdown(f"**You:** {msg['content']}")
                else:
                    st.markdown(f"**Assistant:** {msg['content']}")
                st.markdown("---")
        
        # Check question limit
        questions_count = session.get('help_questions_count', 0)
        if questions_count >= 20:
            st.warning("⚠️ You've reached the limit of 20 help questions for this question.")
            return
        
        # Chat input
        with st.form(f"help_chat_form_{question_id}", clear_on_submit=True):
            user_question = st.text_area(
                f"Ask a question about '{question_text}' or any financial concept:",
                placeholder="e.g., What is an ETF? What does investment horizon mean?",
                height=100
            )
            
            col1, col2 = st.columns([1, 1])
            with col1:
                submit_question = st.form_submit_button("Ask Question", type="primary")
            with col2:
                close_chat = st.form_submit_button("Close Chat")
            
            if close_chat:
                session['help_chat_open'] = False
                st.rerun()
            
            if submit_question and user_question.strip():
                if questions_count >= 20:
                    st.error("You've reached the limit of 20 help questions.")
                    return
                
                # Add user message
                chat_messages.append({
                    'role': 'user',
                    'content': user_question.strip()
                })
                
                # Get LLM response
                try:
                    llm_response = get_llm_help_response(user_question.strip(), question_text)
                    
                    # Add assistant message
                    chat_messages.append({
                        'role': 'assistant',
                        'content': llm_response
                    })
                    
                    # Update session state
                    session['help_chat_messages'] = chat_messages
                    session['help_questions_count'] = questions_count + 1
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Sorry, I couldn't process your question. Error: {str(e)}")

def get_llm_help_response(user_question: str, current_question: str) -> str:
    """Get LLM response for help questions"""
    session = st.session_state[SESSION_STATE_KEY]
    token = session['access_token']
    
    # Make API request to backend for LLM help
    response = make_api_request("/llm/help", "POST", {
        "question": user_question,
        "context": f"Current assessment question: {current_question}"
    }, token=token)
    
    if response and 'answer' in response:
        return response['answer']
    else:
        return "I'm sorry, I couldn't process your question at the moment. Please try again."

def display_question_progress_bar(question_id: str, question_text: str, answers: dict):
    """Display progress bar navigation for questions"""
    session = st.session_state[SESSION_STATE_KEY]
    
    # Update answered questions list
    answered_questions = session.get('answered_questions', [])
    if question_id not in [q['id'] for q in answered_questions]:
        answered_questions.append({
            'id': question_id,
            'text': question_text,
            'answer': answers.get(question_id, '')
        })
        session['answered_questions'] = answered_questions
    
    # Display progress bar at top middle
    if len(answered_questions) > 0:
        st.markdown("---")
        
        # Create progress bar with dashes
        progress_dashes = "-" * len(answered_questions)
        
        # Center the progress bar
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            st.markdown(f"**Progress:** `{progress_dashes}`")
            
            # Make each dash clickable
            cols = st.columns(len(answered_questions))
            for i, question in enumerate(answered_questions):
                with cols[i]:
                    if st.button(f"Q{i+1}", key=f"progress_q{i+1}", help=f"Go to: {question['text'][:30]}..."):
                        navigate_to_question(question['id'])
        
        st.markdown("---")

def navigate_to_question(question_id: str):
    """Navigate to a specific question"""
    session = st.session_state[SESSION_STATE_KEY]
    token = session['access_token']
    
    # Make API request to get question details
    response = make_api_request(f"/assessment/question/{question_id}", token=token)
    if response:
        # Update current assessment with the selected question
        assessment = session.get('current_assessment', {})
        assessment['current_question'] = response.get('question')
        session['current_assessment'] = assessment
        st.rerun()

def display_navigation_sidebar():
    """Display navigation sidebar with vertical list"""
    session = st.session_state[SESSION_STATE_KEY]
    
    st.write(f"Welcome, {session['user']['full_name']}!")
    st.divider()
    
    # Navigation items
    nav_items = [
        ("📊", "Dashboard"),
        ("🎯", "Goals"), 
        ("📋", "Assessment"),
        ("🔔", "Notifications")
    ]
    
    # Check if user has completed assessment
    assessment_completed = session.get('assessment_completed')
    
    if not assessment_completed:
        st.warning("⚠️ Please complete your risk assessment first!")
        # Force navigation to Assessment
        st.session_state[SESSION_STATE_KEY]['current_page'] = 'Assessment'
    
    # Display navigation items
    for icon, page_name in nav_items:
        is_active = session['current_page'] == page_name
        active_class = "active" if is_active else ""
        
        if st.button(f"{icon} {page_name}", key=f"nav_{page_name}", use_container_width=True):
            st.session_state[SESSION_STATE_KEY]['current_page'] = page_name
            st.rerun()
    
    st.divider()
    
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state[SESSION_STATE_KEY] = {
            'authenticated': False,
            'user': None,
            'access_token': None,
            'current_assessment': None,
            'current_goals': [],
            'notifications': [],
            'current_page': 'Dashboard',
            'assessment_completed': None
        }
        st.rerun()

def make_api_request(endpoint: str, method: str = "GET", data: Dict = None, token: str = None) -> Dict:
    """Make API request to backend"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return {}
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend API. Please ensure the Flask server is running.")
        return {}
    except Exception as e:
        st.error(f"Request failed: {str(e)}")
        return {}

def login_page():
    """Login and registration page"""
    st.markdown('<h1 class="main-header">Risk Assessment & Goal Tracking</h1>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if email and password:
                    response = make_api_request("/auth/login", "POST", {
                        "email": email,
                        "password": password
                    })
                    
                    if response and "access_token" in response:
                        st.session_state[SESSION_STATE_KEY].update({
                            'authenticated': True,
                            'user': response['user'],
                            'access_token': response['access_token']
                        })
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Login failed. Please check your credentials.")
                else:
                    st.error("Please fill in all fields.")
    
    with tab2:
        st.subheader("Register")
        with st.form("register_form"):
            full_name = st.text_input("Full Name")
            username = st.text_input("Username")
            email = st.text_input("Email")
            phone = st.text_input("Phone Number (Optional)", placeholder="e.g., +1-555-123-4567")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Register")
            
            if submit:
                if all([full_name, username, email, password, confirm_password]):
                    if password != confirm_password:
                        st.error("Passwords do not match.")
                    elif len(password) < 8:
                        st.error("Password must be at least 8 characters long.")
                    else:
                        response = make_api_request("/auth/register", "POST", {
                            "full_name": full_name,
                            "username": username,
                            "email": email,
                            "phone": phone,
                            "password": password
                        })
                        
                        if response and "access_token" in response:
                            st.session_state[SESSION_STATE_KEY].update({
                                'authenticated': True,
                                'user': response['user'],
                                'access_token': response['access_token']
                            })
                            st.success("Registration successful!")
                            st.rerun()
                        else:
                            st.error("Registration failed. Please try again.")
                else:
                    st.error("Please fill in all fields.")

def display_assessment_results(assessment_data):
    """Display assessment results with risk profile and suggestions"""
    st.markdown('<div class="assessment-results">', unsafe_allow_html=True)
    
    # Risk Score Display - Check both nested and direct structure
    risk_profile = assessment_data.get('risk_profile', {})
    assessment = assessment_data.get('assessment', {})
    
    # Try to get risk score from nested structure first, then direct
    risk_score = risk_profile.get('score') or assessment.get('risk_score') or assessment_data.get('risk_score', 0)
    risk_label = risk_profile.get('label') or assessment.get('risk_label') or assessment_data.get('risk_label', 'Unknown')
    risk_description = risk_profile.get('description') or assessment.get('risk_description') or assessment_data.get('risk_description', '')
    
    st.markdown(f'<div class="risk-score-display">Risk Score: {risk_score:.1f}%</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="risk-category">Risk Profile: {risk_label}</div>', unsafe_allow_html=True)
    
    # Risk Description
    if risk_description:
        st.write(f"**Profile Description:** {risk_description}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Get personalized suggestions
    session = st.session_state[SESSION_STATE_KEY]
    token = session['access_token']
    
    suggestions_response = make_api_request("/recommendations", token=token)
    suggestions = suggestions_response.get('recommendations', []) if suggestions_response else []
    
    if suggestions:
        st.markdown('<div class="suggestions-box">', unsafe_allow_html=True)
        st.subheader("💡 Personalized Recommendations")
        for i, suggestion in enumerate(suggestions, 1):
            st.write(f"{i}. {suggestion}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Prompt to create goals
    st.success("🎉 Assessment complete! Now let's set up your financial goals.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("🔄 Retake Assessment", use_container_width=True):
            # Clear assessment data and restart
            session = st.session_state[SESSION_STATE_KEY]
            session['assessment_completed'] = None
            session['current_assessment'] = None
            session['answered_questions'] = []
            session['help_chat_open'] = False
            session['help_chat_messages'] = []
            session['help_questions_count'] = 0
            st.rerun()
    with col2:
        if st.button("🎯 Set Up Your Goals", type="primary", use_container_width=True):
            st.session_state[SESSION_STATE_KEY]['current_page'] = 'Goals'
            st.rerun()

def assessment_page():
    """Risk assessment questionnaire page"""
    st.markdown('<h1 class="main-header">Risk Assessment</h1>', unsafe_allow_html=True)
    
    session = st.session_state[SESSION_STATE_KEY]
    token = session['access_token']
    
    # Check if assessment is already completed
    if session.get('assessment_completed'):
        display_assessment_results(session['assessment_completed'])
        return
    
    # Start assessment if not already started
    if not session['current_assessment']:
        response = make_api_request("/assessment/start", "POST", token=token)
        if response and "assessment_id" in response:
            st.session_state[SESSION_STATE_KEY]['current_assessment'] = response
    
    assessment = session['current_assessment']
    if not assessment:
        st.error("Failed to start assessment. Please try again.")
        return
    
    # Display current question
    if "current_question" in assessment and assessment['current_question'] is not None:
        question = assessment['current_question']
        answers = assessment.get('answers', {})
        
        # Display progress bar
        display_question_progress_bar(question['id'], question['question'], answers)
        
        st.subheader(f"Question {len(answers) + 1}")
        st.write(question['question'])
        
        # Get current answer for this question
        current_answer = answers.get(question['id'], '')
        
        # Handle different question types
        if question['type'] == 'number':
            validation = question.get('validation', {})
            min_val = float(validation.get('min', 0))
            max_val = float(validation.get('max', 1000))
            step_val = 1.0 if question['id'] in ['age', 'horizon', 'dependents'] else 0.1
            
            # Use current answer as default value
            default_value = float(current_answer) if current_answer else min_val
            
            answer = st.number_input(
                "Your answer:",
                min_value=min_val,
                max_value=max_val,
                step=step_val,
                value=default_value
            )
        elif question['type'] == 'multiple_choice':
            # Use current answer as default selection
            default_index = 0
            if current_answer and current_answer in question['options']:
                default_index = question['options'].index(current_answer)
            
            answer = st.selectbox("Your answer:", question['options'], index=default_index)
        else:
            # Use current answer as default text
            answer = st.text_input("Your answer:", value=current_answer)
        
        col1, col2 = st.columns([1, 2])
        with col1:
            # Previous Question button
            answered_questions = session.get('answered_questions', [])
            if len(answered_questions) > 1:
                if st.button("⬅️ Previous Question"):
                    prev_question = answered_questions[-2]
                    navigate_to_question(prev_question['id'])
        
        with col2:
            if st.button("Submit Answer", type="primary"):
                if answer:
                    response = make_api_request("/assessment/answer", "POST", {
                        "question_id": question['id'],
                        "answer": str(answer)
                    }, token=token)
                    
                    if response:
                        if "next_step" in response and response["next_step"] == "complete_assessment":
                            # Assessment complete, calculate results
                            complete_response = make_api_request("/assessment/complete", "POST", token=token)
                            if complete_response:
                                st.session_state[SESSION_STATE_KEY]['assessment_completed'] = complete_response
                                st.rerun()
                        else:
                            # Update current assessment
                            st.session_state[SESSION_STATE_KEY]['current_assessment'] = response
                            st.rerun()
                else:
                    st.error("Please provide an answer.")
        
        # Display help chat full-width below buttons
        display_help_chat(question['id'], question['question'])
    else:
        # Assessment is complete but completion logic didn't trigger
        st.success("Assessment completed!")
        st.info("Please refresh the page or navigate to the Goals section to continue.")

def goals_page():
    """Goal setting and management page"""
    st.markdown('<h1 class="main-header">Financial Goals</h1>', unsafe_allow_html=True)
    
    session = st.session_state[SESSION_STATE_KEY]
    token = session['access_token']
    
    # Get goal categories
    categories_response = make_api_request("/goals/categories", token=token)
    categories = categories_response.get('categories', []) if categories_response else []
    
    # Create new goal
    with st.expander("Create New Goal", expanded=False):
        # Check for prefilled goal
        session = st.session_state[SESSION_STATE_KEY]
        prefilled_goal = session.get('prefilled_goal')
        
        # Pre-fill goal name if suggestion was selected
        default_name = prefilled_goal if prefilled_goal else ""
        
        with st.form("create_goal_form", clear_on_submit=False):
            col1, col2 = st.columns(2)
            with col1:
                goal_name = st.text_input("Goal Name", value=default_name)
                goal_category = st.selectbox("Category", categories)
                target_amount = st.number_input("Target Amount ($)", min_value=0.0, step=100.0)
            with col2:
                target_date = st.date_input("Target Date", min_value=date.today())
                start_amount = st.number_input("Starting Amount ($)", min_value=0.0, step=100.0)
                description = st.text_area("Description (Optional)")
            
            submit_button = st.form_submit_button("Create Goal")
            
            if submit_button:
                if goal_name and target_amount and target_date:
                    response = make_api_request("/goals", "POST", {
                        "name": goal_name,
                        "category": goal_category,
                        "target_amount": target_amount,
                        "target_date": target_date.isoformat(),
                        "start_amount": start_amount,
                        "description": description
                    }, token=token)
                    
                    if response:
                        st.success("Goal created successfully!")
                        # Hide goal suggestions after successful creation
                        session = st.session_state[SESSION_STATE_KEY]
                        session['goal_suggestions_visible'] = False
                        # Clear prefilled goal and cached suggestions only after successful creation
                        session['prefilled_goal'] = None
                        session['cached_goal_suggestions'] = None
                        st.rerun()
                else:
                    st.error("Please fill in all required fields.")
                    # Don't clear prefilled goal on validation error
    
    # Display existing goals
    goals_response = make_api_request("/goals", token=token)
    goals = goals_response.get('goals', []) if goals_response else []
    
    if goals:
        st.subheader("Your Goals")
        for goal in goals:
            with st.container():
                st.markdown(f"""
                <div class="goal-card">
                    <h3>{goal['name']}</h3>
                    <p><strong>Category:</strong> {goal['category']}</p>
                    <p><strong>Target:</strong> ${goal['target_amount']:,.2f} by {goal['target_date']}</p>
                    <p><strong>Current:</strong> ${goal['current_amount']:,.2f}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Progress bar
                progress_pct = (goal['current_amount'] / goal['target_amount']) * 100
                st.progress(progress_pct / 100)
                st.write(f"Progress: {progress_pct:.1f}%")
                
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button(f"Delete", key=f"delete_{goal['id']}"):
                        response = make_api_request(f"/goals/{goal['id']}", "DELETE", token=token)
                        if response:
                            st.success("Goal deleted!")
                            st.rerun()
    else:
        st.info("No goals created yet. Create your first goal above!")
    
    # Display goal suggestions
    session = st.session_state[SESSION_STATE_KEY]
    suggestions_visible = session.get('goal_suggestions_visible', True)
    
    # Toggle button for goal suggestions
    if not suggestions_visible:
        if st.button("Show Goal Suggestions"):
            session['goal_suggestions_visible'] = True
            st.rerun()
    else:
        if st.button("Hide Goal Suggestions"):
            session['goal_suggestions_visible'] = False
            st.rerun()
    
    # Display suggestions only if visible
    if suggestions_visible:
        display_goal_suggestions(token)

def display_goal_suggestions(token: str):
    """Display goal suggestions based on user's risk assessment"""
    st.markdown("---")
    st.subheader("💡 Goal Suggestions")
    
    session = st.session_state[SESSION_STATE_KEY]
    
    # Check if user has completed assessment
    assessment_completed = session.get('assessment_completed')
    
    if assessment_completed:
        # Get personalized suggestions based on risk profile
        risk_profile = assessment_completed.get('risk_profile', {})
        risk_label = risk_profile.get('label', 'Balanced')
        
        st.write(f"**Based on your {risk_label} risk profile, here are some suggested goals:**")
        
        # Get LLM-generated goal suggestions (use cached if available)
        cached_suggestions = session.get('cached_goal_suggestions')
        if cached_suggestions is None:
            suggestions_response = make_api_request("/goals/suggestions", token=token)
            suggestions = suggestions_response.get('suggestions', []) if suggestions_response else []
            session['cached_goal_suggestions'] = suggestions
        else:
            suggestions = cached_suggestions
        
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{i}. {suggestion}")
                with col2:
                    if st.button(f"Use This Goal", key=f"use_suggestion_{i}"):
                        # Pre-fill the create goal form with this suggestion
                        session = st.session_state[SESSION_STATE_KEY]
                        session['prefilled_goal'] = suggestion
                        st.rerun()
            
            # Button to get more suggestions
            if st.button("🔄 Get More Suggestions"):
                with st.spinner("Generating more suggestions..."):
                    more_suggestions_response = make_api_request("/goals/suggestions", "POST", {
                        "request_more": True
                    }, token=token)
                    if more_suggestions_response and 'suggestions' in more_suggestions_response:
                        # Update cached suggestions with new ones
                        session['cached_goal_suggestions'] = more_suggestions_response['suggestions']
                        st.success("More suggestions generated!")
                        st.rerun()
                    else:
                        st.error("Failed to generate more suggestions. Please try again.")
        else:
            st.info("No personalized suggestions available. Complete your assessment for better recommendations.")
    else:
        st.info("Complete your risk assessment to get personalized goal suggestions!")

def dashboard_page():
    """Main dashboard with progress tracking and recommendations"""
    st.markdown('<h1 class="main-header">Dashboard</h1>', unsafe_allow_html=True)
    
    session = st.session_state[SESSION_STATE_KEY]
    token = session['access_token']
    
    # Update progress button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Update Progress", type="primary", use_container_width=True):
            with st.spinner("Updating progress..."):
                response = make_api_request("/progress/update", "POST", token=token)
                if response:
                    st.success("Progress updated successfully!")
                    time.sleep(1)
                    st.rerun()
    
    # Get goals and their progress
    goals_response = make_api_request("/goals", token=token)
    goals = goals_response.get('goals', []) if goals_response else []
    
    if not goals:
        st.info("No goals found. Please create some goals first.")
        
        # Check if user has completed assessment
        assessment_completed = session.get('assessment_completed')
        
        if assessment_completed:
            st.success("🎉 Assessment complete! Now let's set up your financial goals.")
            
            # Get goal-setting suggestions based on assessment
            suggestions_response = make_api_request("/recommendations", token=token)
            suggestions = suggestions_response.get('recommendations', []) if suggestions_response else []
            
            if suggestions:
                st.markdown('<div class="suggestions-box">', unsafe_allow_html=True)
                st.subheader("💡 Goal-Setting Suggestions")
                for i, suggestion in enumerate(suggestions, 1):
                    st.write(f"{i}. {suggestion}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🎯 Create Your First Goal", type="primary", use_container_width=True):
                    st.session_state[SESSION_STATE_KEY]['current_page'] = 'Goals'
                    st.rerun()
        else:
            st.warning("⚠️ Please complete your risk assessment first!")
            if st.button("📋 Take Assessment", type="primary"):
                st.session_state[SESSION_STATE_KEY]['current_page'] = 'Assessment'
                st.rerun()
        return
    
    # Display goals with progress
    for goal in goals:
        st.subheader(f"📊 {goal['name']}")
        
        # Get progress for this goal
        progress_response = make_api_request(f"/progress/{goal['id']}", token=token)
        progress = progress_response.get('progress', {}) if progress_response else {}
        
        if progress:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Current Amount", f"${progress.get('current_amount', 0):,.2f}")
            with col2:
                st.metric("Target Amount", f"${progress.get('target_amount', 0):,.2f}")
            with col3:
                st.metric("Progress", f"{progress.get('progress_pct', 0):.1f}%")
            with col4:
                st.metric("Days Remaining", progress.get('days_remaining', 0))
            
            # Progress visualization
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = progress.get('progress_pct', 0),
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Progress"},
                delta = {'reference': 100},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 25], 'color': "lightgray"},
                        {'range': [25, 50], 'color': "yellow"},
                        {'range': [50, 75], 'color': "orange"},
                        {'range': [75, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 100
                    }
                }
            ))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
            # Pacing status
            pacing_status = progress.get('pacing_status', 'unknown')
            pacing_detail = progress.get('pacing_detail', '')
            
            if pacing_status == 'ahead':
                st.success(f"🎉 {pacing_detail}")
            elif pacing_status == 'on_track':
                st.info(f"✅ {pacing_detail}")
            elif pacing_status == 'behind':
                st.warning(f"⚠️ {pacing_detail}")
            
            # Get recommendations
            recommendations_response = make_api_request(f"/recommendations?goal_id={goal['id']}", token=token)
            recommendations = recommendations_response.get('recommendations', []) if recommendations_response else []
            
            if recommendations:
                st.subheader("💡 Recommendations")
                for i, rec in enumerate(recommendations, 1):
                    st.write(f"{i}. {rec}")
        
        st.divider()

def notifications_page():
    """Notifications page"""
    st.markdown('<h1 class="main-header">Notifications</h1>', unsafe_allow_html=True)
    
    session = st.session_state[SESSION_STATE_KEY]
    token = session['access_token']
    
    # Get notifications
    notifications_response = make_api_request("/notifications", token=token)
    notifications = notifications_response.get('notifications', []) if notifications_response else []
    
    if notifications:
        for notification in notifications:
            with st.container():
                read_status = "✅" if notification['is_read'] else "🔔"
                st.markdown(f"""
                <div class="notification">
                    <h4>{read_status} {notification['title']}</h4>
                    <p>{notification['message']}</p>
                    <small>{notification['created_at']}</small>
                </div>
                """, unsafe_allow_html=True)
                
                if not notification['is_read']:
                    if st.button(f"Mark as Read", key=f"read_{notification['id']}"):
                        response = make_api_request(f"/notifications/{notification['id']}/read", "POST", token=token)
                        if response:
                            st.success("Notification marked as read!")
                            st.rerun()
    else:
        st.info("No notifications yet.")

def main():
    """Main application"""
    init_session_state()
    
    session = st.session_state[SESSION_STATE_KEY]
    
    if not session['authenticated']:
        login_page()
    else:
        # Sidebar navigation
        with st.sidebar:
            display_navigation_sidebar()
        
        # Route to appropriate page based on current_page
        current_page = session['current_page']
        
        if current_page == "Dashboard":
            dashboard_page()
        elif current_page == "Goals":
            goals_page()
        elif current_page == "Assessment":
            assessment_page()
        elif current_page == "Notifications":
            notifications_page()

if __name__ == "__main__":
    main()
