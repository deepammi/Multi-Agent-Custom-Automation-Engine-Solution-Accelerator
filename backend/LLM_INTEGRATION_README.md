# LLM Integration for Invoice Agent

## Overview

The Invoice Agent now supports real AI model API calls through a flexible, provider-agnostic LLM service. You can use OpenAI, Anthropic, or local Ollama models, with a mock mode for cost-free testing.

## Features

✅ **Multiple LLM Providers**: OpenAI, Anthropic, Ollama
✅ **Mock Mode**: Cost-free testing with hardcoded responses
✅ **Streaming Responses**: Real-time token-by-token delivery via WebSocket
✅ **Error Handling**: Comprehensive error classification and retry logic
✅ **Logging**: Detailed logging with API key sanitization
✅ **Timeout Management**: Configurable timeouts with graceful handling
✅ **Retry Logic**: Automatic retry with exponential backoff for rate limits

## Quick Start

### 1. Configure Environment

Edit `backend/.env`:

```bash
# For testing without API costs (default)
USE_MOCK_LLM=true

# For real AI responses
USE_MOCK_LLM=false
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

### 2. Start the Server

```bash
cd backend
python -m uvicorn app.main:app --reload
```

### 3. Test

Submit an invoice-related task through the frontend and watch the AI respond in real-time!

## Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `USE_MOCK_LLM` | Enable mock mode (true/false) | `false` | No |
| `LLM_PROVIDER` | Provider name (openai/anthropic/ollama) | `openai` | Yes |
| `LLM_TIMEOUT` | Request timeout in seconds | `60` | No |
| `LLM_MAX_RETRIES` | Max retry attempts for rate limits | `2` | No |
| `LLM_TEMPERATURE` | Sampling temperature (0.0-2.0) | `0.7` | No |

### OpenAI Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `OPENAI_MODEL` | Model name | `gpt-4o` |

Supported models:
- `gpt-4o` - Latest GPT-4 Omni (recommended)
- `gpt-4o-mini` - Faster and cheaper
- `gpt-4-turbo` - Previous generation
- `gpt-3.5-turbo` - Cheapest option

### Anthropic Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | Required |
| `ANTHROPIC_MODEL` | Model name | `claude-3-5-sonnet-20241022` |

Supported models:
- `claude-3-5-sonnet-20241022` - Latest Claude (recommended)
- `claude-3-opus-20240229` - Most capable
- `claude-3-sonnet-20240229` - Balanced
- `claude-3-haiku-20240307` - Fastest and cheapest

### Ollama Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Model name | `llama3` |

Requires:
1. Ollama installed locally
2. `langchain-ollama` package: `pip install langchain-ollama`
3. Model pulled: `ollama pull llama3`

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                    Invoice Agent Node                    │
│  (backend/app/agents/nodes.py)                          │
│                                                          │
│  - Checks mock mode                                     │
│  - Builds prompt from template                          │
│  - Calls LLM service                                    │
│  - Returns AI response                                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                     LLM Service                          │
│  (backend/app/services/llm_service.py)                  │
│                                                          │
│  - Provider configuration                               │
│  - Mock mode detection                                  │
│  - Streaming with WebSocket                             │
│  - Error handling & retry logic                         │
│  - Logging with API key sanitization                    │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
    ┌────────┐  ┌────────┐  ┌────────┐
    │OpenAI  │  │Anthropic│ │Ollama  │
    │  API   │  │   API   │  │ Local  │
    └────────┘  └────────┘  └────────┘
```

### Prompt Templates

Located in `backend/app/agents/prompts.py`:

- `INVOICE_AGENT_PROMPT` - Invoice analysis template
- `CLOSING_AGENT_PROMPT` - Closing process template
- `AUDIT_AGENT_PROMPT` - Audit review template

Each template includes:
- Agent role and expertise
- Task description placeholder
- Output format instructions
- Guidelines for handling missing data

### Error Handling

The LLM service classifies errors into categories:

1. **LLMTimeoutError**: Request exceeded timeout
2. **LLMAuthError**: Invalid API key or authentication failure
3. **LLMRateLimitError**: Rate limit exceeded (triggers retry)
4. **LLMNetworkError**: Connection or network issues
5. **LLMError**: Generic LLM errors

Rate limit errors trigger automatic retry with exponential backoff (2s, 4s).

### Logging

All LLM interactions are logged with:
- Plan ID for traceability
- Agent name
- Request duration
- Response length
- Error details (if any)

**Security**: API keys are automatically sanitized from logs using regex patterns.

## Usage Examples

### Basic Usage (Mock Mode)

```python
from app.services.llm_service import LLMService

# Check if mock mode is enabled
if LLMService.is_mock_mode():
    response = LLMService.get_mock_response("Invoice", "Check invoice #123")
    print(response)
```

### Real API Call with Streaming

