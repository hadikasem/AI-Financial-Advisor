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
import re
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
    .progress-bar-container {
        background: linear-gradient(135deg, #2c3e50, #34495e);
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .progress-bar-label {
        color: white;
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .progress-bar-wrapper {
        position: relative;
        margin: 1rem 0;
    }
    .progress-bar {
        width: 100%;
        height: 20px;
        background-color: rgba(255,255,255,0.1);
        border-radius: 10px;
        overflow: hidden;
        position: relative;
    }
    .progress-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease;
        position: relative;
    }
    .progress-fill.date {
        background: linear-gradient(90deg, #3498db, #5dade2);
    }
    .progress-fill.amount {
        background: linear-gradient(90deg, #e74c3c, #f1948a);
    }
    .progress-fill.timeline {
        background: linear-gradient(90deg, #2196F3, #03DAC6);
    }
    .progress-value {
        position: absolute;
        top: -35px;
        background-color: #2c3e50;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-weight: bold;
        font-size: 0.9rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        z-index: 10;
    }
    .progress-value::after {
        content: '';
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        width: 0;
        height: 0;
        border-left: 6px solid transparent;
        border-right: 6px solid transparent;
        border-top: 6px solid #2c3e50;
    }
    .progress-endpoints {
        display: flex;
        justify-content: space-between;
        margin-top: 0.5rem;
        color: rgba(255,255,255,0.8);
        font-size: 0.9rem;
    }
    .progress-endpoint {
        text-align: center;
        flex: 1;
    }
    .progress-endpoint.start {
        text-align: left;
    }
    .progress-endpoint.end {
        text-align: right;
    }
    .progress-endpoint.middle {
        text-align: center;
        font-weight: bold;
        color: white;
    }
    .button-align {
        margin-top: 1.5rem;
    }
    .goals-table {
        border-collapse: collapse;
        width: 100%;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-radius: 8px;
        overflow: hidden;
    }
    .goals-table th {
        background-color: #1f77b4;
        color: white;
        padding: 12px 8px;
        text-align: left;
        font-weight: bold;
        border: 1px solid #1565c0;
    }
    .goals-table td {
        padding: 10px 8px;
        border: 1px solid #e0e0e0;
        background-color: white;
    }
    .goals-table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    .goals-table tr:hover {
        background-color: #e3f2fd;
        cursor: pointer;
    }
    .goal-row {
        display: flex;
        align-items: center;
        padding: 8px;
        border-bottom: 1px solid #e0e0e0;
    }
    .goal-row:hover {
        background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

def extract_amount_from_goal_text(goal_text: str) -> Optional[float]:
    """Extract monetary amount from goal suggestion text and return as float"""
    try:
        # Common monetary amount patterns in goal suggestions
        patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # $15,000 or $15,000.00
            r'\$(\d+(?:\.\d{2})?)',  # $15000 or $15000.00
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*dollars?',  # 15,000 dollars
            r'(\d+(?:\.\d{2})?)\s*dollars?',  # 15000 dollars
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*USD',  # 15,000 USD
            r'(\d+(?:\.\d{2})?)\s*USD',  # 15000 USD
        ]
        
        for pattern in patterns:
            match = re.search(pattern, goal_text, re.IGNORECASE)
            if match:
                amount_str = match.group(1)
                # Remove commas and convert to float
                amount_str_clean = amount_str.replace(',', '')
                amount = float(amount_str_clean)
                
                # Reasonable amount range (between $100 and $10,000,000)
                if 100 <= amount <= 10000000:
                    return amount
        
        return None
    except Exception as e:
        print(f"Error extracting amount from '{goal_text}': {e}")
        return None

def extract_date_from_goal_text(goal_text: str) -> Optional[date]:
    """Extract date from goal suggestion text and return as date object"""
    try:
        # Common date patterns in goal suggestions
        patterns = [
            r'by\s+(\w+)\s+(\d{4})',  # "by June 2026"
            r'by\s+(\d{1,2})/(\d{4})',  # "by 6/2026"
            r'by\s+(\d{1,2})-(\d{4})',  # "by 6-2026"
            r'in\s+(\w+)\s+(\d{4})',   # "in June 2026"
            r'(\w+)\s+(\d{4})',        # "June 2026" (without by/in)
        ]
        
        month_names = {
            'january': 1, 'jan': 1,
            'february': 2, 'feb': 2,
            'march': 3, 'mar': 3,
            'april': 4, 'apr': 4,
            'may': 5,
            'june': 6, 'jun': 6,
            'july': 7, 'jul': 7,
            'august': 8, 'aug': 8,
            'september': 9, 'sep': 9, 'sept': 9,
            'october': 10, 'oct': 10,
            'november': 11, 'nov': 11,
            'december': 12, 'dec': 12
        }
        
        goal_text_lower = goal_text.lower()
        
        for pattern in patterns:
            match = re.search(pattern, goal_text_lower)
            if match:
                groups = match.groups()
                
                if len(groups) == 2:
                    month_str, year_str = groups
                    year = int(year_str)
                    
                    # Handle month
                    if month_str.isdigit():
                        month = int(month_str)
                    else:
                        month = month_names.get(month_str.lower())
                    
                    if month and 1 <= month <= 12 and year >= 2024:  # Reasonable year range
                        # Return the first day of the month
                        return date(year, month, 1)
        
        return None
    except Exception as e:
        print(f"Error extracting date from '{goal_text}': {e}")
        return None

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
        'prefilled_goal_date': None,
        'prefilled_goal_amount': None,
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
    
    # Update answered questions list - only add if question has an answer
    answered_questions = session.get('answered_questions', [])
    
    # Add current question to answered list if it has an answer
    if question_id in answers and answers[question_id]:
        # Check if this question is already in answered_questions
        existing_question = next((q for q in answered_questions if q['id'] == question_id), None)
        if existing_question:
            # Update existing question
            existing_question['answer'] = answers[question_id]
        else:
            # Add new answered question
            answered_questions.append({
                'id': question_id,
                'text': question_text,
                'answer': answers[question_id]
            })
        session['answered_questions'] = answered_questions
    
    # Always show progress bar
    st.markdown("---")
    
    # Progress header
    st.markdown("### 📊 Assessment Progress")
    
    # Create a better visual progress indicator
    total_questions = 12  # Assuming 12 questions total
    answered_count = len(answered_questions)
    progress_percentage = (answered_count / total_questions) * 100
    
    # Progress bar
    st.progress(progress_percentage / 100)
    st.markdown(f"**{answered_count}/{total_questions} questions answered**")
    
    # Question navigation buttons - show questions progressively
    st.markdown("**Navigate to questions:**")
    
    # Create list of questions to show
    questions_to_show = []
    
    # Map question IDs to question numbers
    question_id_to_num = {
        'age': 1, 'horizon': 2, 'emergency_fund_months': 3, 'dependents': 4,
        'income_stability': 5, 'experience': 6, 'loss_tolerance': 7, 'savings_rate': 8,
        'debt_load': 9, 'liquidity_need': 10, 'reaction_scenario': 11, 'investment_objective': 12
    }
    
    # Get all answered question numbers
    answered_question_nums = set()
    for q in answered_questions:
        q_num = question_id_to_num.get(q['id'], 0)
        if q_num > 0:
            answered_question_nums.add(q_num)
    
    # Get current question number
    current_question_num = question_id_to_num.get(question_id, 1)
    
    # Determine the maximum question number to show
    # Show all answered questions + current question
    max_question_num = max(max(answered_question_nums, default=0), current_question_num)
    
    # Show all questions from 1 to max question number
    for q_num in range(1, max_question_num + 1):
        # Find the question ID for this number
        q_id = next((qid for qid, num in question_id_to_num.items() if num == q_num), f"q{q_num}")
        
        # Check if this question is answered
        is_answered = q_num in answered_question_nums
        is_current = q_id == question_id
        
        questions_to_show.append({
            'num': q_num,
            'id': q_id,
            'answered': is_answered,
            'current': is_current
        })
    
    # Sort by question number
    questions_to_show.sort(key=lambda x: x['num'])
    
    
    # Display buttons horizontally in one line
    if questions_to_show:
        # Create columns for each question to show
        cols = st.columns(len(questions_to_show))
        
        for i, question_info in enumerate(questions_to_show):
            with cols[i]:
                q_num = question_info['num']
                is_answered = question_info['answered']
                is_current = question_info['current']
                
                # Style the button based on status
                if is_current:
                    button_style = "🔵"  # Current question
                    button_text = f"{button_style} Q{q_num}"
                elif is_answered:
                    button_style = "✅"  # Answered
                    button_text = f"{button_style} Q{q_num}"
                else:
                    button_style = "⚪"  # Not answered yet
                    button_text = f"{button_style} Q{q_num}"
                
                if st.button(
                    button_text,
                    key=f"progress_q{q_num}",
                    help=f"Question {q_num}" + (" (Current)" if is_current else " (Answered)" if is_answered else " (Not answered)"),
                    use_container_width=True
                ):
                    navigate_to_question(question_info['id'])
    
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
        ("➕", "Create Goal"),
        ("🪜", "Ongoing Goals"),
        ("🏆", "Completed Goals"),
        ("🎮", "Gamification"),
        ("📋", "Assessment"),
        ("🔔", "Notifications")
    ]
    
    # Check if user has completed assessment
    assessment_completed = session.get('assessment_completed')
    
    if not assessment_completed:
        st.warning("⚠️ Please complete your risk assessment first!")
        # Force navigation to Assessment
        st.session_state[SESSION_STATE_KEY]['current_page'] = 'Assessment'
    
    # Check if assessment is completed
    assessment_completed = session.get('assessment_completed')
    
    # Display navigation items
    for icon, page_name in nav_items:
        is_active = session['current_page'] == page_name
        active_class = "active" if is_active else ""
        
        # Disable all buttons except Assessment if assessment not completed
        if page_name == "Assessment" or assessment_completed:
            if st.button(f"{icon} {page_name}", key=f"nav_{page_name}", use_container_width=True):
                st.session_state[SESSION_STATE_KEY]['current_page'] = page_name
                st.rerun()
        else:
            st.button(f"{icon} {page_name}", key=f"nav_{page_name}", use_container_width=True, disabled=True)
    
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
                        
                        # Load existing assessment if any
                        try:
                            assessment_response = make_api_request("/assessment/current", token=response['access_token'])
                            if assessment_response and assessment_response.get('status') == 'completed':
                                st.session_state[SESSION_STATE_KEY]['assessment_completed'] = assessment_response
                            elif assessment_response and assessment_response.get('status') == 'in_progress':
                                st.session_state[SESSION_STATE_KEY]['current_assessment'] = assessment_response
                        except Exception as e:
                            print(f"Error loading existing assessment: {e}")
                        
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
    
    if suggestions_response and 'error' in suggestions_response:
        st.error(f"❌ {suggestions_response['error']}")
        st.info("Please check your LLM configuration and try again.")
    elif suggestions_response and suggestions_response.get('recommendations'):
        suggestions = suggestions_response['recommendations']
        st.markdown('<div class="suggestions-box">', unsafe_allow_html=True)
        st.subheader("💡 Personalized Recommendations")
        for i, suggestion in enumerate(suggestions, 1):
            st.write(f"{i}. {suggestion}")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.error("❌ Unable to generate personalized recommendations. Please check your LLM configuration.")
    
    # Prompt to create goals
    st.success("🎉 Assessment complete! Now let's set up your financial goals.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("🔄 Retake Assessment", use_container_width=True):
            # Start a new assessment using the API
            session = st.session_state[SESSION_STATE_KEY]
            token = session['access_token']
            
            try:
                response = make_api_request("/assessment/retake", "POST", token=token)
                if response and "assessment_id" in response:
                    # Clear session state and start fresh
                    session['assessment_completed'] = None
                    session['current_assessment'] = response
                    session['answered_questions'] = []
                    session['help_chat_open'] = False
                    session['help_chat_messages'] = []
                    session['help_questions_count'] = 0
                    st.success("New assessment started!")
                    st.rerun()
                else:
                    st.error("Failed to start new assessment. Please try again.")
            except Exception as e:
                st.error(f"Error starting new assessment: {str(e)}")
    with col2:
        if st.button("🎯 Set Up Your Goals", type="primary", use_container_width=True):
            st.session_state[SESSION_STATE_KEY]['current_page'] = 'Create Goal'
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
        
        # Calculate the actual question number based on question ID
        question_id_to_num = {
            'age': 1, 'horizon': 2, 'emergency_fund_months': 3, 'dependents': 4,
            'income_stability': 5, 'experience': 6, 'loss_tolerance': 7, 'savings_rate': 8,
            'debt_load': 9, 'liquidity_need': 10, 'reaction_scenario': 11, 'investment_objective': 12
        }
        actual_question_num = question_id_to_num.get(question['id'], len(answers) + 1)
        
        st.subheader(f"Question {actual_question_num}")
        st.write(question['question'])
        
        # Get current answer for this question
        current_answer = answers.get(question['id'], '')
        
        # Handle different question types
        if question['type'] == 'number':
            validation = question.get('validation', {})
            min_val = float(validation.get('min', 0))
            max_val = float(validation.get('max', 1000))
            
            # For questions 3, 4, 8 (emergency_fund_months, dependents, savings_rate), use integer input
            if question['id'] in ['emergency_fund_months', 'dependents', 'savings_rate']:
                step_val = 1
                default_value = int(float(current_answer)) if current_answer else int(min_val)
                answer = st.number_input(
                    "Your answer:",
                    min_value=int(min_val),
                    max_value=int(max_val),
                    step=step_val,
                    value=default_value,
                    format="%d"
                )
            else:
                step_val = 1.0 if question['id'] in ['age', 'horizon'] else 0.1
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
            
            # Map question IDs to question numbers
            question_id_to_num = {
                'age': 1, 'horizon': 2, 'emergency_fund_months': 3, 'dependents': 4,
                'income_stability': 5, 'experience': 6, 'loss_tolerance': 7, 'savings_rate': 8,
                'debt_load': 9, 'liquidity_need': 10, 'reaction_scenario': 11, 'investment_objective': 12
            }
            
            # Get current question number
            current_question_num = question_id_to_num.get(question['id'], 1)
            prev_question_num = current_question_num - 1
            
            # Check if there's a previous question (question number > 0)
            if prev_question_num > 0:
                # Find the question ID for the previous question number
                prev_question_id = next((qid for qid, num in question_id_to_num.items() if num == prev_question_num), None)
                
                if prev_question_id:
                    if st.button("⬅️ Previous Question"):
                        navigate_to_question(prev_question_id)
        
        with col2:
            if st.button("Submit Answer", type="primary"):
                if answer is not None:
                    with st.spinner("Submitting answer..."):
                        response = make_api_request("/assessment/answer", "POST", {
                            "question_id": question['id'],
                            "answer": str(answer)
                        }, token=token)
                    
                    if response:
                        # Update answered questions list
                        session = st.session_state[SESSION_STATE_KEY]
                        answered_questions = session.get('answered_questions', [])
                        
                        # Add current question to answered list
                        # Use the actual question ID from the backend (age, horizon, etc.)
                        q_id = question['id']
                        
                        existing_question = next((q for q in answered_questions if q['id'] == q_id), None)
                        if existing_question:
                            existing_question['answer'] = str(answer)
                        else:
                            answered_questions.append({
                                'id': q_id,
                                'text': question['question'],
                                'answer': str(answer)
                            })
                        session['answered_questions'] = answered_questions
                        
                        if "next_step" in response and response["next_step"] == "complete_assessment":
                            # Assessment complete, calculate results
                            with st.spinner("Calculating your risk profile..."):
                                complete_response = make_api_request("/assessment/complete", "POST", token=token)
                            if complete_response:
                                st.session_state[SESSION_STATE_KEY]['assessment_completed'] = complete_response
                                
                                # Update streak for completing assessment
                                try:
                                    streak_response = make_api_request("/gamification/update-streak", "POST", {}, token=token)
                                    if streak_response and streak_response.get('success'):
                                        if streak_response.get('streak_bonus', 0) > 0:
                                            st.info(f"🔥 Assessment completed! Streak bonus: {streak_response.get('streak_bonus', 0)} points")
                                except Exception as e:
                                    st.error(f"Error updating streak: {str(e)}")
                                
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
                # Cap progress at 100% for Streamlit compatibility
                progress_value = min(1.0, progress_pct / 100)
                st.progress(progress_value)
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

def create_date_progress_bar(goal: dict, simulated_until_date: str):
    """Create a date progress bar showing start date, simulated until date, and target date"""
    
    # Parse dates
    start_date = datetime.fromisoformat(goal['start_date']).date()
    target_date = datetime.fromisoformat(goal['target_date']).date()
    simulated_date = datetime.fromisoformat(simulated_until_date).date() if simulated_until_date else date.today()
    
    # Calculate progress percentage
    total_days = (target_date - start_date).days
    elapsed_days = (simulated_date - start_date).days
    progress_pct = min(100, max(0, (elapsed_days / total_days) * 100)) if total_days > 0 else 0
    
    # Create the progress bar HTML
    progress_html = f"""
    <div class="progress-bar-container">
        <div class="progress-bar-label">📅 GOAL TIMELINE</div>
        <div class="progress-bar-wrapper">
            <div class="progress-bar">
                <div class="progress-fill date" style="width: {progress_pct}%"></div>
                <div class="progress-value" style="left: {progress_pct}%">
                    {simulated_date.strftime('%Y-%m-%d')}
                </div>
            </div>
            <div class="progress-endpoints">
                <div class="progress-endpoint start">
                    <strong>START</strong><br>
                    {start_date.strftime('%Y-%m-%d')}
                </div>
                <div class="progress-endpoint middle">
                    <strong>{progress_pct:.1f}%</strong><br>
                    {simulated_date.strftime('%Y-%m-%d')}<br>
                    ELAPSED
                </div>
                <div class="progress-endpoint end">
                    <strong>TARGET</strong><br>
                    {target_date.strftime('%Y-%m-%d')}
                </div>
            </div>
        </div>
    </div>
    """
    
    return progress_html

def create_amount_progress_bar(goal: dict, current_amount: float, is_completed: bool = False):
    """Create an amount progress bar showing 0, current amount, and target amount"""
    target_amount = float(goal['target_amount'])
    current_amount = float(current_amount)
    
    # Calculate progress percentage
    if is_completed or current_amount >= target_amount:
        progress_pct = 100.0
    else:
        progress_pct = min(100, max(0, (current_amount / target_amount) * 100)) if target_amount > 0 else 0
    
    # Create the progress bar HTML
    progress_html = f"""
    <div class="progress-bar-container">
        <div class="progress-bar-label">💰 GOAL AMOUNT</div>
        <div class="progress-bar-wrapper">
            <div class="progress-bar">
                <div class="progress-fill amount" style="width: {progress_pct}%"></div>
                <div class="progress-value" style="left: {progress_pct}%">
                    ${current_amount:,.0f}
                </div>
            </div>
            <div class="progress-endpoints">
                <div class="progress-endpoint start">
                    <strong>$0</strong><br>
                    START
                </div>
                <div class="progress-endpoint middle">
                    <strong>{progress_pct:.1f}%</strong><br>
                    ${current_amount:,.0f}<br>
                    ACHIEVED
                </div>
                <div class="progress-endpoint end">
                    <strong>${target_amount:,.0f}</strong><br>
                    TARGET
                </div>
            </div>
        </div>
    </div>
    """
    
    return progress_html

def display_goal_completion_message(goal_status: dict, goal: dict, simulated_until_date: str = None):
    """Display congratulations message for completed goals"""
    st.markdown("---")
    
    # Success message with celebration
    st.success("🎉 **GOAL COMPLETED!** 🎉")
    
    # Get progress data to calculate days remaining
    from datetime import datetime, date
    if simulated_until_date:
        try:
            simulated_date = datetime.fromisoformat(simulated_until_date).date()
            target_date = datetime.fromisoformat(goal['target_date']).date()
            days_remaining = (target_date - simulated_date).days
        except:
            days_remaining = 0
    else:
        days_remaining = 0
    
    # Display achievement summary stats
    st.markdown("### 🏆 Achievement Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Goal Details:**
        - **Goal:** {goal['name']}
        - **Category:** {goal['category']}
        - **Target Amount:** ${goal['target_amount']:,.2f}
        - **Target Date:** {goal['target_date']}
        """)
    
    with col2:
        st.markdown(f"""
        **Achievement Stats:**
        - **Current Amount:** ${goal['current_amount']:,.2f}
        - **Simulated Until:** {simulated_until_date if simulated_until_date else 'Current simulation date'}
        - **Completed:** {days_remaining} days early! ⏰
        - **Status:** Target exceeded! 🚀
        """)
    
    # Celebration animation or additional message
    st.balloons()
    st.markdown("**Congratulations on achieving your financial goal!** 🎊")

def display_target_date_reached_message(goal_status: dict, goal: dict, token: str, simulated_until_date: str = None):
    """Display message when target date is reached but goal not completed"""
    st.markdown("---")
    
    # Warning message
    st.warning("⏰ **Target Date Reached** ⏰")
    
    # Display current status
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Current Status:**
        - **Goal:** {goal['name']}
        - **Target Amount:** ${goal['target_amount']:,.2f}
        - **Current Amount:** ${goal['current_amount']:,.2f}
        - **Remaining:** ${goal_status.get('remaining_amount', 0):,.2f}
        """)
    
    with col2:
        st.markdown(f"""
        **Progress:**
        - **Completion:** {(goal['current_amount'] / goal['target_amount'] * 100):.1f}%
        - **Status:** Target date reached
        - **Reached on:** {simulated_until_date if simulated_until_date else 'Current simulation date'}
        - **Message:** {goal_status.get('message', '')}
        """)
    
    # Show progress bars for target date reached
    if simulated_until_date:
        st.markdown("### 📊 Current Progress")
        date_progress_html = create_date_progress_bar(goal, simulated_until_date)
        st.markdown(date_progress_html, unsafe_allow_html=True)
        
        amount_progress_html = create_amount_progress_bar(goal, goal['current_amount'])
        st.markdown(amount_progress_html, unsafe_allow_html=True)
    
    # Option to extend goal
    st.markdown("### 🔄 Extend Goal Target Date")
    st.write("Would you like to extend your goal target date to give yourself more time?")
    
    with st.form(f"extend_goal_{goal['id']}"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Calculate suggested new date (add 3 months)
            current_target = datetime.fromisoformat(goal['target_date']).date()
            suggested_date = current_target + timedelta(days=90)  # 3 months
            new_target_date = st.date_input(
                "New Target Date",
                value=suggested_date,
                min_value=current_target + timedelta(days=1),
                help="Select a new target date for your goal"
            )
        
        with col2:
            st.write("**Current Target Date:**")
            st.write(f"📅 {goal['target_date']}")
            st.write("**Suggested New Date:**")
            st.write(f"📅 {suggested_date.strftime('%Y-%m-%d')}")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            extend_goal = st.form_submit_button("Extend Goal", type="primary")
        with col2:
            keep_current = st.form_submit_button("Keep Current")
        
        if extend_goal and new_target_date:
            try:
                response = make_api_request(f"/goals/{goal['id']}/extend", "POST", {
                    "new_target_date": new_target_date.isoformat()
                }, token=token)
                
                if response:
                    st.success("✅ Goal target date extended successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to extend goal. Please try again.")
            except Exception as e:
                st.error(f"❌ Error extending goal: {str(e)}")
        
        if keep_current:
            st.info("Goal will remain with current target date. Consider increasing your savings rate to reach the goal faster!")

def display_completed_goal_summary(goal: dict, token: str):
    """Display summary for completed goals"""
    st.markdown(f"#### 🏆 {goal['name']}")
    
    # Get progress summary for simulated until date
    progress_summary_response = make_api_request("/progress/summary", token=token)
    progress_summary = progress_summary_response if progress_summary_response else {}
    simulated_until_date = progress_summary.get('last_mock_date')
    
    # Display achievement summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Goal Details:**
        - **Goal:** {goal['name']}
        - **Category:** {goal['category']}
        - **Target Amount:** ${goal['target_amount']:,.2f}
        - **Target Date:** {goal['target_date']}
        """)
    
    with col2:
        st.markdown(f"""
        **Achievement Stats:**
        - **Current Amount:** ${goal['current_amount']:,.2f}
        - **Simulated Until:** {simulated_until_date if simulated_until_date else 'Current simulation date'}
        - **Status:** Goal completed! ✅
        - **Progress:** 100.0%
        """)
    
    st.markdown("---")

def display_goal_with_progress(goal: dict, token: str):
    """Display active goal with progress tracking"""
    st.markdown(f"## 🎯 {goal['name']}")
    
    # Get progress for this goal
    progress_response = make_api_request(f"/progress/{goal['id']}", token=token)
    progress = progress_response.get('progress', {}) if progress_response else {}
    
    # Get goal completion status
    status_response = make_api_request(f"/goals/{goal['id']}/status", token=token)
    goal_status = status_response if status_response else {}
    
    # Get simulated until date for progress bars
    progress_summary_response = make_api_request("/progress/summary", token=token)
    progress_summary = progress_summary_response if progress_summary_response else {}
    simulated_until_date = progress_summary.get('last_mock_date')
    
    # Display progress bars at the top (always visible)
    st.markdown("#### 📊 Progress Visualization")
    
    # Always show progress bars (use goal start date as fallback for simulated_until_date)
    if simulated_until_date:
        date_progress_html = create_date_progress_bar(goal, simulated_until_date)
    else:
        # Use goal start date as fallback
        date_progress_html = create_date_progress_bar(goal, goal['start_date'])
    st.markdown(date_progress_html, unsafe_allow_html=True)
    
    # Amount progress bar
    is_completed = goal_status.get('status') == 'completed'
    amount_progress_html = create_amount_progress_bar(goal, progress.get('current_amount', 0), is_completed)
    st.markdown(amount_progress_html, unsafe_allow_html=True)
    
    if progress:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Current Amount", f"${progress.get('current_amount', 0):,.2f}")
        with col2:
            st.metric("Target Amount", f"${progress.get('target_amount', 0):,.2f}")
        with col3:
            progress_pct = progress.get('progress_pct', 0)
            # Ensure progress stays at 100% for completed goals
            if goal_status.get('status') == 'completed':
                progress_pct = 100.0
            st.metric("Progress", f"{progress_pct:.1f}%")
        with col4:
            days_remaining = progress.get('days_remaining', 0)
            st.metric("Days Remaining", days_remaining)
        
        # Check goal completion status and display appropriate message
        if goal_status.get('status') == 'completed':
            display_goal_completion_message(goal_status, goal, simulated_until_date)
        elif goal_status.get('status') == 'target_date_reached':
            display_target_date_reached_message(goal_status, goal, token, simulated_until_date)
        
        
        # Pacing status
        pacing_status = progress.get('pacing_status', 'unknown')
        pacing_detail = progress.get('pacing_detail', '')
        
        if pacing_status == 'ahead':
            st.success(f"🎉 {pacing_detail}")
        elif pacing_status == 'on_track':
            st.info(f"✅ {pacing_detail}")
        elif pacing_status == 'behind':
            st.warning(f"⚠️ {pacing_detail}")
        
        # Get recommendations - only show if goal is not completed
        if goal_status.get('status') != 'completed':
            recommendations_response = make_api_request(f"/recommendations?goal_id={goal['id']}", token=token)
            
            if recommendations_response and 'error' in recommendations_response:
                st.error(f"❌ {recommendations_response['error']}")
                st.info("Please check your LLM configuration.")
            elif recommendations_response and recommendations_response.get('recommendations'):
                recommendations = recommendations_response['recommendations']
                st.subheader("💡 Recommendations")
                for recommendation in recommendations:
                    st.info(f"💡 {recommendation}")
    
    st.markdown("---")

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
            with st.spinner("Generating personalized goal suggestions..."):
                suggestions_response = make_api_request("/goals/suggestions", token=token)
                suggestions = suggestions_response.get('suggestions', []) if suggestions_response else []
                session['cached_goal_suggestions'] = suggestions
        else:
            suggestions = cached_suggestions
        
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                col1, col2 = st.columns([3, 1])
                with col1:
                    # Use markdown with consistent styling instead of st.write
                    st.markdown(f"**{i}.** {suggestion}")
                with col2:
                    if st.button(f"Use This Goal", key=f"use_suggestion_{i}", help=f"Use '{suggestion}' as your goal name"):
                        # Pre-fill the create goal form with this suggestion
                        session = st.session_state[SESSION_STATE_KEY]
                        session['prefilled_goal'] = suggestion
                        
                        # Extract date from suggestion text
                        extracted_date = extract_date_from_goal_text(suggestion)
                        if extracted_date:
                            session['prefilled_goal_date'] = extracted_date
                        else:
                            session['prefilled_goal_date'] = None
                        
                        # Extract amount from suggestion text
                        extracted_amount = extract_amount_from_goal_text(suggestion)
                        if extracted_amount:
                            session['prefilled_goal_amount'] = extracted_amount
                        else:
                            session['prefilled_goal_amount'] = None
                        
                        # Navigate to Create Goal page
                        session['current_page'] = 'Create Goal'
                        # Don't clear cached suggestions - keep them persistent
                        # session['cached_goal_suggestions'] = None  # Removed this line
                        st.success(f"Selected: {suggestion}")
                        st.rerun()
            
            # Button to get more suggestions
            if len(suggestions) < 100:
                if st.button("🔄 Get More Suggestions"):
                    with st.spinner("Generating more suggestions..."):
                        more_suggestions_response = make_api_request("/goals/suggestions", "POST", {
                            "request_more": True,
                            "existing_suggestions": suggestions
                        }, token=token)
                        if more_suggestions_response and 'suggestions' in more_suggestions_response:
                            # Update cached suggestions with new ones
                            session['cached_goal_suggestions'] = more_suggestions_response['suggestions']
                            st.success("More suggestions generated!")
                            st.rerun()
                        elif more_suggestions_response and 'error' in more_suggestions_response:
                            st.error(more_suggestions_response['error'])
                        else:
                            st.error("Failed to generate more suggestions. Please try again.")
            else:
                st.info("Maximum number of suggested goals reached (100).")
        else:
            st.info("No personalized suggestions available. Complete your assessment for better recommendations.")
    else:
        st.info("Complete your risk assessment to get personalized goal suggestions!")

def dashboard_page():
    """Enhanced Dashboard Overview with comprehensive goal management"""
    st.markdown('<h1 class="main-header">Dashboard Overview</h1>', unsafe_allow_html=True)
    
    # Get user token - fix the token retrieval
    session = st.session_state.get(SESSION_STATE_KEY, {})
    token = session.get('access_token')
    if not token:
        st.error("Please log in to view your dashboard")
        return
    
    # Get user goals
    goals_response = make_api_request("/goals", token=token)
    if not goals_response:
        st.error("Failed to load goals")
        return
    
    goals = goals_response.get('goals', [])
    active_goals = [g for g in goals if not g.get('completed', False)]
    completed_goals = [g for g in goals if g.get('completed', False)]
    
    # Summary cards
    st.markdown("### 📊 Summary Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Goals", len(active_goals))
    with col2:
        st.metric("Completed Goals", len(completed_goals))
    with col3:
        # Calculate total saved from goal accounts
        total_saved = 0
        for goal in goals:
            try:
                account_response = make_api_request(f"/goals/{goal['id']}/account", token=token)
                if account_response and account_response.get('account'):
                    total_saved += account_response['account'].get('balance', 0)
                else:
                    total_saved += goal.get('current_amount', 0)
            except:
                total_saved += goal.get('current_amount', 0)
        st.metric("Total Saved", f"${total_saved:,.2f}")
    with col4:
        if goals:
            overall_progress = 0
            for goal in goals:
                try:
                    account_response = make_api_request(f"/goals/{goal['id']}/account", token=token)
                    if account_response and account_response.get('account'):
                        current_amount = account_response['account'].get('balance', 0)
                    else:
                        current_amount = goal.get('current_amount', 0)
                    target_amount = goal.get('target_amount', 1)
                    if target_amount > 0:
                        overall_progress += (current_amount / target_amount) * 100
                except:
                    pass
            overall_progress = overall_progress / len(goals) if goals else 0
            st.metric("Overall Progress", f"{overall_progress:.1f}%")
        else:
            st.metric("Overall Progress", "0%")
    
    # Gamification widget
    st.markdown("---")
    st.markdown("### 🎮 Gamification Status")
    
    try:
        gamification_response = make_api_request("/gamification/data", token=token)
        if gamification_response and gamification_response.get('success'):
            gamification_data = gamification_response
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                streak = gamification_data.get('current_streak', 0)
                if streak >= 7:
                    st.success(f"🔥 {streak}-day streak! You're on fire!")
                elif streak >= 3:
                    st.info(f"🔥 {streak}-day streak! Keep it going!")
                else:
                    st.metric("🔥 Current Streak", f"{streak} days")
            
            with col2:
                points = gamification_data.get('total_points', 0)
                level = gamification_data.get('level', 'Bronze')
                st.metric("⭐ Points", f"{points} ({level})")
            
            with col3:
                next_milestone = gamification_data.get('next_milestone')
                if next_milestone:
                    st.info(f"🎯 Next: {next_milestone['level']}")
                else:
                    st.success("🏆 All milestones achieved!")
        else:
            st.info("🎮 Complete your first goal to start earning points!")
    except Exception as e:
        st.info("🎮 Gamification features loading...")
    
    # Quick action buttons
    st.markdown("---")
    st.markdown("### 🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ Create New Goal", use_container_width=True, type="primary"):
            st.session_state[SESSION_STATE_KEY]['current_page'] = "Create Goal"
            st.rerun()
    
    with col2:
        if st.button("📊 View Active Goals", use_container_width=True):
            st.session_state[SESSION_STATE_KEY]['current_page'] = "Ongoing Goals"
            st.rerun()
    
    with col3:
        if st.button("🏆 View Completed Goals", use_container_width=True):
            st.session_state[SESSION_STATE_KEY]['current_page'] = "Completed Goals"
            st.rerun()
    
    # Recent activity section
    st.markdown("---")
    st.markdown("### 📈 Recent Activity")
    
    if active_goals:
        # Show recent transactions from all goals
        all_transactions = []
        for goal in active_goals:
            try:
                transactions_response = make_api_request(f"/goals/{goal['id']}/transactions", token=token)
                if transactions_response and transactions_response.get('transactions'):
                    for transaction in transactions_response['transactions']:
                        transaction['goal_name'] = goal['name']
                        all_transactions.append(transaction)
            except:
                pass
        
        if all_transactions:
            # Sort by date and show last 5
            all_transactions.sort(key=lambda x: x.get('date', ''), reverse=True)
            recent_transactions = all_transactions[:5]
            
            for transaction in recent_transactions:
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"**{transaction.get('description', 'Transaction')}** ({transaction.get('goal_name', 'Unknown Goal')})")
                with col2:
                    amount = transaction.get('amount', 0)
                    if transaction.get('transaction_type') == 'income':
                        st.write(f"💰 +${amount:,.2f}")
                    else:
                        st.write(f"💸 -${amount:,.2f}")
                with col3:
                    st.write(transaction.get('category', 'N/A'))
                with col4:
                    st.write(transaction.get('date', 'N/A')[:10])
        else:
            st.info("No recent activity. Start simulating progress on your goals to see transactions here.")
    else:
        st.info("No active goals found. Create your first goal to get started!")
    
    # Top active goals progress overview
    if active_goals:
        st.markdown("---")
        st.markdown("### 🎯 Top Active Goals Progress")
        
        # Show top 3 active goals by progress
        goal_progress = []
        for goal in active_goals:
            try:
                # First try to get current amount from account API
                account_response = make_api_request(f"/goals/{goal['id']}/account", token=token)
                if account_response and account_response.get('account'):
                    current_amount = float(account_response['account'].get('balance', 0))
                    data_source = "account API"
                else:
                    # Fallback to goal's current_amount
                    current_amount = float(goal.get('current_amount', 0))
                    data_source = "goal data"
                
                target_amount = float(goal.get('target_amount', 1))
                
                # Calculate progress percentage with proper handling
                if target_amount > 0:
                    progress_pct = (current_amount / target_amount) * 100
                    # Cap progress at 100%
                    progress_pct = min(100.0, progress_pct)
                else:
                    progress_pct = 0.0
                
                # Debug: show data source
                st.caption(f"Debug: {goal['name']} - Data from: {data_source}")
                
                goal_progress.append((goal, progress_pct, current_amount))
            except Exception as e:
                # If there's any error, use goal's current_amount as fallback
                current_amount = float(goal.get('current_amount', 0))
                target_amount = float(goal.get('target_amount', 1))
                progress_pct = (current_amount / target_amount) * 100 if target_amount > 0 else 0
                progress_pct = min(100.0, progress_pct)
                st.caption(f"Debug: {goal['name']} - Error: {str(e)}")
                goal_progress.append((goal, progress_pct, current_amount))
        
        # Sort by progress and show top 3
        goal_progress.sort(key=lambda x: x[1], reverse=True)
        top_goals = goal_progress[:3]
        
        for i, (goal, progress_pct, current_amount) in enumerate(top_goals, 1):
            progress_pct = min(100, progress_pct)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{i}. {goal['name']}**")
                st.progress(progress_pct / 100)
                # Debug info - show current and target amounts
                st.caption(f"Current: ${current_amount:,.2f} | Target: ${float(goal.get('target_amount', 0)):,.2f}")
            with col2:
                st.write(f"{progress_pct:.1f}%")
    
    # Smart recommendations
    st.markdown("---")
    st.markdown("### 💡 Smart Recommendations")
    
    if not active_goals:
        st.info("🎯 **Create your first goal!** Start by setting a financial target and begin your journey towards financial success.")
    elif len(active_goals) == 1:
        st.info("📈 **Great start!** Consider creating additional goals to diversify your financial portfolio.")
    elif len(active_goals) < 3:
        st.info("🚀 **Keep it up!** You're making great progress. Consider adding more goals to maximize your financial growth.")
    else:
        st.info("🌟 **Excellent work!** You have multiple active goals. Keep monitoring your progress and adjust strategies as needed.")
    
    # Additional insights
    if active_goals:
        st.markdown("---")
        st.markdown("### 📊 Goal Insights")
        
        # Calculate average progress
        total_progress = 0
        for goal in active_goals:
            try:
                account_response = make_api_request(f"/goals/{goal['id']}/account", token=token)
                if account_response and account_response.get('account'):
                    current_amount = account_response['account'].get('balance', 0)
                else:
                    current_amount = goal.get('current_amount', 0)
                target_amount = goal.get('target_amount', 1)
                if target_amount > 0:
                    total_progress += (current_amount / target_amount) * 100
            except:
                pass
        
        avg_progress = total_progress / len(active_goals) if active_goals else 0
        
        if avg_progress < 25:
            st.warning("💪 **Keep pushing!** Your goals are just getting started. Consider increasing your savings rate or adjusting timelines.")
        elif avg_progress < 50:
            st.info("📈 **Good progress!** You're on track. Consider reviewing your strategies to accelerate progress.")
        elif avg_progress < 75:
            st.success("🎯 **Great momentum!** You're making excellent progress. Stay consistent with your approach.")
        else:
            st.success("🏆 **Almost there!** You're very close to achieving your goals. Keep up the excellent work!")

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
        elif current_page == "Create Goal":
            create_goal_page()
        elif current_page == "Ongoing Goals":
            ongoing_goals_page()
        elif current_page == "Completed Goals":
            completed_goals_page()
        elif current_page == "Gamification":
            gamification_page()
        elif current_page == "Assessment":
            assessment_page()
        elif current_page == "Notifications":
            notifications_page()

def gamification_page():
    """Gamification page with milestones, streaks, and leaderboard"""
    st.markdown('<h1 class="main-header">🎮 Gamification</h1>', unsafe_allow_html=True)
    
    session = st.session_state[SESSION_STATE_KEY]
    token = session['access_token']
    
    # Get gamification data
    try:
        gamification_response = make_api_request("/gamification/data", token=token)
        if gamification_response and gamification_response.get('success'):
            gamification_data = gamification_response
        else:
            st.error("Failed to load gamification data")
            return
    except Exception as e:
        st.error(f"Error loading gamification data: {str(e)}")
        return
    
    # Display user stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔥 Current Streak", f"{gamification_data.get('current_streak', 0)} days")
    
    with col2:
        st.metric("⭐ Total Points", f"{gamification_data.get('total_points', 0)}")
    
    with col3:
        st.metric("🏆 Level", gamification_data.get('level', 'Bronze'))
    
    with col4:
        total_saved = gamification_data.get('total_saved', 0)
        # Ensure total_saved is a number, not a string
        try:
            total_saved = float(total_saved) if total_saved else 0
        except (ValueError, TypeError):
            total_saved = 0
        st.metric("💰 Total Saved", f"${total_saved:,.2f}")
    
    st.markdown("---")
    
    # Milestone Tracker
    st.subheader("🏁 Milestone Tracker")
    
    achieved_milestones = gamification_data.get('achieved_milestones', [])
    next_milestone = gamification_data.get('next_milestone')
    total_saved = gamification_data.get('total_saved', 0)
    # Ensure total_saved is a number, not a string
    try:
        total_saved = float(total_saved) if total_saved else 0
    except (ValueError, TypeError):
        total_saved = 0
    
    if achieved_milestones:
        st.markdown("### ✅ Achieved Milestones")
        for milestone in achieved_milestones:
            st.success(f"🎉 {milestone['level']} - ${milestone['amount']:,}")
    
    if next_milestone:
        st.markdown("### 🎯 Next Milestone")
        progress = min(total_saved / next_milestone['amount'], 1.0)
        st.progress(progress, text=f"{next_milestone['level']} - ${total_saved:,.0f} / ${next_milestone['amount']:,}")
        
        remaining = next_milestone['amount'] - total_saved
        if remaining > 0:
            st.info(f"💰 You need ${remaining:,.2f} more to unlock {next_milestone['level']}!")
    
    # Level Progress
    st.markdown("---")
    st.subheader("📈 Level Progress")
    
    next_level = gamification_data.get('next_level')
    if next_level:
        current_points = gamification_data.get('total_points', 0)
        points_needed = next_level['points_needed']
        total_for_next = current_points + points_needed
        
        progress = current_points / total_for_next if total_for_next > 0 else 0
        st.progress(progress, text=f"{current_points} / {total_for_next} points")
        st.info(f"🎯 {points_needed} more points to reach {next_level['name']} level!")
    
    # Leaderboard
    st.markdown("---")
    st.subheader("🏆 Leaderboard")
    
    try:
        leaderboard_response = make_api_request("/gamification/leaderboard?limit=10", token=token)
        if leaderboard_response and leaderboard_response.get('success'):
            leaderboard = leaderboard_response.get('leaderboard', [])
            
            if leaderboard:
                st.markdown("### 🥇 Top Performers")
                for i, user in enumerate(leaderboard):
                    rank_emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                    st.markdown(f"{rank_emoji} **{user['username']}** - {user['level']} ({user['total_points']} pts)")
            else:
                st.info("No leaderboard data available yet.")
        else:
            st.error("Failed to load leaderboard")
    except Exception as e:
        st.error(f"Error loading leaderboard: {str(e)}")
    
    # Streak Saver Challenge
    st.markdown("---")
    st.subheader("🔥 Streak Saver Challenge")
    
    st.markdown("""
    **Keep your streak alive!** 🎯
    
    Your streak increases every time you:
    - ✅ Create a new goal
    - ✅ Update progress on existing goals
    - ✅ Complete a goal
    - ✅ Take the risk assessment
    
    **Current Streak:** {streak} days
    
    💡 **Tip:** Check in daily to maintain your streak and earn bonus points!
    """.format(streak=gamification_data.get('current_streak', 0)))
    
    # Update streak button
    if st.button("🔄 Update My Streak", type="primary"):
        try:
            streak_response = make_api_request("/gamification/update-streak", "POST", {}, token=token)
            if streak_response and streak_response.get('success'):
                st.success(f"🎉 Streak updated! Current streak: {streak_response.get('current_streak', 0)} days")
                if streak_response.get('streak_bonus', 0) > 0:
                    st.info(f"⭐ Bonus points earned: {streak_response.get('streak_bonus', 0)}")
                st.rerun()
            else:
                st.error("Failed to update streak")
        except Exception as e:
            st.error(f"Error updating streak: {str(e)}")

def create_goal_page():
    """Create Goal page with goal creation form and suggestions"""
    st.markdown('<h1 class="main-header">Create New Goal</h1>', unsafe_allow_html=True)
    
    session = st.session_state[SESSION_STATE_KEY]
    token = session['access_token']
    
    # Goal creation form
    st.subheader("🎯 Create Your Financial Goal")
    
    with st.form("create_goal_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Check for prefilled goal from suggestions
            prefilled_goal = session.get('prefilled_goal', '')
            goal_name = st.text_input("Goal Name", value=prefilled_goal, placeholder="e.g., Save for Building a Chalet")
            category = st.selectbox(
                "Category",
                ["Emergency Fund", "Vacation", "Education", "Home Purchase", "Debt Payoff", "Investment", "Business", "Retirement", "Other"]
            )
            # Check for prefilled amount from suggestions
            prefilled_amount = session.get('prefilled_goal_amount')
            default_amount = prefilled_amount if prefilled_amount else 100.0
            target_amount = st.number_input(
                "Target Amount ($)",
                min_value=100.0,
                step=100.0,
                format="%.2f",
                value=default_amount
            )
        
        with col2:
            # Check for prefilled date from suggestions
            prefilled_date = session.get('prefilled_goal_date')
            default_date = prefilled_date if prefilled_date else date.today() + timedelta(days=365)
            target_date = st.date_input("Target Date", value=default_date)
            description = st.text_area("Description (Optional)", placeholder="Describe your goal...")
        
        # Submit button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            create_goal = st.form_submit_button("🎯 Create Goal", type="primary", use_container_width=True)
        
        if create_goal:
            # Clear the prefilled goal, date, and amount after form submission
            if 'prefilled_goal' in session:
                del session['prefilled_goal']
            if 'prefilled_goal_date' in session:
                del session['prefilled_goal_date']
            if 'prefilled_goal_amount' in session:
                del session['prefilled_goal_amount']
            
            if goal_name and target_amount and target_date > date.today():
                goal_data = {
                    "name": goal_name,
                    "category": category,
                    "target_amount": target_amount,
                    "start_date": date.today().isoformat(),  # Set start date to today
                    "target_date": target_date.isoformat(),
                    "description": description,
                    "current_amount": 0.0
                }
                
                response = make_api_request("/goals", "POST", goal_data, token=token)
                
                if response:
                    st.success("🎉 Goal created successfully!")
                    
                    # Update streak for goal creation
                    try:
                        streak_response = make_api_request("/gamification/update-streak", "POST", {}, token=token)
                        if streak_response and streak_response.get('success'):
                            if streak_response.get('streak_bonus', 0) > 0:
                                st.info(f"🔥 Streak updated! Bonus points: {streak_response.get('streak_bonus', 0)}")
                    except Exception as e:
                        st.error(f"Error updating streak: {str(e)}")
                    
                    st.info("Redirecting to Ongoing Goals...")
                    time.sleep(1)
                    st.session_state[SESSION_STATE_KEY]['current_page'] = 'Ongoing Goals'
                    st.rerun()
                else:
                    st.error("❌ Failed to create goal. Please try again.")
            else:
                st.error("Please fill in all required fields and ensure target date is after start date.")
    
    st.markdown("---")
    
    # Goal suggestions
    session = st.session_state[SESSION_STATE_KEY]
    suggestions_visible = session.get('goal_suggestions_visible', True)
    
    # Toggle button for goal suggestions
    if not suggestions_visible:
        if st.button("💡 Show Goal Suggestions"):
            session['goal_suggestions_visible'] = True
            st.rerun()
    else:
        if st.button("💡 Hide Goal Suggestions"):
            session['goal_suggestions_visible'] = False
            st.rerun()
    
    # Display goal suggestions if visible
    if suggestions_visible:
        display_goal_suggestions(token)

def ongoing_goals_page():
    """Ongoing Goals page with table view of active goals"""
    st.markdown('<h1 class="main-header">Ongoing Goals</h1>', unsafe_allow_html=True)
    
    session = st.session_state[SESSION_STATE_KEY]
    token = session['access_token']
    
    # Get active goals
    goals_response = make_api_request("/goals/ongoing", token=token)
    goals = goals_response.get('goals', []) if goals_response else []
    active_goals = goals  # Already filtered to active goals
    
    if not active_goals:
        st.info("No active goals found. Create your first goal to get started!")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("➕ Create Your First Goal", type="primary", use_container_width=True):
                st.session_state[SESSION_STATE_KEY]['current_page'] = 'Create Goal'
                st.rerun()
        return
    
    # Goals table
    st.subheader(f"🪜 Active Goals ({len(active_goals)})")
    
    # Create table data
    table_data = []
    for goal in active_goals:
        progress_pct = (goal.get('current_amount', 0) / goal.get('target_amount', 1)) * 100
        progress_pct = min(100, progress_pct)
        
        # Calculate days remaining
        try:
            target_date = datetime.fromisoformat(goal['target_date']).date()
            days_remaining = (target_date - date.today()).days
        except:
            days_remaining = 0
        
        table_data.append({
            "Goal Name": goal['name'],
            "Category": goal['category'],
            "Target Amount": f"${goal.get('target_amount', 0):,.2f}",
            "Current Amount": f"${goal.get('current_amount', 0):,.2f}",
            "Progress": f"{progress_pct:.1f}%",
            "Days Remaining": days_remaining,
            "Last Updated": goal.get('updated_at', 'N/A')[:10] if goal.get('updated_at') else 'N/A'
        })
    
    # Display table using Streamlit columns for better alignment
    if active_goals:
        # Table header
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
        with col1:
            st.markdown("**Goal Name**")
        with col2:
            st.markdown("**Category**")
        with col3:
            st.markdown("**Target Amount**")
        with col4:
            st.markdown("**Current Amount**")
        with col5:
            st.markdown("**Progress**")
        with col6:
            st.markdown("**Days Remaining**")
        with col7:
            st.markdown("**Last Updated**")
        with col8:
            st.markdown("**Actions**")
        
        st.markdown("---")
        
        # Display each goal as a row
        for i, goal in enumerate(active_goals):
            # Get goal-specific account data
            try:
                account_response = make_api_request(f"/goals/{goal['id']}/account", token=token)
                account = account_response.get('account', {}) if account_response else {}
                current_amount = account.get('balance', 0)
            except:
                current_amount = goal.get('current_amount', 0)
            
            progress_pct = (current_amount / goal.get('target_amount', 1)) * 100 if goal.get('target_amount', 0) > 0 else 0
            progress_pct = min(100, progress_pct)
            
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
            
            with col1:
                st.write(f"📊 {goal['name']}")
            
            with col2:
                st.write(goal['category'])
            with col3:
                st.write(f"${goal.get('target_amount', 0):,.2f}")
            with col4:
                st.write(f"${current_amount:,.2f}")
            with col5:
                st.write(f"{progress_pct:.1f}%")
            with col6:
                try:
                    target_date = datetime.fromisoformat(goal['target_date']).date()
                    # Use last simulation date if available, otherwise use today
                    if goal.get('last_simulation_date'):
                        current_date = datetime.fromisoformat(goal['last_simulation_date']).date()
                    else:
                        current_date = date.today()
                    days_remaining = (target_date - current_date).days
                    st.write(days_remaining)
                except:
                    st.write("N/A")
            with col7:
                st.write(goal.get('updated_at', 'N/A')[:10] if goal.get('updated_at') else 'N/A')
            with col8:
                # Actions column with View and Delete buttons
                col8_1, col8_2 = st.columns(2)
                with col8_1:
                    if st.button("👁️", key=f"view_{i}", help="View goal details"):
                        st.session_state.selected_goal = goal
                        st.rerun()
                with col8_2:
                    if st.button("🗑️", key=f"delete_{i}", help="Delete goal"):
                        response = make_api_request(f"/goals/{goal['id']}", "DELETE", token=token)
                        if response:
                            st.success("Goal deleted!")
                            st.rerun()
        
        # If a goal was selected, show its dashboard
        if 'selected_goal' in st.session_state and st.session_state.selected_goal:
            st.markdown("---")
            st.subheader(f"📊 {st.session_state.selected_goal['name']} Dashboard")
            display_individual_goal_dashboard(st.session_state.selected_goal, token)

def completed_goals_page():
    """Completed Goals page with table view of completed goals"""
    st.markdown('<h1 class="main-header">Completed Goals</h1>', unsafe_allow_html=True)
    
    session = st.session_state[SESSION_STATE_KEY]
    token = session['access_token']
    
    # Get completed goals
    goals_response = make_api_request("/goals/completed", token=token)
    goals = goals_response.get('goals', []) if goals_response else []
    completed_goals = goals  # Already filtered to completed goals
    
    if not completed_goals:
        st.info("No completed goals yet. Keep working on your active goals!")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🪜 View Active Goals", type="primary", use_container_width=True):
                st.session_state[SESSION_STATE_KEY]['current_page'] = 'Ongoing Goals'
                st.rerun()
        return
    
    # Goals table
    st.subheader(f"🏆 Completed Goals ({len(completed_goals)})")
    
    # Create table data
    table_data = []
    for goal in completed_goals:
        final_amount = goal.get('current_amount', 0)
        target_amount = goal.get('target_amount', 0)
        
        # Calculate completion date and days early/late using same logic as Days Remaining metric
        try:
            target_date = datetime.fromisoformat(goal['target_date']).date()
            # Use last simulation date if available, otherwise use completion date
            if goal.get('last_simulation_date'):
                current_date = datetime.fromisoformat(goal['last_simulation_date']).date()
            else:
                current_date = datetime.fromisoformat(goal.get('completed_at', goal.get('updated_at', ''))).date()
            
            # Calculate days remaining (negative means early, positive means late)
            days_remaining = (target_date - current_date).days
            
            # For completed goals, negative days_remaining means early completion
            days_early = -days_remaining if days_remaining < 0 else 0
            completion_date = current_date
        except:
            days_early = 0
            completion_date = 'N/A'
        
        table_data.append({
            "Goal Name": goal['name'],
            "Category": goal['category'],
            "Target Amount": f"${target_amount:,.2f}",
            "Final Amount": f"${final_amount:,.2f}",
            "Completion Date": str(completion_date),
            "Days Early/Late": f"{days_early} days early" if days_early > 0 else f"{abs(days_remaining)} days late" if days_remaining > 0 else "On time"
        })
    
    # Display table using Streamlit columns for better alignment
    if completed_goals:
        # Table header
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        with col1:
            st.markdown("**Goal Name**")
        with col2:
            st.markdown("**Category**")
        with col3:
            st.markdown("**Target Amount**")
        with col4:
            st.markdown("**Final Amount**")
        with col5:
            st.markdown("**Completion Date**")
        with col6:
            st.markdown("**Days Early/Late**")
        with col7:
            st.markdown("**Actions**")
        
        st.markdown("---")
        
        # Display each goal as a row
        selected_goal = None
        for i, goal in enumerate(completed_goals):
            # Get goal-specific account data
            try:
                account_response = make_api_request(f"/goals/{goal['id']}/account", token=token)
                account = account_response.get('account', {}) if account_response else {}
                final_amount = account.get('balance', goal.get('current_amount', 0))
            except:
                final_amount = goal.get('current_amount', 0)
            
            col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
            
            with col1:
                st.write(f"🏆 {goal['name']}")
            
            with col2:
                st.write(goal['category'])
            with col3:
                st.write(f"${goal.get('target_amount', 0):,.2f}")
            with col4:
                st.write(f"${final_amount:,.2f}")
            with col5:
                try:
                    completion_date = goal.get('completed_at', goal.get('updated_at', ''))
                    if completion_date:
                        completion_date = datetime.fromisoformat(completion_date).date()
                        st.write(str(completion_date))
                    else:
                        st.write("N/A")
                except:
                    st.write("N/A")
            with col6:
                try:
                    target_date = datetime.fromisoformat(goal['target_date']).date()
                    completion_date = datetime.fromisoformat(goal.get('completed_at', goal.get('updated_at', ''))).date()
                    days_early = (target_date - completion_date).days
                    if days_early > 0:
                        st.write(f"{days_early} days early")
                    elif days_early < 0:
                        st.write(f"{abs(days_early)} days late")
                    else:
                        st.write("On time")
                except:
                    st.write("N/A")
            with col7:
                if st.button("👁️", key=f"view_{i}", help="View goal details"):
                    selected_goal = goal
        
        # If a goal was selected, show its completion dashboard
        if selected_goal:
            st.markdown("---")
            st.subheader(f"🏆 {selected_goal['name']} - Completion Dashboard")
            display_individual_goal_dashboard(selected_goal, token)

def display_individual_goal_dashboard(goal: dict, token: str):
    """Display individual goal dashboard with goal-specific simulation controls"""
    st.markdown(f"## 🎯 {goal['name']}")
    
    # Get goal-specific account data
    account_response = make_api_request(f"/goals/{goal['id']}/account", token=token)
    account = account_response.get('account', {}) if account_response else {}
    
    # If no account exists, create one
    if not account:
        try:
            create_response = make_api_request(f"/goals/{goal['id']}/account", "GET", {}, token=token)
            if create_response and create_response.get('account'):
                account = create_response.get('account', {})
        except:
            pass
    
    # Get current amount from account or fallback to goal
    current_amount = float(account.get('balance', 0)) if account else float(goal.get('current_amount', 0))
    target_amount = float(goal.get('target_amount', 0))
    
    # Calculate progress percentage
    if target_amount > 0:
        progress_pct = min(100, (current_amount / target_amount) * 100)
    else:
        progress_pct = 0
    
    # Display goal-specific progress bars
    st.markdown("#### 📊 Progress Visualization")
    
    # Goal Timeline progress bar
    try:
        start_date = datetime.fromisoformat(goal['start_date']).date()
        target_date = datetime.fromisoformat(goal['target_date']).date()
        
        # Use last simulation date if available, otherwise use today
        if goal.get('last_simulation_date'):
            current_date = datetime.fromisoformat(goal['last_simulation_date']).date()
        else:
            current_date = date.today()
        
        # Calculate timeline progress
        total_days = (target_date - start_date).days
        days_passed = (current_date - start_date).days
        timeline_progress = min(100, max(0, (days_passed / total_days) * 100)) if total_days > 0 else 0
        
        timeline_progress_html = f"""
        <div class="progress-bar-container">
            <div class="progress-bar-label">📅 GOAL TIMELINE</div>
            <div class="progress-bar-wrapper">
                <div class="progress-bar">
                    <div class="progress-fill timeline" style="width: {timeline_progress}%"></div>
                    <div class="progress-value" style="left: {timeline_progress}%">
                        {days_passed} days
                    </div>
                </div>
                <div class="progress-endpoints">
                    <div class="progress-endpoint start">
                        <strong>{start_date.strftime('%Y-%m-%d')}</strong><br>
                        START DATE
                    </div>
                    <div class="progress-endpoint middle">
                        <strong>{timeline_progress:.1f}%</strong><br>
                        {days_passed} days<br>
                        ELAPSED
                    </div>
                    <div class="progress-endpoint end">
                        <strong>{target_date.strftime('%Y-%m-%d')}</strong><br>
                        TARGET DATE
                    </div>
                </div>
            </div>
        </div>
        """
        st.markdown(timeline_progress_html, unsafe_allow_html=True)
    except:
        st.warning("Could not display timeline progress")
    
    # Amount progress bar
    amount_progress_html = f"""
    <div class="progress-bar-container">
        <div class="progress-bar-label">💰 GOAL AMOUNT</div>
        <div class="progress-bar-wrapper">
            <div class="progress-bar">
                <div class="progress-fill amount" style="width: {progress_pct}%"></div>
                <div class="progress-value" style="left: {progress_pct}%">
                    ${current_amount:,.0f}
                </div>
            </div>
            <div class="progress-endpoints">
                <div class="progress-endpoint start">
                    <strong>$0</strong><br>
                    START
                </div>
                <div class="progress-endpoint middle">
                    <strong>{progress_pct:.1f}%</strong><br>
                    ${current_amount:,.0f}<br>
                    ACHIEVED
                </div>
                <div class="progress-endpoint end">
                    <strong>${target_amount:,.0f}</strong><br>
                    TARGET
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(amount_progress_html, unsafe_allow_html=True)
    
    # Display goal metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Amount", f"${current_amount:,.2f}")
    with col2:
        st.metric("Target Amount", f"${target_amount:,.2f}")
    with col3:
        st.metric("Progress", f"{progress_pct:.1f}%")
    with col4:
        try:
            target_date = datetime.fromisoformat(goal['target_date']).date()
            # Use last simulation date if available, otherwise use today
            if goal.get('last_simulation_date'):
                current_date = datetime.fromisoformat(goal['last_simulation_date']).date()
            else:
                current_date = date.today()
            days_remaining = (target_date - current_date).days
            st.metric("Days Remaining", days_remaining)
        except:
            st.metric("Days Remaining", "N/A")
    
    # Personalized Advice Section - only show when conditions are met
    goal_status = goal.get('status', 'active')
    simulated_until = goal.get('last_simulation_date', goal.get('start_date', ''))
    start_date = goal.get('start_date', '')
    
    # Check conditions: current amount > 0, simulated until != start date, goal is active
    show_advice = (
        current_amount > 0 and 
        simulated_until != start_date and 
        goal_status != 'completed'
    )
    
    if show_advice:
        st.markdown("---")
        st.subheader("💡 Personalized Advice")
        st.markdown("*Tailored financial insights to help you reach your goals.*")
        
        # Part 1: Analyze and compare Goal Timeline vs Goal Amount progress
        timeline_progress_pct = timeline_progress if 'timeline_progress' in locals() else 0
        amount_progress_pct = progress_pct
        
        # Calculate the difference
        progress_difference = amount_progress_pct - timeline_progress_pct
        
        if progress_difference > 5:
            st.success(f"🎉 **Excellent progress!** You're ahead of your timeline by {progress_difference:.1f}%. Keep up the great work!")
        elif progress_difference > 0:
            st.info(f"✅ **Good job!** You're on track and slightly ahead by {progress_difference:.1f}%. You're doing well!")
        elif progress_difference > -5:
            st.warning(f"⚠️ **Slightly behind** by {abs(progress_difference):.1f}%. This is manageable - consider increasing your savings rate slightly.")
        else:
            st.error(f"🚨 **Behind schedule** by {abs(progress_difference):.1f}%. Consider reviewing your budget and increasing your monthly contributions.")
        
        # Part 2: LLM-generated personalized advice based on user profile and transactions
        try:
            with st.spinner("Generating personalized advice..."):
                # Get user's recent transactions for this goal
                transactions_response = make_api_request(f"/goals/{goal['id']}/transactions?limit=10", token=token)
                recent_transactions = transactions_response.get('transactions', []) if transactions_response else []
                
                # Get user's assessment data for context
                assessment_response = make_api_request("/assessment/current", token=token)
                assessment_data = assessment_response.get('assessment', {}) if assessment_response else {}
                
                # Prepare context for LLM
                advice_context = {
                    'goal_name': goal['name'],
                    'goal_category': goal['category'],
                    'current_amount': current_amount,
                    'target_amount': target_amount,
                    'progress_percentage': amount_progress_pct,
                    'timeline_progress': timeline_progress_pct,
                    'days_remaining': days_remaining if 'days_remaining' in locals() else 0,
                    'recent_transactions': recent_transactions[:5],  # Last 5 transactions
                    'user_risk_profile': assessment_data.get('risk_label', 'Balanced'),
                    'savings_rate': assessment_data.get('answers', {}).get('savings_rate', 10)
                }
                
                # Generate personalized advice using LLM
                advice_response = make_api_request("/goals/personalized-advice", "POST", advice_context, token=token)
                
                if advice_response and advice_response.get('advice'):
                    st.markdown("### 🎯 Smart Recommendations")
                    # Display advice with consistent font styling
                    st.markdown(f"""
                    <div style="font-family: 'Source Sans Pro', sans-serif; font-size: 16px; line-height: 1.5; color: #333;">
                        {advice_response['advice']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("💡 Complete your risk assessment to get personalized financial advice!")
                    
        except Exception as e:
            st.info("💡 Personalized advice will be available once you have some transaction history.")
    else:
        # Show message when conditions are not met
        if current_amount == 0:
            st.info("💡 Start simulating progress to get personalized advice!")
        elif simulated_until == start_date:
            st.info("💡 Simulate some progress to get personalized advice!")
        elif goal_status == 'completed':
            st.info("🎉 Congratulations! This goal is completed.")
    
    # Goal-specific simulation controls - only show for ongoing goals
    if goal_status != 'completed':
        st.markdown("---")
        st.subheader("🔄 Goal-Specific Simulation")
    
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            # Show the last simulation date or goal start date
            if goal.get('last_simulation_date'):
                simulated_until = goal.get('last_simulation_date')
            else:
                simulated_until = goal.get('start_date', 'Not simulated')
            st.metric("Simulated Until", simulated_until)
        
        with col2:
            months_to_simulate = st.selectbox(
                "Months to simulate",
                [1, 3, 6, 12],
                index=0,
                key=f"months_{goal['id']}",
                help="Select how many months of mock data to generate for this goal"
            )
        
        with col3:
            st.markdown('<div class="button-align">', unsafe_allow_html=True)
            if st.button(f"🔄 Simulate Progress", key=f"simulate_{goal['id']}", type="primary", use_container_width=True):
                with st.spinner(f"Generating mock transactions for {goal['name']}..."):
                    try:
                        # Simulate progress for this specific goal
                        simulate_response = make_api_request(f"/goals/{goal['id']}/simulate", "POST", {
                            "months_to_simulate": months_to_simulate
                        }, token=token)
                        
                        if simulate_response and simulate_response.get('success'):
                            transactions_generated = simulate_response.get('transactions_generated', 0)
                            months_simulated = simulate_response.get('months_simulated', 0)
                            progress_until = simulate_response.get('progress_until', 'Unknown')
                            current_balance = simulate_response.get('current_balance', 0)
                            is_completed = simulate_response.get('is_completed', False)
                            goal_status = simulate_response.get('goal_status', 'active')
                            
                            st.success(f"✅ Generated {transactions_generated} transactions for {months_simulated} month(s)!")
                            st.info(f"📅 Progress tracked until: {progress_until}")
                            st.info(f"💰 Current balance: ${current_balance:,.2f}")
                            
                            # Check if goal is completed
                            if is_completed:
                                st.balloons()
                                st.success("🎉 Congratulations! You've completed your goal! 🎊")
                                
                                # Check for milestones
                                try:
                                    milestone_response = make_api_request("/gamification/check-milestones", "POST", {
                                        "goal_amount": current_balance
                                    }, token=token)
                                    if milestone_response and milestone_response.get('success'):
                                        new_milestones = milestone_response.get('new_milestones', [])
                                        if new_milestones:
                                            st.success("🏆 New Milestone Achieved!")
                                            for milestone in new_milestones:
                                                st.info(f"🎉 {milestone['level']} - {milestone['points']} points earned!")
                                except Exception as e:
                                    st.error(f"Error checking milestones: {str(e)}")
                                
                                # Update the selected goal in session state with new data
                                if 'selected_goal' in st.session_state:
                                    st.session_state.selected_goal['current_amount'] = current_balance
                                    st.session_state.selected_goal['status'] = goal_status
                                    st.session_state.selected_goal['last_simulation_date'] = progress_until
                                
                                # Clear selected goal and navigate to Completed Goals page
                                if 'selected_goal' in st.session_state:
                                    del st.session_state.selected_goal
                                
                                # Navigate to Completed Goals page
                                time.sleep(2)
                                st.session_state[SESSION_STATE_KEY]['current_page'] = "Completed Goals"
                                st.rerun()
                            else:
                                # Update the selected goal in session state with new data
                                if 'selected_goal' in st.session_state:
                                    st.session_state.selected_goal['current_amount'] = current_balance
                                    st.session_state.selected_goal['last_simulation_date'] = progress_until
                                
                                # Update streak for progress simulation
                                try:
                                    streak_response = make_api_request("/gamification/update-streak", "POST", {}, token=token)
                                    if streak_response and streak_response.get('success'):
                                        if streak_response.get('streak_bonus', 0) > 0:
                                            st.info(f"🔥 Progress updated! Streak bonus: {streak_response.get('streak_bonus', 0)} points")
                                except Exception as e:
                                    st.error(f"Error updating streak: {str(e)}")
                                
                                # Refresh the page to show updated data
                                time.sleep(1)
                                st.rerun()
                        else:
                            error_msg = simulate_response.get('error', 'Unknown error') if simulate_response else 'Failed to connect to API'
                            st.error(f"❌ Failed to simulate progress: {error_msg}")
                    except Exception as e:
                        st.error(f"❌ Error simulating progress: {str(e)}")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Show recent transactions for this goal
    try:
        # Force refresh transactions by adding a timestamp parameter
        transactions_response = make_api_request(f"/goals/{goal['id']}/transactions?t={int(time.time())}", token=token)
        transactions = transactions_response.get('transactions', []) if transactions_response else []
        
        if transactions:
            st.markdown("---")
            st.subheader("📈 Recent Transactions")
            
            # Show last 10 transactions (already ordered by newest first from backend)
            recent_transactions = transactions[:10] if len(transactions) > 10 else transactions
            
            for transaction in recent_transactions:
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"**{transaction.get('description', 'Transaction')}**")
                with col2:
                    amount = transaction.get('amount', 0)
                    if transaction.get('transaction_type') == 'income':
                        st.write(f"💰 +${amount:,.2f}")
                    else:
                        st.write(f"💸 -${amount:,.2f}")
                with col3:
                    st.write(transaction.get('category', 'N/A'))
                with col4:
                    st.write(transaction.get('date', 'N/A')[:10])
    except:
        st.info("No transactions available for this goal yet.")
    
    # Back button
    st.markdown("---")
    if st.button("← Back to Goals List", key=f"back_{goal['id']}"):
        if 'selected_goal' in st.session_state:
            del st.session_state.selected_goal
        st.rerun()

if __name__ == "__main__":
    main()
