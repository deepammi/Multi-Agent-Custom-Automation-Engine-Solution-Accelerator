# LangGraph Orchestrator Simplification Requirements

## Introduction

This specification addresses the infinite loop issue in the current multi-agent LangGraph implementation by converting from complex conditional routing to LangGraph's built-in linear orchestrator pattern. The system will support two workflow types with Human-in-the-Loop (HITL) approval at key stages.

## Glossary

- **LangGraph**: Open-source framework for building multi-agent workflows with state management
- **Linear Workflow**: Sequential execution pattern where each agent runs exactly once in a predefined order
- **AI-Driven Workflow**: Intelligent agent sequence generation using GenAI within the Planner
- **GenAI Agent**: AI component within Planner that analyzes tasks and suggests optimal agent sequences
- **HITL (Human-in-the-Loop)**: Human approval points in the workflow for plan approval and result validation
- **Agent Sequence**: Ordered list of agents that will execute for a specific workflow
- **Planner Agent**: Initial agent that analyzes tasks and creates execution plans
- **Supervisor Router**: Current custom routing function that causes infinite loops (to be removed)

## Requirements

### Requirement 1: AI-Driven Workflow Generation

**User Story:** As a business user, I want the system to intelligently generate optimal agent sequences for any task, so that I don't need predefined workflow templates.

#### Acceptance Criteria

1. THE System SHALL use a GenAI Agent within the Planner to analyze all incoming tasks
2. THE GenAI Agent SHALL generate optimal agent sequences based on task analysis
3. WHEN a task is submitted, THE Planner SHALL create a custom agent sequence using AI reasoning
4. THE System SHALL present the AI-generated sequence with explanations to HITL
5. THE System SHALL allow HITL to approve or modify the suggested sequence before execution

### Requirement 2: Human-in-the-Loop Approval Process

**User Story:** As a business user, I want to approve the execution plan before agents run and approve the final results, so that I maintain control over the automation process.

#### Acceptance Criteria

1. WHEN Planner creates an agent sequence, THE System SHALL present the plan to HITL for approval
2. WHEN HITL approves the plan, THE System SHALL execute agents in the predetermined sequence
3. WHEN all agents complete, THE System SHALL present final results to HITL for approval
4. WHEN HITL rejects a plan, THE System SHALL terminate the workflow without execution
5. THE System SHALL NOT execute any agents without explicit HITL approval of the plan

### Requirement 3: Linear Agent Execution

**User Story:** As a developer, I want agents to execute in a strict linear sequence, so that infinite loops are impossible and execution is predictable.

#### Acceptance Criteria

1. WHEN a workflow is approved, THE System SHALL execute agents in the exact predetermined sequence
2. WHEN an agent completes, THE System SHALL automatically proceed to the next agent in sequence
3. WHEN the final agent completes, THE System SHALL terminate the workflow automatically
4. THE System SHALL execute each agent exactly once per workflow instance
5. THE System SHALL NOT allow agents to modify the execution sequence during runtime

### Requirement 4: Supervisor Router Elimination

**User Story:** As a system maintainer, I want to remove all conditional routing logic, so that routing cannot cause infinite loops.

#### Acceptance Criteria

1. THE System SHALL eliminate the supervisor_router function completely
2. THE System SHALL use LangGraph's add_edge() method for all agent connections
3. THE System SHALL remove all next_agent routing logic from agent implementations
4. THE System SHALL remove workflow_type conditional routing from the graph
5. THE System SHALL use static graph structures defined at creation time

### Requirement 5: AI-Driven Agent Sequence Planning

**User Story:** As a business user, I want an AI agent within the Planner to intelligently suggest optimal agent sequences, so that I don't need predefined workflows with hardcoded logic.

#### Acceptance Criteria

1. WHEN Planner receives a task, THE System SHALL use a GenAI Agent to analyze task requirements
2. THE GenAI Agent SHALL suggest an optimal sequence of agents based on task content and context
3. THE GenAI Agent SHALL select from available agents: Gmail, Invoice, Salesforce, Zoho, Audit, Closing, Analysis
4. THE System SHALL present the AI-suggested sequence to HITL with reasoning for each agent selection
5. THE System SHALL allow HITL to modify the suggested sequence before approval

### Requirement 6: Intelligent Workflow Adaptation

**User Story:** As a business user, I want the AI Planner to adapt to different business scenarios without requiring code changes, so that new workflow types can be handled automatically.

#### Acceptance Criteria

1. THE GenAI Agent SHALL analyze task complexity, required data sources, and business context
2. WHEN analyzing PO investigations, THE GenAI Agent SHALL typically suggest: Gmail → Invoice → Salesforce → Analysis
3. WHEN analyzing simple queries, THE GenAI Agent SHALL suggest minimal agent sequences
4. THE GenAI Agent SHALL provide reasoning for why each agent is included in the sequence
5. THE System SHALL learn from HITL modifications to improve future sequence suggestions

### Requirement 7: State Management Simplification

**User Story:** As a developer, I want simplified state management that supports linear execution, so that the system is maintainable and debuggable.

#### Acceptance Criteria

1. THE System SHALL remove next_agent field from AgentState
2. THE System SHALL preserve collected_data for cross-agent data sharing
3. THE System SHALL maintain execution_plan for progress tracking
4. THE System SHALL use current_step for linear progression tracking
5. THE System SHALL eliminate all dynamic routing state variables

### Requirement 8: Basic Error Handling

**User Story:** As a system operator, I want basic error handling that prevents system instability, so that failures are managed gracefully.

#### Acceptance Criteria

1. WHEN an agent fails, THE System SHALL terminate the workflow and notify HITL
2. THE System SHALL log agent failures with basic error information
3. THE System SHALL provide clear error messages via WebSocket
4. THE System SHALL maintain system stability when workflows fail
5. THE System SHALL NOT attempt automatic retries or recovery

### Requirement 9: Basic Performance Management

**User Story:** As a system administrator, I want basic performance controls, so that workflows don't consume excessive resources.

#### Acceptance Criteria

1. THE System SHALL limit workflow execution time to 15 minutes maximum
2. THE System SHALL complete typical workflows within 5 minutes
3. THE System SHALL release resources when workflows complete or timeout
4. THE System SHALL prevent more than 10 concurrent workflows per user
5. THE System SHALL log basic execution duration for monitoring

### Requirement 10: Basic Observability

**User Story:** As a developer, I want basic visibility into workflow execution, so that I can debug issues when they occur.

#### Acceptance Criteria

1. THE System SHALL log workflow start, agent transitions, and completion
2. THE System SHALL provide workflow status through WebSocket messages
3. THE System SHALL maintain basic execution history for completed workflows
4. THE System SHALL log errors with agent name and timestamp
5. THE System SHALL provide workflow progress updates to HITL during execution