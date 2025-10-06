# Quick Start Guide - Risk Assessment & Goal Tracking App

## 🚀 Get Started in 5 Minutes

### Step 1: Prerequisites
Make sure you have:
- Docker and Docker Compose installed
- Ollama installed (for LLM features)

### Step 2: Install Ollama
```bash
# Download and install Ollama from https://ollama.ai/download
# Then pull the required model
ollama pull gpt-oss:20b
```

### Step 3: Deploy the Application
```bash
# Clone the repository
git clone <your-repo-url>
cd risk_agent

# Run the deployment script
./deploy.sh
```

### Step 4: Access the Application
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:5000
- **Database**: localhost:5432

### Step 5: Test the Application
1. Open http://localhost:8501 in your browser
2. Click "Register" and create a new account
3. Complete the risk assessment questionnaire
4. Create your first financial goal
5. Click "Update Progress" to see the smart simulation in action
6. View personalized recommendations

## 🎯 Key Features to Try

### Risk Assessment
- Complete the 12-question financial risk assessment
- Get your personalized risk profile (Conservative, Balanced, Aggressive)
- See detailed scoring and explanations

### Goal Management
- Create goals in different categories (Emergency Fund, Retirement, etc.)
- Set target amounts and dates
- Track progress with visual indicators

### Smart Progress Tracking
- Click "Update Progress" to simulate realistic financial activity
- See account balances change over time
- Get pacing analysis (on track, ahead, behind)

### LLM Recommendations
- Receive personalized financial advice
- Get goal-specific recommendations
- Ask questions about financial terms

## 🔧 Management Commands

```bash
# View all service logs
docker-compose logs -f

# Stop all services
docker-compose down

# Restart services
docker-compose restart

# Update and restart
docker-compose up --build -d

# Check service status
docker-compose ps
```

## 🐛 Quick Troubleshooting

**Application not loading?**
```bash
# Check if all services are running
docker-compose ps

# Check logs for errors
docker-compose logs
```

**Ollama not working?**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

**Database issues?**
```bash
# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

## 📊 Sample Data

The application comes with sample data for testing:
- Test user: test@example.com / password123
- Mock financial accounts and transactions
- Sample goals and progress data

## 🎉 You're Ready!

Your Risk Assessment & Goal Tracking application is now running! Explore the features, create goals, and experience the smart financial simulation system.

For detailed documentation, see the main README.md file.
