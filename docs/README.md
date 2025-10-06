# Risk Assessment Agent

A comprehensive financial risk assessment and goal tracking system built with Python.

## Overview

The Risk Assessment Agent is a modular system that helps users:
- Complete personalized financial risk assessments
- Set and track progress toward financial goals
- Receive AI-powered recommendations
- Monitor their financial progress over time

## Features

### Risk Assessment
- **12-question assessment** covering age, time horizon, income stability, and more
- **Intelligent validation** with support for natural language input
- **Dynamic scoring** that adapts to user responses
- **Risk profile classification** (Conservative to Aggressive)
- **Interactive clarifications** for financial terms

### Goal Tracking
- **Goal validation** ensuring complete target amounts and dates
- **Progress calculation** with pacing analysis
- **Multiple goal support** from risk assessment results
- **AI-powered recommendations** based on progress
- **Data persistence** with JSON storage

### Technical Features
- **Modular architecture** with clear separation of concerns
- **LLM integration** using Ollama for recommendations
- **Mock data support** for development and testing
- **Comprehensive testing** with unit and integration tests
- **CLI interfaces** for both assessment and tracking

## Quick Start

### Prerequisites
- Python 3.10+
- Ollama (for LLM features)

### Installation
1. Clone the repository
2. Install dependencies (if any)
3. Start Ollama service: `ollama serve`

### Running the Application

#### Risk Assessment
```bash
python main.py assessment
```

#### Goal Tracking
```bash
# Single goal tracking
python main.py tracking --single --user-id u123 --data-root ./data

# Multiple goals from assessment
python main.py tracking --multi --user-id u123 --assessment-file user_data.json --data-root ./data
```

## Architecture

### Directory Structure
```
risk_agent/
├── src/                          # Main source code
│   ├── core/                     # Core business logic
│   │   ├── assessment.py         # Risk assessment logic
│   │   ├── validation.py         # Input validation
│   │   └── scoring.py            # Scoring algorithms
│   ├── data/                     # Data layer
│   │   ├── models.py             # Data models
│   │   └── sources.py            # Data sources
│   ├── services/                 # Service layer
│   │   ├── progress.py           # Progress calculations
│   │   ├── llm.py                # LLM integration
│   │   └── goal_validation.py    # Goal validation
│   └── cli/                      # CLI interfaces
│       ├── assessment_cli.py     # Risk assessment CLI
│       └── tracking_cli.py       # Goal tracking CLI
├── tests/                        # Test suite
├── data/                         # Data storage
│   ├── users/                    # User data
│   └── mock/                     # Mock data
├── docs/                         # Documentation
└── main.py                       # Main entry point
```

### Key Components

#### Core Layer (`src/core/`)
- **assessment.py**: Main risk assessment agent
- **validation.py**: Input validation and parsing
- **scoring.py**: Risk scoring algorithms

#### Data Layer (`src/data/`)
- **models.py**: Data structures and protocols
- **sources.py**: Data source implementations

#### Services Layer (`src/services/`)
- **progress.py**: Progress calculation engine
- **llm.py**: LLM integration and recommendations
- **goal_validation.py**: Goal validation system

#### CLI Layer (`src/cli/`)
- **assessment_cli.py**: Interactive risk assessment
- **tracking_cli.py**: Goal tracking interface

## Usage Examples

### Risk Assessment Flow
1. Start assessment: `python main.py assessment`
2. Answer questions about your financial situation
3. Ask for clarifications on any terms
4. Review your risk profile
5. Select financial goals
6. Complete and save your assessment

### Goal Tracking Flow
1. Set up mock data or use real data
2. Run tracking: `python main.py tracking --single --user-id u123`
3. View progress dashboard
4. Review AI recommendations
5. Track progress over time

## Data Format

### Assessment Data
```json
{
  "user_id": "user_abc12345",
  "session_id": "session_def67890",
  "assessment_data": {
    "risk_profile": {
      "score_percentage": 65.5,
      "label": "Balanced"
    },
    "answers": { /* user responses */ },
    "individual_scores": { /* per-question scores */ }
  },
  "goals": {
    "selected_goals": [ /* active goals */ ],
    "deleted_goals": [ /* deleted goals */ ]
  }
}
```

### Progress Data
```json
{
  "user_id": "user_abc12345",
  "as_of": "2025-01-15T10:30:00Z",
  "current_amount": 4500.00,
  "progress_pct": 45.0,
  "pacing_status": "on_track",
  "target_amount": 10000.0,
  "target_date": "2026-12-31"
}
```

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

Or run individual test modules:
```bash
python tests/test_assessment.py
python tests/test_goal_validation.py
```

## Development

### Adding New Questions
1. Add question to `_initialize_questions()` in `assessment.py`
2. Add validation function to `validation.py`
3. Add scoring function to `scoring.py`
4. Update tests

### Adding New Data Sources
1. Implement `FinancialDataSource` protocol
2. Add to `sources.py`
3. Update CLI to use new source

### Adding New Services
1. Create service module in `src/services/`
2. Add to CLI interfaces as needed
3. Write tests

## Contributing

1. Follow the modular architecture
2. Write tests for new features
3. Update documentation
4. Ensure code quality with linting

## License

[Add your license information here]

## Support

[Add support information here]
