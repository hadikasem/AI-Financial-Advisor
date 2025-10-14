# LLM Service Configuration Guide

## Overview

The LLM service now supports both OpenAI and Ollama providers, with OpenAI as the default and Ollama as a fallback option. You can easily switch between providers or let the system automatically choose the best available option.

## Configuration

### Environment Variables

Add these variables to your `.env` file:

```bash
# LLM Provider Configuration
# Set to 'openai' to use OpenAI as default, 'ollama' to use Ollama as default
DEFAULT_LLM_PROVIDER=openai

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Ollama Configuration (fallback)
OLLAMA_MODEL=gpt-oss:20b
OLLAMA_HOST=http://localhost:11434
```

### Provider Selection Logic

1. **Primary Provider**: Uses the provider specified in `DEFAULT_LLM_PROVIDER`
2. **Fallback**: If the primary provider fails, automatically tries the other provider
3. **Availability Check**: Both providers are tested for availability on startup

## Usage

### API Endpoints

#### Test LLM Service
```bash
POST /api/test/llm
{
  "question": "What is compound interest?"
}
```

#### Get Provider Status
```bash
GET /api/llm/debug
```

#### Switch Provider (requires restart)
```bash
POST /api/llm/provider
{
  "provider": "openai"  # or "ollama"
}
```

#### Get Help Response
```bash
POST /api/llm/help
{
  "question": "How should I invest my money?",
  "context": "I'm 25 years old and have $10,000 to invest"
}
```

### Programmatic Usage

```python
from services.llm_service import LLMService

# Initialize service
llm_service = LLMService()

# Get provider status
status = llm_service.get_provider_status()
print(f"Current provider: {status['current_provider']}")

# Get help response
answer = llm_service.get_help_response("What is a Roth IRA?")

# Generate goal suggestions
suggestions = llm_service.generate_goal_suggestions("user_id", "Balanced")

# Get recommendations
recommendations = llm_service.get_recommendations("user_id", "goal_id")
```

## Provider-Specific Features

### OpenAI
- **Models**: gpt-3.5-turbo, gpt-4, gpt-4-turbo
- **Advantages**: Fast, reliable, high-quality responses
- **Requirements**: Valid OpenAI API key

### Ollama
- **Models**: Any locally installed Ollama model
- **Advantages**: Free, runs locally, privacy-focused
- **Requirements**: Ollama installed and running locally

## Troubleshooting

### OpenAI Issues
- Verify your API key is correct and has sufficient credits
- Check if the model name is valid
- Ensure you have internet connectivity

### Ollama Issues
- Make sure Ollama is installed and running
- Verify the host URL is correct (default: http://localhost:11434)
- Check if the specified model is installed (`ollama list`)

### Fallback Behavior
- If OpenAI fails, the service automatically tries Ollama
- If Ollama fails, the service automatically tries OpenAI
- If both fail, fallback responses are provided

## Testing

Run the test script to verify your configuration:

```bash
python test_llm_service.py
```

This will test both providers and show you the current status.
