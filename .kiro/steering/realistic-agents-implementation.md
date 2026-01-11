---
inclusion: manual
---

# Realistic Multi-Agent Implementation Guide

## Overview

This guide provides instructions for upgrading the current dummy agents to realistic LLM-powered agents. The implementation focuses on **Option A: Invoice Agent + Data Analyst Agent** as the minimal viable approach to demonstrate real multi-agent collaboration.

## Current State

- ✅ 3 dummy agents (Invoice, Closing, Audit) with hardcoded responses
- ✅ Planner routes based on keywords
- ✅ Human-in-the-loop approval working
- ✅ Frontend integration complete
- ✅ WebSocket streaming functional

## Implementation Goal

Transform 2 agents from dummy to realistic:
1. **Invoice Agent**: Real invoice analysis using LLM
2. **Data Analyst Agent**: Real data analysis and insights using LLM

**Estimated Effort**: 2-3 hours
**Files to Modify**: 4 files
**New Files**: 1 file
**Lines of Code**: ~150 lines total

---

## Phase 7: Realistic Agent Implementation

### Step 1: LLM Client Setup (30 minutes)

#### Create LLM Client Module

**File**: `backend/app/agents/llm_client.py` (NEW)

**Purpose**: Centralized LLM API client for all agents

**Implementation**:
```python
"""
LLM client for agent interactions.
Supports OpenAI, Anthropic, and Ollama.
"""
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class LLMClient:
    """Unified LLM client supporting multiple providers."""
    
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai")  # openai, anthropic, ollama
        self.api_key = None
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client based on provider."""
        if self.provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
            if self.api_key:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized")
        
        elif self.provider == "anthropic":
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
            if self.api_key:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
                logger.info("Anthropic client initialized")
        
        elif self.provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            from openai import OpenAI
            self.client = OpenAI(base_url=f"{base_url}/v1", api_key="ollama")
            logger.info(f"Ollama client initialized at {base_url}")
    
    def generate_response(
        self, 
        system_prompt: str, 
        user_message: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            system_prompt: System instructions for the agent
            user_message: User's task/question
            model: Model name (optional, uses default)
            temperature: Response randomness (0-1)
            max_tokens: Maximum response length
            
        Returns:
            Generated response text
        """
        if not self.client:
            logger.warning("LLM client not initialized, returning fallback response")
            return "LLM not configured. Please set LLM_PROVIDER and API key."
        
        try:
            if self.provider in ["openai", "ollama"]:
                model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            
            elif self.provider == "anthropic":
                model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_message}
                    ]
                )
                return response.content[0].text
        
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return f"Error generating response: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if LLM client is properly configured."""
        return self.client is not None


# Global LLM client instance
llm_client = LLMClient()
```

**Key Features**:
- Supports OpenAI, Anthropic, and Ollama
- Unified interface for all providers
- Error handling and fallback responses
- Environment-based configuration

---

### Step 2: Update Invoice Agent (1 hour)

#### Modify Invoice Agent Node

**File**: `backend/app/agents/nodes.py`

**Current Implementation** (lines 50-70):
```python
def invoice_agent_node(state: AgentState) -> Dict[str, Any]:
    """Invoice agent node - handles invoice management tasks."""
    task = state["task_description"]
    plan_id = state["plan_id"]
    
    logger.info(f"Invoice Agent processing task for plan {plan_id}")
    
    response = f"Invoice Agent here. I've processed your request:\n\n"
    response += "✓ Verified invoice accuracy and completeness\n"
    response += "✓ Checked payment due dates and status\n"
    response += "✓ Reviewed vendor information\n"
    response += "✓ Validated payment terms\n\n"
    response += "Invoice analysis complete. All checks passed successfully."
    
    return {
        "messages": [response],
        "current_agent": "Invoice",
        "final_result": response
    }
```

