# Design Document

## Overview

This design document outlines the integration of real LLM API calls into the Invoice Agent, replacing hardcoded responses with intelligent AI-generated analysis. The solution provides a configurable, reusable pattern that supports multiple LLM providers (OpenAI, Anthropic, Ollama) with streaming capabilities, error handling, and a mock mode for cost-effective testing.

The design follows the existing LangGraph multi-agent architecture and maintains compatibility with the current WebSocket streaming infrastructure. The LLM service layer is designed to be provider-agnostic and reusable across all specialized agents.

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│   Frontend      │
│   (React)       │
└────────┬────────┘
         │ WebSocket
         │ (streaming)
         ▼
┌─────────────────┐
│   FastAPI       │
│   Backend       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   LangGraph     │
│   Workflow      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│ Invoice Agent   │─────▶│   LLM Service    │
│    Node         │      │   (Configurable) │
└─────────────────┘      └────────┬─────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
              ┌──────────┐  ┌──────────┐  ┌──────────┐
              │ OpenAI   │  │Anthropic │  │  Ollama  │
              │   API    │  │   API    │  │  Local   │
              └──────────┘  └──────────┘  └──────────┘
```

### Component Interaction Flow

1. **User submits task** → Frontend sends to FastAPI
2. **FastAPI creates plan** → Initializes LangGraph workflow
3. **Planner routes to Invoice Agent** → Based on task keywords
4. **Invoice Agent calls LLM Service** → With task description and context
5. **LLM Service checks mock mode** → Returns dummy or calls real API
6. **LLM streams response** → Tokens sent via WebSocket
7. **Frontend displays results** → Real-time streaming UI

## Components and Interfaces

### 1. LLM Service Module (`app/services/llm_service.py`)

**Purpose**: Centralized service for LLM provider configuration and API calls.

**Key Methods**:

```python
class LLMService:
    @staticmethod
    def get_llm_instance() -> BaseChatModel:
        """Get configured LLM instance based on environment variables."""
        
    @staticmethod
    def is_mock_mode() -> bool:
        """Check if mock mode is enabled."""
        
    @staticmethod
    async def call_llm_streaming(
        prompt: str,
        plan_id: str,
        websocket_manager: WebSocketManager,
        agent_name: str = "Invoice"
    ) -> str:
        """Call LLM with streaming support and WebSocket delivery."""
        
    @staticmethod
    def get_mock_response(agent_name: str, task: str) -> str:
        """Return hardcoded mock response for testing."""
```

**Configuration**:
- Reads `LLM_PROVIDER` (openai|anthropic|ollama)
- Reads `USE_MOCK_LLM` (true|false)
- Reads provider-specific keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
- Reads model names (OPENAI_MODEL, OLLAMA_MODEL, etc.)

### 2. Updated Invoice Agent Node (`app/agents/nodes.py`)

**Current Implementation**:
```python
def invoice_agent_node(state: AgentState) -> Dict[str, Any]:
    # Hardcoded response
    response = "Invoice Agent here. I've processed your request..."
    return {"messages": [response], "final_result": response}
```

**New Implementation**:
```python
async def invoice_agent_node(state: AgentState) -> Dict[str, Any]:
    task = state["task_description"]
    plan_id = state["plan_id"]
    
    # Check mock mode
    if LLMService.is_mock_mode():
        response = LLMService.get_mock_response("Invoice", task)
        return {"messages": [response], "final_result": response}
    
    # Build prompt
    prompt = build_invoice_prompt(task)
    
    # Call LLM with streaming
    websocket_manager = state.get("websocket_manager")
    response = await LLMService.call_llm_streaming(
        prompt=prompt,
        plan_id=plan_id,
        websocket_manager=websocket_manager,
        agent_name="Invoice"
    )
    
    return {"messages": [response], "final_result": response}
