w# Multi-Agent Invoice Analysis Workflow - Design Document

## Overview

This design document outlines the architecture and implementation approach for a multi-agent workflow system that analyzes invoice data across multiple business systems. The system coordinates AI agents to gather data from email, accounts payable, and CRM systems, then generates comprehensive analysis reports with human-in-the-loop approval.

The design builds upon the proven foundation of the existing integrated test framework that achieves 100% success rate for vendor invoice analysis scenarios.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    User[User Query] --> Planner[AI Planner Agent]
    Planner --> HITL[Human Approval]
    HITL --> Orchestrator[Agent Orchestrator]
    
    Orchestrator --> Email[Email Agent]
    Orchestrator --> AP[AccountsPayable Agent]
    Orchestrator --> CRM[CRM Agent]
    
    Email --> MCP1[Email MCP Server]
    AP --> MCP2[Bill.com MCP Server]
    CRM --> MCP3[Salesforce MCP Server]
    
    Email --> Analysis[Analysis Agent][Analysis Agent]
    AP --> Analysis
    CRM --> Analysis
    
    Analysis --> Report[Final Report]
    
    Orchestrator --> WS[WebSocket Manager]
    WS --> Frontend[Frontend UI]
```

### Core Principles

1. **Agent Autonomy**: Each agent operates independently with clear responsibilities
2. **Graceful Degradation**: System continues operation when individual agents fail
3. **Real-time Communication**: WebSocket streaming provides live progress updates
4. **Human Oversight**: Critical decisions require human approval
5. **Vendor Agnostic**: Framework supports any vendor, not just specific test cases

## Components and Interfaces

### 1. AI Planner Agent

**Purpose**: Analyzes user queries and generates multi-step execution plans

**Interface**:
```python
class AIPlanner:
    async def plan_workflow(self, query: str) -> PlanResult:
        """Generate execution plan for user query"""
        pass
```

**Responsibilities**:
- Parse natural language queries
- Identify required agents and data sources
- Generate structured execution plan
- Estimate complexity and duration

### 2. Agent Orchestrator

**Purpose**: Coordinates multi-agent execution with proper sequencing

**Interface**:
```python
class AgentOrchestrator:
    async def execute_plan(self, plan: ExecutionPlan) -> WorkflowResult:
        """Execute multi-agent workflow"""
        pass
    
    async def handle_agent_failure(self, agent: str, error: Exception):
        """Handle individual agent failures gracefully"""
        pass
```

**Responsibilities**:
- Execute agents in correct sequence
- Pass data between agents
- Handle agent failures without crashing workflow
- Coordinate with WebSocket manager for progress updates

### 3. Individual Agents

#### Email Agent
**Purpose**: Search and extract invoice-related emails

**Interface**:
```python
class EmailAgent:
    async def search_emails(self, vendor_name: str, keywords: List[str]) -> EmailResult:
        """Search for vendor-related emails"""
        pass
```

**Responsibilities**:
- Search emails by vendor name and keywords
- Extract invoice numbers, amounts, dates
- Identify payment status communications
- Support multiple email providers (Gmail, Outlook, etc.)
- Handle MCP server connection issues with environment-controlled fallback

#### AccountsPayable Agent
**Purpose**: Retrieve bill data from accounts payable systems

**Interface**:
```python
class AccountsPayableAgent:
    async def search_bills(self, vendor_name: str) -> BillResult:
        """Search for vendor bills in AP system"""
        pass
```

**Responsibilities**:
- Query Bill.com for vendor records
- Retrieve bill status, amounts, payment dates
- Correlate with email data
- Handle API failures gracefully

#### CRM Agent
**Purpose**: Retrieve customer/vendor data from CRM systems

**Interface**:
```python
class CRMAgent:
    async def search_records(self, vendor_name: str) -> CRMResult:
        """Search for vendor records in CRM"""
        pass
```

**Responsibilities**:
- Search Salesforce for account records
- Retrieve customer relationship data
- Identify opportunities and account issues
- Handle authentication and API limits

### 4. Analysis Agent

**Purpose**: Generate comprehensive reports from collected data

**Interface**:
```python
class AnalysisAgent:
    async def generate_analysis(self, 
                              gmail_data: EmailResult,
                              ap_data: BillResult, 
                              crm_data: CRMResult) -> AnalysisReport:
        """Generate cross-system analysis"""
        pass
```

**Responsibilities**:
- Correlate data across all systems
- Identify payment issues and discrepancies
- Generate actionable recommendations
- Format results for business users

### 5. WebSocket Manager

**Purpose**: Provide real-time communication with frontend

**Interface**:
```python
class WebSocketManager:
    async def send_progress_update(self, plan_id: str, progress: ProgressUpdate):
        """Send progress update to frontend"""
        pass
    
    async def stream_agent_response(self, plan_id: str, content: str):
        """Stream agent response content"""
        pass