**New Implementation**:
```python
def invoice_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Invoice agent node - handles invoice management tasks using LLM.
    Provides realistic invoice analysis, validation, and recommendations.
    """
    from app.agents.llm_client import llm_client
    
    task = state["task_description"]
    plan_id = state["plan_id"]
    
    logger.info(f"Invoice Agent processing task for plan {plan_id}")
    
    # System prompt for invoice agent
    system_prompt = """You are an expert Invoice Management Agent specializing in:
- Invoice validation and accuracy verification
- Payment status tracking and due date management
- Vendor information review and compliance
- Duplicate invoice detection
- Payment terms analysis
- Invoice-to-PO matching

Provide clear, actionable analysis with specific findings and recommendations.
Format your response with bullet points for key findings.
Be concise but thorough."""

    # Generate response using LLM
    if llm_client.is_available():
        response = llm_client.generate_response(
            system_prompt=system_prompt,
            user_message=f"Task: {task}\n\nProvide a detailed invoice analysis.",
            temperature=0.7,
            max_tokens=800
        )
    else:
        # Fallback if LLM not configured
        response = f"Invoice Agent here. I've analyzed your request: '{task}'.\n\n"
        response += "⚠️ LLM not configured. Using fallback response.\n\n"
        response += "To enable realistic responses, configure:\n"
        response += "- OPENAI_API_KEY for OpenAI\n"
        response += "- ANTHROPIC_API_KEY for Anthropic\n"
        response += "- OLLAMA_BASE_URL for Ollama"
    
    return {
        "messages": [response],
        "current_agent": "Invoice",
        "final_result": response
    }
```

**Changes**:
- Import `llm_client`
- Define invoice-specific system prompt
- Call LLM with task description
- Provide fallback for unconfigured LLM
- Keep same function signature (no breaking changes)

---

### Step 3: Add Data Analyst Agent (1 hour)

#### Add New Agent Node

**File**: `backend/app/agents/nodes.py`

**Add after `audit_agent_node` function** (around line 120):

```python
def data_analyst_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Data Analyst agent node - handles data analysis and insights using LLM.
    Provides trend analysis, pattern detection, and business intelligence.
    """
    from app.agents.llm_client import llm_client
    
    task = state["task_description"]
    plan_id = state["plan_id"]
    
    logger.info(f"Data Analyst Agent processing task for plan {plan_id}")
    
    # System prompt for data analyst agent
    system_prompt = """You are an expert Data Analyst Agent specializing in:
- Trend analysis and pattern recognition
- Business intelligence and insights
- Comparative analysis and benchmarking
- Anomaly detection in data
- Predictive insights and forecasting
- Data-driven recommendations

Provide clear, actionable insights with specific findings.
Use data-driven language and quantify findings when possible.
Format your response with sections: Analysis, Key Findings, Recommendations.
Be analytical but accessible."""

    # Generate response using LLM
    if llm_client.is_available():
        response = llm_client.generate_response(
            system_prompt=system_prompt,
            user_message=f"Task: {task}\n\nProvide a comprehensive data analysis.",
            temperature=0.7,
            max_tokens=800
        )
    else:
        # Fallback if LLM not configured
        response = f"Data Analyst Agent here. I've analyzed your request: '{task}'.\n\n"
        response += "⚠️ LLM not configured. Using fallback response.\n\n"
        response += "To enable realistic responses, configure:\n"
        response += "- OPENAI_API_KEY for OpenAI\n"
        response += "- ANTHROPIC_API_KEY for Anthropic\n"
        response += "- OLLAMA_BASE_URL for Ollama"
    
    return {
        "messages": [response],
        "current_agent": "DataAnalyst",
        "final_result": response
    }
```

#### Update Planner Routing

**File**: `backend/app/agents/nodes.py`