```

### 3. Prompt Templates (`app/agents/prompts.py`)

**Purpose**: Domain-specific prompt templates for each agent.

```python
INVOICE_AGENT_PROMPT = """You are an expert Invoice Agent specializing in invoice management and analysis.

Your expertise includes:
- Verifying invoice accuracy and completeness
- Checking payment due dates and status
- Reviewing vendor information
- Validating payment terms
- Identifying discrepancies or issues

Task: {task_description}

Please analyze this invoice-related task and provide:
1. A clear assessment of the situation
2. Any issues or concerns identified
3. Recommended actions or next steps
4. Specific details about invoice accuracy, due dates, vendor info, and payment terms

Provide your analysis in a clear, structured format."""

def build_invoice_prompt(task_description: str) -> str:
    """Build invoice agent prompt with task details."""
    return INVOICE_AGENT_PROMPT.format(task_description=task_description)
```

### 4. Environment Configuration

**New Environment Variables**:

```bash
# LLM Provider Configuration
LLM_PROVIDER=openai              # openai | anthropic | ollama
USE_MOCK_LLM=false               # true | false

# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o              # gpt-4o | gpt-4-turbo | gpt-3.5-turbo

# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Ollama Configuration (for local development)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# LLM Settings
LLM_TIMEOUT=60                   # seconds
LLM_MAX_RETRIES=2
LLM_TEMPERATURE=0.7
```

### 5. WebSocket Streaming Integration

**Streaming Flow**:

1. **Start Stream**: Send `agent_stream_start` message
2. **Stream Tokens**: Send `agent_message_streaming` for each token
3. **End Stream**: Send `agent_stream_end` message
4. **Final Message**: Send complete `agent_message` with full content

**Message Format**:
```python
# Stream start
{
    "type": "agent_stream_start",
    "agent": "Invoice",
    "plan_id": "uuid",
    "timestamp": "ISO8601"
}

# Token streaming
{
    "type": "agent_message_streaming",
    "agent": "Invoice",
    "content": "token",
    "plan_id": "uuid"
}

# Stream end
{
    "type": "agent_stream_end",
    "agent": "Invoice",
    "plan_id": "uuid",
    "timestamp": "ISO8601"
}
```

## Data Models

### AgentState Extension

```python
class AgentState(TypedDict):
    # Existing fields
    task_description: str
    plan_id: str
    messages: List[str]
    current_agent: str
    next_agent: str
    final_result: str
    
    # New fields for LLM integration
    websocket_manager: Optional[WebSocketManager]  # For streaming
    llm_provider: Optional[str]                    # Override provider
    llm_temperature: Optional[float]               # Override temperature
```

### LLM Configuration Model

```python
from pydantic import BaseModel, Field

class LLMConfig(BaseModel):
    """LLM provider configuration."""
    provider: str = Field(default="openai", description="LLM provider name")
    use_mock: bool = Field(default=False, description="Use mock responses")
    api_key: Optional[str] = Field(default=None, description="API key")
    model: str = Field(default="gpt-4o", description="Model name")
    base_url: Optional[str] = Field(default=None, description="Base URL for Ollama")
    timeout: int = Field(default=60, description="Request timeout in seconds")
    max_retries: int = Field(default=2, description="Maximum retry attempts")
    temperature: float = Field(default=0.7, description="Sampling temperature")
```

## Data Flow

### Mock Mode Flow

```
User Task → Invoice Agent → Check Mock Mode (TRUE)
                          → Get Mock Response
                          → Return Hardcoded Response
                          → WebSocket → Frontend
```

### Real API Flow

```
User Task → Invoice Agent → Check Mock Mode (FALSE)
                          → Build Prompt Template
                          → Call LLM Service
                          → Initialize LLM Provider
                          → Stream API Call
                          → For Each Token:
                              → Send via WebSocket
                          → Collect Full Response
                          → Return Final Result
                          → Store in Database
```

### Error Handling Flow

```
LLM API Call → Timeout?
            → Yes → Log Error → Return Timeout Message
            → No → Rate Limit?
                → Yes → Retry with Backoff (max 2 times)
                      → Still Failing? → Return Error Message
                → No → Auth Error?
                    → Yes → Log Error → Return Auth Error
                    → No → Success → Return Response
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Prompt Structure Completeness

