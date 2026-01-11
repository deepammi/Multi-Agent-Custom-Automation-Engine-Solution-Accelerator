# Requirements Document: Multi-Agent Loop with Human-in-the-Loop

## Introduction

This feature enables a comprehensive multi-agent workflow with frontend integration where users can initiate tasks through the web interface, receive dual Human-in-the-Loop (HITL) approval points, and view detailed results. The system includes: (1) frontend query submission, (2) Planner Agent HITL approval before executing specialized agents, and (3) comprehensive final results presentation with verbose output for final HITL approval. This allows for complete user control over multi-agent execution with full visibility into the process.

## Glossary

- **HITL Agent**: Human-in-the-Loop agent that requests human approval or revision of agent results
- **Planner Agent**: Initial agent that analyzes tasks and creates execution plans for specialized agents
- **Specialized Agent**: Gmail, Accounts Payable, CRM, or Analysis agent that processes specific aspects of the task
- **Context**: The original task description and execution history maintained across loops
- **Clarification Request**: A message from HITL agent asking the human to approve or provide revision
- **Plan Approval**: First HITL checkpoint where user approves the Planner's execution plan before agents run
- **Final Results Approval**: Second HITL checkpoint where user reviews comprehensive agent results
- **Comprehensive Testing**: End-to-end workflow testing with real MCP servers and full agent coordination
- **Frontend Integration**: Web interface components that handle user input, plan display, and results presentation
- **Verbose Output**: Detailed results from all agents including data sources, analysis, and correlations

## Requirements

### Requirement 1: Frontend Query Submission

**User Story:** As a system user, I want to type my query in the frontend interface to initiate comprehensive multi-agent testing, so that I can easily start complex workflows through the web interface.

#### Acceptance Criteria

1. WHEN a user types a query in the frontend input field THEN the system SHALL accept the query and initiate the workflow
2. WHEN the query is submitted THEN the system SHALL send it to the Planner Agent for analysis
3. WHEN the frontend receives a workflow start confirmation THEN the system SHALL display the plan creation progress
4. WHEN the Planner Agent completes analysis THEN the system SHALL display the proposed execution plan
5. WHEN the plan is displayed THEN the system SHALL show which agents will be executed and in what order

### Requirement 2: Planner Agent HITL Approval

**User Story:** As a system user, I want to approve the Planner Agent's execution plan before individual agents start running, so that I can control which agents execute and modify the plan if needed.

#### Acceptance Criteria

1. WHEN the Planner Agent creates an execution plan THEN the system SHALL pause execution and request human approval
2. WHEN a plan approval request is sent THEN the system SHALL display the complete plan with agent sequence and estimated duration
3. WHEN the user approves the plan THEN the system SHALL proceed to execute the specialized agents in sequence
4. WHEN the user rejects the plan THEN the system SHALL allow plan modification or task cancellation
5. WHEN plan approval is pending THEN the system SHALL prevent agent execution until approval is received

### Requirement 3: Comprehensive Multi-Agent Execution

**User Story:** As a system user, I want to see all specialized agents (Gmail, Accounts Payable, CRM, Analysis) execute in coordination, so that I can observe the complete multi-agent workflow in action.

#### Acceptance Criteria

1. WHEN the plan is approved THEN the system SHALL execute Gmail, Accounts Payable, and CRM agents in sequence
2. WHEN each agent executes THEN the system SHALL display real-time progress and streaming results
3. WHEN an agent completes THEN the system SHALL show the agent's results and proceed to the next agent
4. WHEN all data-gathering agents complete THEN the system SHALL execute the Analysis agent to correlate results
5. WHEN any agent encounters an error THEN the system SHALL display the error and allow user intervention

### Requirement 4: Verbose Results Presentation

**User Story:** As a system user, I want to see comprehensive, verbose results from all agents including data sources, analysis, and correlations, so that I can understand the complete findings before final approval.

#### Acceptance Criteria