**Current planner_node function** (lines 15-45):
```python
def planner_node(state: AgentState) -> Dict[str, Any]:
    """Planner agent node - analyzes task and creates execution plan."""
    task = state["task_description"]
    plan_id = state["plan_id"]
    
    logger.info(f"Planner processing task for plan {plan_id}")
    
    # Analyze task and determine which agent to route to
    task_lower = task.lower()
    
    if any(word in task_lower for word in ["invoice", "payment", "bill", "vendor"]):
        next_agent = "invoice"
        response = f"I've analyzed your task: '{task}'.\n\nThis appears to be an invoice-related task. Routing to Invoice Agent for specialized handling."
    elif any(word in task_lower for word in ["closing", "reconciliation", "journal", "variance", "gl"]):
        next_agent = "closing"
        response = f"I've analyzed your task: '{task}'.\n\nThis appears to be a closing process task. Routing to Closing Agent for specialized handling."
    elif any(word in task_lower for word in ["audit", "compliance", "evidence", "exception", "monitoring"]):
        next_agent = "audit"
        response = f"I've analyzed your task: '{task}'.\n\nThis appears to be an audit-related task. Routing to Audit Agent for specialized handling."
    else:
        # Default to invoice agent
        next_agent = "invoice"
        response = f"I've analyzed your task: '{task}'.\n\nRouting to Invoice Agent for processing."
    
    return {
        "messages": [response],
        "current_agent": "Planner",
        "next_agent": next_agent
    }
```

**Updated planner_node function**:
```python
def planner_node(state: AgentState) -> Dict[str, Any]:
    """Planner agent node - analyzes task and creates execution plan."""
    task = state["task_description"]
    plan_id = state["plan_id"]
    
    logger.info(f"Planner processing task for plan {plan_id}")
    
    # Analyze task and determine which agent to route to
    task_lower = task.lower()
    
    # Check for data analysis keywords first (new agent)
    if any(word in task_lower for word in ["analyze", "analysis", "data", "trend", "pattern", "insight", "report", "metrics", "statistics"]):
        next_agent = "data_analyst"
        response = f"I've analyzed your task: '{task}'.\n\nThis appears to be a data analysis task. Routing to Data Analyst Agent for specialized handling."
    
    # Invoice-related tasks
    elif any(word in task_lower for word in ["invoice", "payment", "bill", "vendor", "payable"]):
        next_agent = "invoice"
        response = f"I've analyzed your task: '{task}'.\n\nThis appears to be an invoice-related task. Routing to Invoice Agent for specialized handling."
    
    # Closing process tasks
    elif any(word in task_lower for word in ["closing", "reconciliation", "journal", "variance", "gl"]):
        next_agent = "closing"
        response = f"I've analyzed your task: '{task}'.\n\nThis appears to be a closing process task. Routing to Closing Agent for specialized handling."
    
    # Audit tasks
    elif any(word in task_lower for word in ["audit", "compliance", "evidence", "exception", "monitoring"]):
        next_agent = "audit"
        response = f"I've analyzed your task: '{task}'.\n\nThis appears to be an audit-related task. Routing to Audit Agent for specialized handling."
    
    # Default to data analyst for general queries
    else:
        next_agent = "data_analyst"
        response = f"I've analyzed your task: '{task}'.\n\nRouting to Data Analyst Agent for processing."
    
    return {
        "messages": [response],
        "current_agent": "Planner",
        "next_agent": next_agent
    }
```

**Changes**:
- Added data analysis keywords: "analyze", "data", "trend", "pattern", "insight", "report", "metrics", "statistics"
- Prioritize data analyst routing for analysis tasks
- Changed default from invoice to data_analyst
- More specific keyword matching

---

### Step 4: Update Agent Service (30 minutes)

#### Add Data Analyst Case

**File**: `backend/app/services/agent_service.py`

**Current resume_after_approval function** (lines 150-180):
```python
# Execute the appropriate specialized agent
if next_agent == "invoice":
    result = invoice_agent_node(state)
else:
    result = {"messages": ["No specialized agent selected"], "final_result": "Task completed"}
```