```

**Message Types**:
- `agent_stream_start`: Agent begins processing
- `agent_message_streaming`: Token-by-token content streaming
- `agent_stream_end`: Agent completes processing
- `plan_approval_request`: Request human approval
- `step_progress`: Overall workflow progress

### 6. MCP Integration Layer

**Purpose**: Standardized communication with external services

**Interface**:
```python
class MCPHttpManager:
    async def call_tool(self, service_name: str, tool_name: str, arguments: dict) -> Any:
        """Call MCP tool via HTTP"""
        pass
```

**Services**:
- Bill.com MCP Server (Port 9000)
- Salesforce MCP Server (Port 9001)
- Email MCP Server (Gmail/Outlook when available)

## Data Models

### Core Data Structures

```python
@dataclass
class ExecutionPlan:
    plan_id: str
    description: str
    steps: List[ExecutionStep]
    estimated_duration: float
    complexity_score: float

@dataclass
class ExecutionStep:
    id: str
    agent: str
    description: str
    status: StepStatus
    dependencies: List[str]

@dataclass
class WorkflowResult:
    success: bool
    plan_id: str
    results: Dict[str, AgentResult]
    final_analysis: str
    execution_time: float

@dataclass
class AgentResult:
    agent_name: str
    status: str
    data: Any
    error_message: Optional[str]
    execution_time: float

@dataclass
class EmailResult:
    emails_found: int
    relevant_emails: List[EmailData]
    invoice_numbers: List[str]
    payment_status: str

@dataclass
class BillResult:
    bills_found: int
    vendor_bills: List[BillData]
    outstanding_amount: float
    payment_status: str

@dataclass
class CRMResult:
    accounts_found: int
    account_data: List[AccountData]
    opportunities: List[OpportunityData]
    relationship_status: str

@dataclass
class AnalysisReport:
    executive_summary: str
    email_analysis: str
    billing_analysis: str
    crm_analysis: str
    payment_issues: List[str]
    recommendations: List[str]
    data_correlation: str
```

### Database Schema

```python
# MongoDB Collections

# plans collection
{
    "_id": "ObjectId",
    "plan_id": "string",
    "user_query": "string",
    "status": "pending | in_progress | completed | failed",
    "steps": [ExecutionStep],
    "created_at": "datetime",
    "updated_at": "datetime"
}

# agent_results collection
{
    "_id": "ObjectId", 
    "plan_id": "string",
    "agent_name": "string",
    "result_data": "object",
    "status": "string",
    "execution_time": "float",
    "created_at": "datetime"
}

