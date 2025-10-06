# Risk Assessment & Goal Tracking Full-Stack Application

A comprehensive full-stack web application for financial risk assessment and goal tracking, built with Flask backend, Streamlit frontend, PostgreSQL database, and integrated with Ollama LLM for personalized recommendations.

## 🚀 Features

### Core Functionality
- **User Authentication**: Secure registration and login with JWT tokens
- **Risk Assessment**: Comprehensive 12-question financial risk assessment
- **Goal Management**: Create, track, and manage multiple financial goals
- **Progress Tracking**: Smart time-based simulation with realistic financial data
- **LLM Integration**: Personalized recommendations using Ollama
- **Notifications**: Email, in-app, and push notifications for milestones

### Advanced Features
- **Smart Data Simulation**: Realistic financial transactions and account updates
- **Progress Visualization**: Interactive charts and progress bars
- **Goal Categories**: Predefined categories (Emergency Fund, Retirement, etc.)
- **Real-time Updates**: On-demand progress updates with time-based simulation
- **Responsive Design**: Modern, user-friendly interface
- **Docker Support**: Complete containerization for easy deployment

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   Flask API     │    │   PostgreSQL    │
│   Frontend      │◄──►│   Backend       │◄──►│   Database      │
│   (Port 8501)   │    │   (Port 5000)   │    │   (Port 5432)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Ollama LLM    │
                       │   (Port 11434)  │
                       └─────────────────┘
```

## 📁 Project Structure

```
risk_agent/
├── backend/                 # Flask API Backend
│   ├── app.py              # Main Flask application
│   ├── models.py           # Database models
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile         # Backend container
│   └── services/          # Business logic services
│       ├── assessment_service.py
│       ├── goal_service.py
│       ├── progress_service.py
│       ├── llm_service.py
│       └── notification_service.py
├── frontend/               # Streamlit Frontend
│   ├── app.py             # Main Streamlit application
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile         # Frontend container
├── database/              # Database configuration
│   └── init.sql          # Database initialization
├── aws/                   # AWS deployment
│   └── terraform/        # Infrastructure as Code
│       └── main.tf       # Terraform configuration
├── scripts/               # Utility scripts
│   └── migrate_data.py   # Data migration script
├── docker-compose.yml     # Docker orchestration
├── deploy.sh             # Deployment script
└── README.md             # This file
```

## 🛠️ Installation & Setup

### Prerequisites
- Docker and Docker Compose
- Ollama (for LLM functionality)
- Python 3.11+ (for local development)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd risk_agent
   ```

2. **Run the deployment script**
   ```bash
   ./deploy.sh
   ```

   This will:
   - Check Docker and Ollama installation
   - Set up environment files
   - Build and start all services
   - Run database migrations
   - Display service URLs

3. **Access the application**
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:5000
   - Database: localhost:5432

### Manual Setup

1. **Start Ollama**
   ```bash
   ollama serve
   ollama pull gpt-oss:20b
   ```

2. **Set up environment files**
   ```bash
   cp backend/env_example.txt backend/.env
   # Edit backend/.env with your configuration
   ```

3. **Start services with Docker Compose**
   ```bash
   docker-compose up --build -d
   ```

4. **Run database migrations**
   ```bash
   python3 scripts/migrate_data.py
   ```

## 🔧 Configuration

### Environment Variables

**Backend (.env)**
```env
SECRET_KEY=your-super-secret-key
JWT_SECRET_KEY=jwt-secret-key
DATABASE_URL=postgresql://user:pass@localhost:5432/risk_agent_db
SENDGRID_API_KEY=your-sendgrid-api-key
OLLAMA_MODEL=gpt-oss:20b
```

**Frontend (.env)**
```env
API_BASE_URL=http://localhost:5000/api
```

### Database Configuration

The application uses PostgreSQL with the following main tables:
- `users`: User accounts and authentication
- `assessments`: Risk assessment data and scores
- `goals`: Financial goals and targets
- `accounts`: Financial accounts and balances
- `transactions`: Transaction history
- `progress_snapshots`: Progress tracking data
- `notifications`: User notifications

## 🚀 Deployment

### Local Development
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### AWS Deployment

1. **Set up AWS credentials**
   ```bash
   aws configure
   ```

2. **Deploy infrastructure**
   ```bash
   cd aws/terraform
   terraform init
   terraform plan
   terraform apply
   ```

3. **Update application configuration**
   - Update database URL to RDS endpoint
   - Configure domain and SSL certificates
   - Set up SendGrid for email notifications

## 📊 Usage Guide