1. WHEN all agents complete execution THEN the system SHALL compile comprehensive results from all agents
2. WHEN results are compiled THEN the system SHALL display detailed output including data from each source system
3. WHEN results are displayed THEN the system SHALL show data correlations and cross-references between systems
4. WHEN the Analysis agent completes THEN the system SHALL present the final analysis with executive summary and recommendations
5. WHEN verbose results are shown THEN the system SHALL include metadata about data quality, service usage, and execution metrics

### Requirement 5: Final Results HITL Approval

**User Story:** As a system user, I want to review and approve the final comprehensive results before the workflow completes, so that I can validate the analysis and request modifications if needed.

#### Acceptance Criteria

1. WHEN comprehensive results are ready THEN the system SHALL pause and request final human approval
2. WHEN final approval is requested THEN the system SHALL display all agent results, analysis, and recommendations
3. WHEN the user approves the final results THEN the system SHALL mark the workflow as completed
4. WHEN the user requests modifications THEN the system SHALL allow feedback and loop back to appropriate agents
5. WHEN final approval is pending THEN the system SHALL maintain all results in an editable state for potential revision

### Requirement 6

**User Story:** As a system user, I want specialized agents to route their results to a Human-in-the-Loop agent for approval, so that I can validate or revise agent outputs before completion.

#### Acceptance Criteria

1. WHEN a specialized agent completes processing THEN the system SHALL send the result to the HITL agent for review
2. WHEN the HITL agent receives a result THEN the system SHALL send a clarification request to the user asking for approval or revision
3. WHEN the user approves the result THEN the system SHALL mark the task as completed and display the final result
4. WHEN the user provides a revision THEN the system SHALL retain the original task context and send the revision back to the Planner

### Requirement 7

**User Story:** As a system user, I want to provide feedback on agent results without losing the original task context, so that I can iteratively refine the output.

#### Acceptance Criteria

1. WHEN a user provides a revision THEN the system SHALL preserve the original task description in the execution history
2. WHEN the specialized agent receives a revised task THEN the system SHALL have access to the previous execution history and original task context
3. WHEN the task loops back to the specialized agent THEN the system SHALL process the revision with full context awareness
4. WHEN multiple loops occur THEN the system SHALL maintain a complete history of all iterations

### Requirement 8

**User Story:** As a system architect, I want the HITL agent to be optional, so that simpler tasks can skip human review when not needed.

#### Acceptance Criteria

1. WHEN a task is configured to skip HITL THEN the system SHALL complete after the specialized agent finishes
2. WHEN a task is configured to require HITL THEN the system SHALL route through the HITL agent before completion
3. WHEN the HITL agent is invoked THEN the system SHALL send a clarification request message type
4. WHEN the user responds to clarification THEN the system SHALL process the response and either complete or loop back

### Requirement 9

**User Story:** As a system user, I want a clear UI for approving or revising agent results, so that I can easily provide feedback.

#### Acceptance Criteria

1. WHEN a clarification request is received THEN the system SHALL display a text input field for user response
2. WHEN the user types "OK" or similar approval THEN the system SHALL mark the task as approved
3. WHEN the user types a revision THEN the system SHALL capture the revision text
4. WHEN the user clicks the Retry button THEN the system SHALL submit the revision and loop back to the Planner
5. WHEN a clarification request is displayed THEN the system SHALL show the agent's result above the input field for context

### Requirement 10

**User Story:** As a system user, I want unlimited loop iterations, so that I can refine the output as many times as needed.

#### Acceptance Criteria

1. WHEN a user provides a revision THEN the system SHALL allow the task to loop back to the Planner
2. WHEN the Planner processes a revised task THEN the system SHALL route to the appropriate specialized agent again
3. WHEN the specialized agent completes THEN the system SHALL send the result back to the HITL agent
4. WHEN the HITL agent receives a result THEN the system SHALL send another clarification request to the user
5. WHEN a user provides multiple revisions THEN the system SHALL process each revision without limit