**Updated code**:
```python
# Execute the appropriate specialized agent
if next_agent == "invoice":
    result = invoice_agent_node(state)
elif next_agent == "data_analyst":
    result = data_analyst_agent_node(state)
else:
    result = {"messages": ["No specialized agent selected"], "final_result": "Task completed"}
```

**Also update imports at top of file**:
```python
from app.agents.nodes import planner_node, invoice_agent_node, data_analyst_agent_node
```

---

### Step 5: Update Requirements (5 minutes)

#### Add LLM Dependencies

**File**: `backend/requirements.txt`

**Add these lines**:
```
# LLM Providers (choose one or more)
openai>=1.0.0
anthropic>=0.7.0
```

**Note**: Ollama doesn't require a package, it uses the OpenAI client with a different base URL.

---

### Step 6: Environment Configuration (5 minutes)

#### Update Environment Variables

**File**: `backend/.env`

**Add LLM configuration**:
```bash
# LLM Provider Configuration
# Choose: openai, anthropic, or ollama
LLM_PROVIDER=openai

# OpenAI Configuration (if using OpenAI)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Anthropic Configuration (if using Anthropic)
# ANTHROPIC_API_KEY=your-anthropic-api-key-here
# ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Ollama Configuration (if using Ollama locally)
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=llama3
```

**File**: `backend/.env.example`

**Update with same configuration** (without actual keys)

---

## Testing Strategy

### Test Scenarios

#### Invoice Agent Tests

**Test 1: Invoice Validation**
```
Input: "Analyze invoice INV-2024-001: Amount $5,000, Due Date: Dec 31, 2024, Vendor: Acme Corp"
Expected: Detailed validation with specific findings
```

**Test 2: Payment Status**
```
Input: "Check payment status for invoices from Acme Corp in November"
Expected: Analysis of payment patterns and status
```

**Test 3: Duplicate Detection**
```
Input: "Are there any duplicate invoices for PO-12345?"
Expected: Duplicate detection analysis
```

#### Data Analyst Agent Tests

**Test 4: Trend Analysis**
```
Input: "Analyze sales trends for Q4 2024"
Expected: Trend insights and patterns
```

**Test 5: Anomaly Detection**
```
Input: "Identify unusual spending patterns in procurement data"
Expected: Anomaly detection with specific findings
```

**Test 6: Comparative Analysis**
```
Input: "Compare revenue between Q3 and Q4"
Expected: Comparative analysis with insights
```

### Testing Checklist

- [ ] LLM client initializes correctly
- [ ] Invoice agent returns realistic responses
- [ ] Data analyst agent returns realistic responses
- [ ] Planner routes correctly to new agent
- [ ] Responses vary based on input (not hardcoded)
- [ ] Error handling works when LLM unavailable
- [ ] Frontend displays LLM responses correctly
- [ ] Approval flow works with realistic agents
- [ ] Multiple tasks can run concurrently

---

## Implementation Checklist

### Pre-Implementation
- [ ] Choose LLM provider (OpenAI recommended)
- [ ] Obtain API key
- [ ] Install dependencies: `pip install openai anthropic`
- [ ] Test API key works

### Implementation Steps
- [ ] **Step 1**: Create `llm_client.py` (30 min)
- [ ] **Step 2**: Update `invoice_agent_node()` (30 min)
- [ ] **Step 3**: Add `data_analyst_agent_node()` (30 min)
- [ ] **Step 4**: Update planner routing (15 min)
- [ ] **Step 5**: Update agent service (15 min)
- [ ] **Step 6**: Update requirements.txt (5 min)
- [ ] **Step 7**: Configure environment variables (5 min)

### Testing
- [ ] Test invoice agent with 3 scenarios
- [ ] Test data analyst agent with 3 scenarios
- [ ] Test planner routing
- [ ] Test error handling
- [ ] Test frontend integration
- [ ] Run end-to-end workflow

### Validation
- [ ] Responses are contextual and relevant
- [ ] No hardcoded text in responses
- [ ] Agents provide different responses for different inputs
- [ ] Error messages are clear
- [ ] Performance is acceptable (< 5 seconds per response)