### User Flow
1. **Registration**: Create account with email, password, and personal info
2. **Risk Assessment**: Complete 12-question financial risk assessment
3. **Goal Setting**: Create financial goals with categories and targets
4. **Progress Tracking**: Update progress and view recommendations
5. **Dashboard**: Monitor progress with charts and notifications

### API Endpoints

**Authentication**
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login

**Assessment**
- `POST /api/assessment/start` - Start risk assessment
- `POST /api/assessment/answer` - Submit answer
- `POST /api/assessment/complete` - Complete assessment

**Goals**
- `GET /api/goals` - Get user goals
- `POST /api/goals` - Create new goal
- `DELETE /api/goals/{id}` - Delete goal

**Progress**
- `POST /api/progress/update` - Update progress
- `GET /api/progress/{goal_id}` - Get goal progress

**Recommendations**
- `GET /api/recommendations` - Get personalized recommendations

## 🔍 Smart Data Simulation

The application features a sophisticated time-based data simulation system:

- **Realistic Patterns**: Salary deposits, rent payments, daily expenses
- **Time-Based Updates**: Progress updates based on elapsed time
- **Account Management**: Automatic balance updates and transactions
- **Goal Tracking**: Progress calculation with pacing analysis

## 🤖 LLM Integration

### Ollama Integration
- Uses `gpt-oss:20b` model for recommendations
- Generates personalized financial advice
- Provides goal suggestions based on risk profile
- Explains financial terms and concepts

### Recommendation Types
- Investment suggestions based on risk profile
- Spending optimization tips
- General financial advice
- Goal-specific recommendations

## 📱 Notifications

### Notification Types
- **Milestone Notifications**: 25%, 50%, 75%, 100% progress
- **Deadline Reminders**: Goal deadline alerts
- **Weekly Updates**: Progress summaries
- **Recommendations**: Personalized advice

### Delivery Methods
- **Email**: SendGrid integration
- **In-App**: Real-time notifications
- **Push**: Firebase Cloud Messaging (planned)

## 🧪 Testing

### Test Data
The application includes comprehensive test data:
- Sample users with realistic profiles
- Mock financial accounts and transactions
- Pre-configured goals and assessments

### Testing Commands
```bash
# Run backend tests
cd backend
python -m pytest

# Test API endpoints
curl http://localhost:5000/api/health

# Test frontend
# Open http://localhost:8501 and test user flows
```

## 🔒 Security

### Authentication
- JWT token-based authentication
- Password hashing with bcrypt
- Session management

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- CORS configuration
- Environment variable protection

## 📈 Performance

### Optimization Features
- Database indexing for fast queries
- Connection pooling
- Caching strategies
- Efficient data structures

### Monitoring
- Health check endpoints
- Logging and error tracking
- Performance metrics
- Resource monitoring

## 🛠️ Development

### Adding New Features
1. Update database models in `backend/models.py`
2. Add API endpoints in `backend/app.py`
3. Implement business logic in services
4. Update frontend in `frontend/app.py`
5. Add tests and documentation

### Code Structure
- **Backend**: Flask with SQLAlchemy ORM
- **Frontend**: Streamlit with Plotly charts
- **Database**: PostgreSQL with proper indexing
- **Services**: Modular business logic

## 📝 API Documentation

### Authentication Flow
```python
# Register user
POST /api/auth/register
{
    "email": "user@example.com",
    "password": "password123",
    "full_name": "John Doe",
    "username": "johndoe",
    "phone": "+1234567890"
}

# Login
POST /api/auth/login
{
    "email": "user@example.com",
    "password": "password123"
}
```

### Assessment Flow
```python
# Start assessment
POST /api/assessment/start
# Returns: assessment_id and first question

# Answer question
POST /api/assessment/answer
{
    "question_id": "age",
    "answer": "30"
}

# Complete assessment
POST /api/assessment/complete
# Returns: risk score and profile
```

## 🐛 Troubleshooting

### Common Issues

**Ollama not responding**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

**Database connection issues**
```bash
# Check database status
docker-compose logs db

# Restart database
docker-compose restart db
```

**Frontend not loading**
```bash
# Check frontend logs
docker-compose logs frontend

# Restart frontend
docker-compose restart frontend
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

## 🎯 Roadmap

### Phase 2 Features
- Social login integration (Google, Facebook)
- Advanced charting and analytics
- Mobile app development
- Real bank API integration
- Advanced notification system
- Multi-language support

### Future Enhancements
- Machine learning for better recommendations
- Advanced portfolio management
- Tax optimization features
- Retirement planning tools
- Investment tracking
- Financial education content

---

**Built with ❤️ for better financial planning and goal achievement.**