*For any* task description, when the Invoice Agent constructs a prompt, the resulting prompt string should contain all required sections: agent role/expertise, the task description, output format instructions, and data handling guidelines.

**Validates: Requirements 4.1, 4.2, 4.3, 4.5**

### Property 2: LLM Provider Configuration

*For any* valid LLM provider name (openai, anthropic, ollama), when the LLM service initializes with that provider configuration, it should return an LLM instance of the correct type that can accept prompts and return responses.

**Validates: Requirements 2.1**

### Property 3: Streaming Message Sequence

*For any* LLM response stream, the WebSocket messages should follow the correct sequence: exactly one `agent_stream_start` message, followed by zero or more `agent_message_streaming` messages, followed by exactly one `agent_stream_end` message.

**Validates: Requirements 3.2, 3.3, 3.4**

### Property 4: Mock Mode Behavior

*For any* task description, when `USE_MOCK_LLM` is set to true, the Invoice Agent should return a response without making any external API calls, and when set to false, it should make an API call to the configured LLM provider.

**Validates: Requirements 8.2, 8.3**

### Property 5: Timeout Configuration

*For any* LLM API call, the request should have a timeout value set that does not exceed 60 seconds.

**Validates: Requirements 5.1**

### Property 6: Retry Logic for Rate Limits

*For any* LLM API call that returns a rate limit error, the system should retry the request up to 2 additional times with exponential backoff before failing.

**Validates: Requirements 5.3**

### Property 7: Logging Completeness

*For any* LLM API call, the system should create log entries that include the plan_id, agent name, and either response metrics (on success) or error details (on failure).

**Validates: Requirements 6.1, 6.2, 6.3, 6.5**

### Property 8: API Key Security in Logs

*For any* log entry created during LLM interactions, the log message should not contain API keys or authentication tokens.

**Validates: Requirements 6.4**

### Property 9: Provider Encapsulation

*For any* agent using the LLM service, the agent code should not need to import or reference provider-specific classes (ChatOpenAI, ChatAnthropic, ChatOllama) directly.

**Validates: Requirements 7.5**

### Property 10: Response Flow Integrity

*For any* successful LLM API call, the response content returned by the LLM should be included in the agent's final_result field in the state.

**Validates: Requirements 1.4**

### Property 11: Mock Mode Logging Transparency

*For any* task processed in mock mode, the system logs should contain a message indicating that mock responses are being used.

**Validates: Requirements 8.5**

## Error Handling

### Error Categories

1. **Configuration Errors**
   - Missing API keys
   - Invalid provider name
   - Missing required environment variables
   - **Handling**: Raise clear error at startup, don't allow server to start

2. **API Errors**
   - Timeout (> 60 seconds)
   - Rate limiting (429 status)
   - Authentication failure (401 status)
   - Invalid request (400 status)
   - **Handling**: Log error, return user-friendly message, don't expose internal details

3. **Network Errors**
   - Connection refused
   - DNS resolution failure
   - SSL/TLS errors
   - **Handling**: Log error, retry if appropriate, return connectivity error message

4. **Streaming Errors**
   - WebSocket disconnection during streaming
   - Client timeout
   - Partial response
   - **Handling**: Log error, clean up resources, notify remaining clients

### Error Response Format

```python
{
    "error": True,
    "error_type": "timeout" | "auth" | "rate_limit" | "network" | "unknown",
    "message": "User-friendly error message",
    "agent": "Invoice",
    "plan_id": "uuid",
    "timestamp": "ISO8601"
}
```

### Retry Strategy

```python
# Exponential backoff for rate limits
retry_delays = [2, 4]  # seconds
max_retries = 2

for attempt in range(max_retries + 1):
    try:
        response = await llm.call(prompt)
        return response
    except RateLimitError:
        if attempt < max_retries:
            await asyncio.sleep(retry_delays[attempt])
        else:
            raise
```

### Graceful Degradation

When LLM API is unavailable:
1. Log the error with full context
2. Return a clear error message to the user
3. Suggest using mock mode for testing
4. Don't crash the server or workflow
5. Allow other agents to continue if possible