---

## Expected Results

### Before Implementation
```
User: "Analyze invoice INV-2024-001"
Invoice Agent: "✓ Verified invoice accuracy and completeness
✓ Checked payment due dates and status
✓ Reviewed vendor information..."
(Same response every time)
```

### After Implementation
```
User: "Analyze invoice INV-2024-001 for amount $5,000"
Invoice Agent: "I've analyzed invoice INV-2024-001. Here are my findings:

**Invoice Details:**
- Amount: $5,000.00
- Status: Requires verification

**Key Findings:**
- Amount is within normal range for this vendor
- Due date should be verified against payment terms
- Recommend checking against corresponding PO

**Recommendations:**
1. Verify PO match
2. Confirm vendor details
3. Check payment schedule"
(Contextual, varies with input)
```

---

## Troubleshooting

### Issue: LLM Client Not Initializing
**Solution**: Check environment variables are set correctly
```bash
echo $OPENAI_API_KEY
# Should show your API key
```

### Issue: "LLM not configured" Message
**Solution**: Verify `.env` file is loaded
```python
import os
print(os.getenv("OPENAI_API_KEY"))
```

### Issue: Slow Responses
**Solution**: 
- Use faster model (gpt-4o-mini instead of gpt-4)
- Reduce max_tokens
- Consider caching common responses

### Issue: API Rate Limits
**Solution**:
- Add retry logic with exponential backoff
- Implement request queuing
- Use lower tier model

### Issue: Responses Too Generic
**Solution**:
- Improve system prompts with more specific instructions
- Include examples in prompts
- Adjust temperature (lower = more focused)

---

## Performance Considerations

### Response Times
- **OpenAI gpt-4o-mini**: 1-3 seconds
- **Anthropic Claude Sonnet**: 2-4 seconds
- **Ollama (local)**: 5-15 seconds

### Cost Estimates (OpenAI gpt-4o-mini)
- Input: $0.150 per 1M tokens
- Output: $0.600 per 1M tokens
- Average task: ~500 tokens = $0.0003 per request
- 1000 requests = ~$0.30

### Optimization Tips
1. **Cache common queries**: Store frequent responses
2. **Batch requests**: Process multiple tasks together
3. **Use streaming**: Show partial responses as they generate
4. **Implement timeouts**: Prevent hanging requests
5. **Monitor usage**: Track API costs and usage patterns

---

## Next Steps After Implementation

### Phase 8: Tool Integration
Once realistic agents are working:
1. Connect MCP server tools to agents
2. Enable agents to call external APIs
3. Add file processing capabilities
4. Implement web search integration

### Phase 9: Advanced Features
1. **Memory**: Add conversation history
2. **Context**: Share information between agents
3. **Learning**: Improve responses based on feedback
4. **Streaming**: Real-time token-by-token responses

### Phase 10: Production Readiness
1. **Monitoring**: Add logging and metrics
2. **Caching**: Implement response caching
3. **Rate Limiting**: Protect against abuse
4. **Error Recovery**: Robust error handling
5. **Testing**: Comprehensive test suite

---

## Success Criteria

Implementation is successful when:
- ✅ Invoice agent provides contextual, relevant responses
- ✅ Data analyst agent provides insightful analysis
- ✅ Responses vary based on input (not hardcoded)
- ✅ Planner correctly routes to appropriate agent
- ✅ Error handling works gracefully
- ✅ Frontend displays LLM responses correctly
- ✅ Approval flow works end-to-end
- ✅ Performance is acceptable (< 5 seconds)
- ✅ Multiple concurrent tasks work
- ✅ System is stable and reliable

---

## References

- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Anthropic API Documentation](https://docs.anthropic.com/claude/reference)
- [Ollama Documentation](https://ollama.ai/docs)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

---

**Document Version**: 1.0
**Last Updated**: November 25, 2025
**Status**: Ready for Implementation