```python
from app.services.llm_service import LLMService
from app.agents.prompts import build_invoice_prompt

# Build prompt
task = "Verify invoice #12345 from Acme Corp for $5,000"
prompt = build_invoice_prompt(task)

# Call LLM with streaming
response = await LLMService.call_llm_streaming(
    prompt=prompt,
    plan_id="plan-123",
    websocket_manager=websocket_manager,
    agent_name="Invoice"
)
```

### Provider Configuration

```python
import os
from app.services.llm_service import LLMService

# Configure OpenAI
os.environ["LLM_PROVIDER"] = "openai"
os.environ["OPENAI_API_KEY"] = "sk-..."
os.environ["OPENAI_MODEL"] = "gpt-4o-mini"

# Reset to pick up new config
LLMService.reset()

# Get LLM instance
llm = LLMService.get_llm_instance()
```

## Testing

### Run Test Suite

```bash
cd backend
python test_llm_integration.py
```

Tests:
- ✅ Mock mode functionality
- ✅ Prompt building and validation
- ✅ Provider configuration
- ✅ Real API calls (if keys configured)

### Quick OpenAI Test

```bash
cd backend
export OPENAI_API_KEY=sk-your-key
python test_openai_quick.py
```

### Manual Testing

See `TESTING_GUIDE.md` for detailed manual testing instructions.

## Extending to Other Agents

The LLM integration is designed to be reusable. To add LLM support to other agents:

### 1. Create Prompt Template

In `backend/app/agents/prompts.py`:

```python
CLOSING_AGENT_PROMPT = """You are an expert Closing Agent...

Task: {task_description}

Please analyze..."""

def build_closing_prompt(task_description: str) -> str:
    return CLOSING_AGENT_PROMPT.format(task_description=task_description)
```

### 2. Update Agent Node

In `backend/app/agents/nodes.py`:

```python
from app.services.llm_service import LLMService
from app.agents.prompts import build_closing_prompt

async def closing_agent_node(state: AgentState) -> Dict[str, Any]:
    task = state["task_description"]
    plan_id = state["plan_id"]
    websocket_manager = state.get("websocket_manager")
    
    # Check mock mode
    if LLMService.is_mock_mode():
        response = LLMService.get_mock_response("Closing", task)
        return {"messages": [response], "final_result": response}
    
    # Build prompt and call LLM
    prompt = build_closing_prompt(task)
    response = await LLMService.call_llm_streaming(
        prompt=prompt,
        plan_id=plan_id,
        websocket_manager=websocket_manager,
        agent_name="Closing"
    )
    
    return {"messages": [response], "final_result": response}
```

### 3. Update Agent Service

In `backend/app/services/agent_service.py`, add await for the async node:

```python
if next_agent == "closing":
    result = await closing_agent_node(state)
```

That's it! The agent now has full LLM support with streaming, error handling, and logging.

## Troubleshooting

### "No module named 'langchain_anthropic'"

```bash
cd backend
pip install langchain-anthropic
```

### "OPENAI_API_KEY environment variable is required"

1. Add key to `backend/.env`:
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   ```
2. Restart the backend server

### "LLM call timed out"

Increase timeout in `.env`:
```bash
LLM_TIMEOUT=120
```

### Response is still mock even with USE_MOCK_LLM=false

1. Verify `.env` has `USE_MOCK_LLM=false`
2. Restart the backend server
3. Check logs for `🎭 Mock mode is ENABLED` (should not appear)

### Rate limit errors

1. Wait a few minutes and try again
2. Use a cheaper/faster model (e.g., `gpt-4o-mini`)
3. Check your API usage limits in the provider dashboard

## Cost Management

### Estimated Costs (Nov 2024)

**OpenAI GPT-4o-mini** (recommended for testing):
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens
- Typical invoice task: ~$0.001-0.005 per request

**OpenAI GPT-4o**:
- Input: $2.50 per 1M tokens
- Output: $10.00 per 1M tokens
- Typical invoice task: ~$0.01-0.05 per request

### Tips to Minimize Costs

1. **Use mock mode for development**: `USE_MOCK_LLM=true`
2. **Use mini models for testing**: `OPENAI_MODEL=gpt-4o-mini`
3. **Use Ollama for local testing**: Free and private
4. **Set usage limits** in your provider dashboard
5. **Monitor usage** regularly

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for all secrets
3. **Rotate keys regularly**
4. **Use different keys** for dev/staging/production
5. **Monitor API usage** for anomalies
6. **Set spending limits** in provider dashboards

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify API keys are valid
3. Test with mock mode first
4. Review `TESTING_GUIDE.md`
5. Check provider status pages

## Future Enhancements

- [ ] Response caching to reduce costs
- [ ] Multi-turn conversations with context
- [ ] Tool calling for MCP integration
- [ ] Structured output (JSON mode)
- [ ] Fine-tuned models for specific domains
- [ ] Fallback providers on failure
- [ ] Cost tracking per user/plan
- [ ] A/B testing for prompt optimization