## Testing Strategy

### Unit Tests

1. **LLM Service Tests**
   - Test provider initialization for each provider type
   - Test mock mode detection
   - Test configuration reading from environment
   - Test error handling for missing config

2. **Prompt Building Tests**
   - Test prompt template formatting
   - Test variable substitution
   - Test handling of missing data
   - Test prompt length limits

3. **Mock Response Tests**
   - Test mock response generation
   - Test mock mode flag detection
   - Test that no API calls are made in mock mode

### Property-Based Tests

Property-based tests will use the `hypothesis` library for Python to generate random inputs and verify that correctness properties hold across all inputs.

**Configuration**:
- Minimum 100 iterations per property test
- Use appropriate generators for each input type
- Tag each test with the property number from this design document

**Test Tagging Format**:
```python
# Feature: llm-agent-integration, Property 1: Prompt Structure Completeness
# Validates: Requirements 4.1, 4.2, 4.3, 4.5
@given(task_description=st.text(min_size=1, max_size=1000))
def test_prompt_structure_completeness(task_description):
    prompt = build_invoice_prompt(task_description)
    assert "Invoice Agent" in prompt  # Role
    assert task_description in prompt  # Task
    assert "provide" in prompt.lower()  # Instructions
    assert "format" in prompt.lower()  # Format guidance
```

**Property Test Coverage**:
- Property 1: Prompt structure (test with random task descriptions)
- Property 2: Provider configuration (test with different provider configs)
- Property 3: Streaming sequence (test with mock token streams)
- Property 4: Mock mode behavior (test with random tasks in both modes)
- Property 5: Timeout configuration (test with different LLM configs)
- Property 6: Retry logic (test with mock rate limit errors)
- Property 7: Logging completeness (test with random API calls)
- Property 8: API key security (test that logs never contain keys)
- Property 9: Provider encapsulation (test agent imports)
- Property 10: Response flow (test with mock LLM responses)
- Property 11: Mock mode logging (test log output in mock mode)

### Integration Tests

1. **End-to-End Flow Tests**
   - Test complete flow from task submission to LLM response
   - Test WebSocket streaming delivery
   - Test database persistence of results
   - Test frontend display of streamed responses

2. **Provider Integration Tests**
   - Test actual API calls to OpenAI (with test key)
   - Test actual API calls to Anthropic (with test key)
   - Test local Ollama integration
   - Test provider switching

3. **Error Scenario Tests**
   - Test timeout handling with slow mock LLM
   - Test rate limit handling with mock 429 responses
   - Test auth error handling with invalid keys
   - Test network error handling with unreachable endpoints

### Manual Testing Checklist

- [ ] Submit invoice task in mock mode, verify dummy response
- [ ] Submit invoice task in real mode, verify AI response
- [ ] Switch between providers, verify correct provider is used
- [ ] Observe WebSocket streaming in browser DevTools
- [ ] Trigger timeout by setting very low timeout value
- [ ] Trigger rate limit by making many rapid requests
- [ ] Check logs for proper formatting and no API keys
- [ ] Verify other agents (Closing, Audit) still work
- [ ] Test with missing API key, verify error message
- [ ] Test with invalid provider name, verify error message

## Performance Considerations

### Response Time Targets

- **Mock Mode**: < 100ms response time
- **Real API Mode**: < 5 seconds for first token, < 30 seconds total
- **Streaming**: < 50ms latency per token delivery

### Resource Usage

- **Memory**: LLM service should be singleton, not create new instances per request
- **Connections**: Reuse HTTP connections to LLM providers
- **WebSocket**: Limit concurrent connections per user (max 5)

### Optimization Strategies

1. **Connection Pooling**: Use httpx with connection pooling for API calls
2. **Caching**: Cache LLM provider instances (singleton pattern)
3. **Async Operations**: Use async/await throughout the chain
4. **Streaming**: Stream tokens immediately, don't buffer entire response
5. **Timeout Management**: Set aggressive timeouts to prevent hanging requests