# workflow_sessions collection
{
    "_id": "ObjectId",
    "session_id": "string", 
    "user_id": "string",
    "plans": ["string"],
    "created_at": "datetime",
    "last_activity": "datetime"
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Natural Language Query Processing
*For any* natural language query about invoice analysis, the system should process it without errors and generate a structured execution plan
**Validates: Requirements FR1.1, NFR2.1**

### Property 2: AI Planner Accuracy
*For any* invoice analysis query, the AI Planner should generate an execution plan that includes appropriate agents (Gmail, AccountsPayable, CRM, Analysis) based on the query content
**Validates: Requirements FR1.2**

### Property 3: Human Approval Workflow
*For any* generated execution plan, the system should present it for human approval and correctly handle both approval and rejection responses
**Validates: Requirements FR1.3**

### Property 4: Agent Execution Orchestration
*For any* approved execution plan, agents should execute in the planned sequence and successfully pass data between agents
**Validates: Requirements FR1.4**

### Property 5: Individual Agent Functionality
*For any* vendor name, each agent (Email, AccountsPayable, CRM) should return structured data appropriate to its domain when functioning correctly
**Validates: Requirements FR2.1, FR2.2, FR2.3**

### Property 6: Cross-System Data Integration
*For any* workflow execution, the final analysis should incorporate data from all agents that successfully returned results
**Validates: Requirements FR2.4, FR4.1**

### Property 7: Graceful Error Handling
*For any* agent failure during workflow execution, the system should continue processing with available agents and not crash the entire workflow
**Validates: Requirements FR1.5, NFR1.2, NFR1.3, NFR1.4**

### Property 8: Partial Data Analysis
*For any* workflow where some agents fail or return no data, the system should still generate a meaningful analysis report using available data
**Validates: Requirements FR2.5, FR4.4**

### Property 9: WebSocket Progress Communication
*For any* executing workflow, the WebSocket manager should send progress updates including agent status, completion percentage, and streaming content
**Validates: Requirements FR3.1, FR3.2, FR3.3**

### Property 10: Payment Issue Detection
*For any* analysis where discrepancies exist between email, AP, and CRM data, the system should identify and report these discrepancies
**Validates: Requirements FR4.2**

### Property 11: Workflow Success Rate
*For any* set of 20 or more workflow executions, at least 95% should complete successfully (either with full data or graceful partial data handling)
**Validates: Requirements NFR1.1**

### Property 12: Agent Independence
*For any* individual agent, it should be testable in isolation without requiring other agents or the full workflow orchestrator
**Validates: Requirements NFR3.1**

### Property 13: Environment-Controlled Mock Mode
*For any* agent, when `USE_MOCK_MODE=true` in environment and external services are unavailable, it should operate in mock mode and return realistic test data
**Validates: Requirements NFR3.2**

### Property 14: Comprehensive Logging
*For any* workflow execution, log messages should be generated at key decision points including agent start/completion, errors, and data flow
**Validates: Requirements NFR3.3**

### Property 15: System Extensibility
*For any* new agent implementation, it should be addable to the system configuration without modifying existing agent code
**Validates: Requirements NFR3.4**

## Error Handling

### Error Categories

#### 1. MCP Server Connection Errors
- **Scenario**: MCP server unavailable or connection timeout
- **Handling**: Only fallback to mock data when `USE_MOCK_MODE=true` in .env file
- **Recovery**: Retry logic with exponential backoff for real connections
- **User Impact**: Workflow fails if real services unavailable and mock mode disabled

#### 2. Agent Execution Errors
- **Scenario**: Individual agent throws exception during processing
- **Handling**: Log error, mark agent as failed, continue with other agents
- **Recovery**: No automatic retry for agent-level failures
- **User Impact**: Analysis generated with available data, missing data noted

#### 3. LLM Service Errors
- **Scenario**: Gemini API unavailable or rate limited
- **Handling**: Only fallback to template-based analysis when `USE_MOCK_LLM=true` in .env file
- **Recovery**: Retry with exponential backoff for transient errors
- **User Impact**: Workflow fails if LLM unavailable and mock mode disabled

#### 4. WebSocket Connection Errors
- **Scenario**: WebSocket connection drops during workflow
- **Handling**: Continue workflow execution, store messages for reconnection
- **Recovery**: Automatic reconnection with message replay
- **User Impact**: Temporary loss of real-time updates

#### 5. Database Connection Errors
- **Scenario**: MongoDB unavailable or connection timeout
- **Handling**: Workflow fails - no in-memory fallback
- **Recovery**: Automatic reconnection attempts
- **User Impact**: Workflow cannot proceed without database

### Error Recovery Strategies

```python
class ErrorHandler:
    async def handle_mcp_error(self, service: str, error: Exception) -> Optional[MockResult]:
        """Handle MCP server connection errors with environment-controlled mock fallback"""
        if os.getenv('USE_MOCK_MODE') == 'true':
            return self.generate_mock_result(service)
        else:
            raise error
    
    async def handle_agent_error(self, agent: str, error: Exception) -> AgentResult:
        """Handle individual agent errors gracefully"""
        pass
    
    async def handle_llm_error(self, error: Exception) -> Optional[str]:
        """Handle LLM service errors with environment-controlled template fallback"""
        if os.getenv('USE_MOCK_LLM') == 'true':
            return self.generate_template_analysis()
        else:
            raise error
```

## Testing Strategy

### Dual Testing Approach

The system requires both unit testing and property-based testing to ensure comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs
- Both are complementary and necessary for comprehensive coverage

### Property-Based Testing Configuration

- **Testing Library**: Hypothesis for Python property-based testing
- **Minimum Iterations**: 100 iterations per property test
- **Test Tagging**: Each property test must reference its design document property
- **Tag Format**: `# Feature: multi-agent-invoice-workflow, Property {number}: {property_text}`

### Unit Testing Focus

Unit tests should focus on:
- Specific examples that demonstrate correct behavior
- Integration points between components
- Edge cases and error conditions
- Mock data generation and validation

Property tests should focus on:
- Universal properties that hold for all inputs
- Comprehensive input coverage through randomization
- Cross-system data correlation validation
- Error handling across different failure scenarios

### Test Data Strategy

#### Vendor-Agnostic Test Framework
- **Template-Based**: Use `[VENDOR_NAME]` placeholders in test queries
- **Configurable**: Support different vendor names via configuration
- **Realistic**: Generate realistic mock data for any vendor name
- **Extensible**: Easy addition of new vendor test scenarios

#### Mock Data Generation
```python
class MockDataGenerator:
    def generate_email_data(self, vendor_name: str) -> EmailResult:
        """Generate realistic email data for any vendor"""
        pass
    
    def generate_bill_data(self, vendor_name: str) -> BillResult:
        """Generate realistic bill data for any vendor"""
        pass
    
    def generate_crm_data(self, vendor_name: str) -> CRMResult:
        """Generate realistic CRM data for any vendor"""
        pass
```

### Integration Testing

#### End-to-End Workflow Tests
- Complete workflow execution from query to final analysis
- Multi-agent coordination and data flow validation
- Human-in-the-loop approval process testing
- WebSocket message flow verification

#### Agent Integration Tests
- Individual agent integration with MCP servers
- Error handling and fallback behavior
- Data format validation between agents

### Test Execution Strategy

#### Continuous Integration
- All unit tests run on every commit
- Property tests run on pull requests
- Integration tests run on release candidates
- End-to-end tests run on deployment

#### Test Environment Management
- Isolated test databases for each test run
- Environment-controlled mock modes via .env flags
- Real MCP server connections for integration tests
- Real WebSocket connections for end-to-end tests

#### Test Reporting
- Property test failure analysis with counterexamples
- Coverage reporting for unit tests
- Integration test result dashboards
- Performance regression detection