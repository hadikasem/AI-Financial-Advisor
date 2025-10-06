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
            'notifications': []
        }

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
            phone = st.text_input("Phone Number")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Register")
            
            if submit:
                if all([full_name, username, email, phone, password, confirm_password]):
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

def assessment_page():
    """Risk assessment questionnaire page"""
    st.markdown('<h1 class="main-header">Risk Assessment</h1>', unsafe_allow_html=True)
    
    session = st.session_state[SESSION_STATE_KEY]
    token = session['access_token']
    
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
        
        st.subheader(f"Question {len(assessment.get('answers', {})) + 1}")
        st.write(question['question'])
        
        # Handle different question types
        if question['type'] == 'number':
            validation = question.get('validation', {})
            min_val = float(validation.get('min', 0))
            max_val = float(validation.get('max', 1000))
            step_val = 1.0 if question['id'] in ['age', 'horizon', 'dependents'] else 0.1
            
            answer = st.number_input(
                "Your answer:",
                min_value=min_val,
                max_value=max_val,
                step=step_val
            )
        elif question['type'] == 'multiple_choice':
            answer = st.selectbox("Your answer:", question['options'])
        else:
            answer = st.text_input("Your answer:")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Submit Answer"):
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
                                st.success("Assessment completed!")
                                st.session_state[SESSION_STATE_KEY]['assessment_completed'] = complete_response
                                st.rerun()
                        else:
                            # Update current assessment
                            st.session_state[SESSION_STATE_KEY]['current_assessment'] = response
                            st.rerun()
                else:
                    st.error("Please provide an answer.")
        
        with col2:
            if st.button("Get Help"):
                st.info("You can ask questions about any financial terms or concepts. The LLM will help explain them to you.")
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
        with st.form("create_goal_form"):
            col1, col2 = st.columns(2)
            with col1:
                goal_name = st.text_input("Goal Name")
                goal_category = st.selectbox("Category", categories)
                target_amount = st.number_input("Target Amount ($)", min_value=0.0, step=100.0)
            with col2:
                target_date = st.date_input("Target Date", min_value=date.today())
                start_amount = st.number_input("Starting Amount ($)", min_value=0.0, step=100.0)
                description = st.text_area("Description (Optional)")
            
            if st.form_submit_button("Create Goal"):
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
                        st.rerun()
                else:
                    st.error("Please fill in all required fields.")
    
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
            st.write(f"Welcome, {session['user']['full_name']}!")
            
            # Check if user has completed assessment
            assessment_completed = session.get('assessment_completed')
            
            if not assessment_completed:
                st.warning("⚠️ Please complete your risk assessment first!")
                page = "Assessment"
            else:
                page = st.selectbox(
                    "Navigate to:",
                    ["Dashboard", "Goals", "Assessment", "Notifications"]
                )
            
            if st.button("Logout"):
                st.session_state[SESSION_STATE_KEY] = {
                    'authenticated': False,
                    'user': None,
                    'access_token': None,
                    'current_assessment': None,
                    'current_goals': [],
                    'notifications': []
                }
                st.rerun()
        
        # Route to appropriate page
        if page == "Dashboard":
            dashboard_page()
        elif page == "Goals":
            goals_page()
        elif page == "Assessment":
            assessment_page()
        elif page == "Notifications":
            notifications_page()

if __name__ == "__main__":
    main()