## Security Considerations

### API Key Management

- Store API keys in environment variables only
- Never log API keys or include in error messages
- Never send API keys to frontend
- Use different keys for dev/staging/production
- Rotate keys regularly

### Input Validation

- Validate task description length (max 10,000 characters)
- Sanitize task description before including in prompts
- Validate LLM provider name against whitelist
- Validate configuration values at startup

### Rate Limiting

- Implement per-user rate limiting (10 requests per minute)
- Implement per-plan rate limiting (1 concurrent request)
- Track API usage per user for billing/monitoring
- Implement circuit breaker for failing LLM providers

### Data Privacy

- Don't send PII to LLM providers without user consent
- Log only non-sensitive data
- Implement data retention policies for logs
- Consider on-premise Ollama for sensitive data

## Deployment Considerations

### Environment Setup

**Development**:
```bash
LLM_PROVIDER=ollama
USE_MOCK_LLM=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

**Staging**:
```bash
LLM_PROVIDER=openai
USE_MOCK_LLM=false
OPENAI_API_KEY=sk-staging-...
OPENAI_MODEL=gpt-4o
LLM_TIMEOUT=60
```

**Production**:
```bash
LLM_PROVIDER=openai
USE_MOCK_LLM=false
OPENAI_API_KEY=sk-prod-...
OPENAI_MODEL=gpt-4o
LLM_TIMEOUT=60
LLM_MAX_RETRIES=2
```

### Monitoring

**Metrics to Track**:
- LLM API call count (by provider, by agent)
- LLM API latency (p50, p95, p99)
- LLM API error rate (by error type)
- Token usage (for cost tracking)
- Mock mode usage percentage

**Alerts**:
- LLM API error rate > 5%
- LLM API latency p95 > 10 seconds
- LLM API timeout rate > 1%
- API key authentication failures

### Cost Management

- Track token usage per user/plan
- Set monthly budget limits
- Use mock mode for automated tests
- Use cheaper models for non-critical tasks
- Implement caching for repeated queries (future enhancement)

## Future Enhancements

1. **Response Caching**: Cache LLM responses for identical prompts
2. **Multi-Agent Collaboration**: Allow agents to call each other via LLM
3. **Tool Calling**: Enable LLM to call MCP tools directly
4. **Prompt Optimization**: A/B test different prompt templates
5. **Fine-tuning**: Fine-tune models on domain-specific data
6. **Fallback Providers**: Automatically switch providers on failure
7. **Cost Optimization**: Use cheaper models for simple tasks
8. **Structured Output**: Use JSON mode for structured responses
9. **Context Management**: Implement conversation history for multi-turn interactions
10. **Agent Memory**: Store and retrieve relevant past interactions

## Migration Path for Other Agents

Once the Invoice Agent LLM integration is complete and tested, the pattern can be extended to other agents:

### Closing Agent
- Create `CLOSING_AGENT_PROMPT` template
- Update `closing_agent_node` to use `LLMService`
- Add closing-specific prompt building function
- Test with closing-related tasks

### Audit Agent
- Create `AUDIT_AGENT_PROMPT` template
- Update `audit_agent_node` to use `LLMService`
- Add audit-specific prompt building function
- Test with audit-related tasks

### Contract Agent (Future)
- Create `CONTRACT_AGENT_PROMPT` template
- Implement `contract_agent_node` using `LLMService`
- Add contract-specific prompt building function
- Test with contract-related tasks

### Procurement Agent (Future)
- Create `PROCUREMENT_AGENT_PROMPT` template
- Implement `procurement_agent_node` using `LLMService`
- Add procurement-specific prompt building function
- Test with procurement-related tasks

**Reusable Components**:
- `LLMService` class (no changes needed)
- Streaming logic (no changes needed)
- Error handling patterns (no changes needed)
- Configuration management (no changes needed)
- Testing patterns (adapt for each agent)

**Agent-Specific Work**:
- Prompt template design (domain expertise required)
- Prompt building function (extract relevant data)
- Response formatting (if needed)
- Domain-specific error handling (if needed)
