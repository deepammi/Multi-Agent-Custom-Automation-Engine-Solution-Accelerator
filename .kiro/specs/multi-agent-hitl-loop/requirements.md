# Requirements Document: Multi-Agent Loop with Human-in-the-Loop

## Introduction

This feature enables a multi-agent workflow where specialized agents (Invoice, Closing, Audit) process tasks, and a Human-in-the-Loop (HITL) agent can request human approval or revision. If the human provides feedback, the task loops back to the Planner with retained context for re-processing. This allows for iterative refinement of agent outputs without losing the original task context.

## Glossary

- **HITL Agent**: Human-in-the-Loop agent that requests human approval or revision of specialized agent results
- **Planner Agent**: Initial agent that analyzes tasks and routes to specialized agents
- **Specialized Agent**: Invoice, Closing, or Audit agent that processes the routed task
- **Context**: The original task description and execution history maintained across loops
- **Clarification Request**: A message from HITL agent asking the human to approve or provide revision
- **Retry**: User action to resubmit a revised task back to the Planner

## Requirements

### Requirement 1

**User Story:** As a system user, I want specialized agents to route their results to a Human-in-the-Loop agent for approval, so that I can validate or revise agent outputs before completion.

#### Acceptance Criteria

1. WHEN a specialized agent completes processing THEN the system SHALL send the result to the HITL agent for review
2. WHEN the HITL agent receives a result THEN the system SHALL send a clarification request to the user asking for approval or revision
3. WHEN the user approves the result THEN the system SHALL mark the task as completed and display the final result
4. WHEN the user provides a revision THEN the system SHALL retain the original task context and send the revision back to the Planner

### Requirement 2

**User Story:** As a system user, I want to provide feedback on agent results without losing the original task context, so that I can iteratively refine the output.

#### Acceptance Criteria

1. WHEN a user provides a revision THEN the system SHALL preserve the original task description in the execution history
2. WHEN the Planner receives a revised task THEN the system SHALL have access to the previous execution history
3. WHEN the task loops back to the Planner THEN the system SHALL route to the appropriate specialized agent based on the revised task
4. WHEN multiple loops occur THEN the system SHALL maintain a complete history of all iterations

### Requirement 3

**User Story:** As a system architect, I want the HITL agent to be optional, so that simpler tasks can skip human review when not needed.

#### Acceptance Criteria

1. WHEN a task is configured to skip HITL THEN the system SHALL complete after the specialized agent finishes
2. WHEN a task is configured to require HITL THEN the system SHALL route through the HITL agent before completion
3. WHEN the HITL agent is invoked THEN the system SHALL send a clarification request message type
4. WHEN the user responds to clarification THEN the system SHALL process the response and either complete or loop back

### Requirement 4

**User Story:** As a system user, I want a clear UI for approving or revising agent results, so that I can easily provide feedback.

#### Acceptance Criteria

1. WHEN a clarification request is received THEN the system SHALL display a text input field for user response
2. WHEN the user types "OK" or similar approval THEN the system SHALL mark the task as approved
3. WHEN the user types a revision THEN the system SHALL capture the revision text
4. WHEN the user clicks the Retry button THEN the system SHALL submit the revision and loop back to the Planner
5. WHEN a clarification request is displayed THEN the system SHALL show the agent's result above the input field for context

### Requirement 5

**User Story:** As a system user, I want unlimited loop iterations, so that I can refine the output as many times as needed.

#### Acceptance Criteria

1. WHEN a user provides a revision THEN the system SHALL allow the task to loop back to the Planner
2. WHEN the Planner processes a revised task THEN the system SHALL route to the appropriate specialized agent again
3. WHEN the specialized agent completes THEN the system SHALL send the result back to the HITL agent
4. WHEN the HITL agent receives a result THEN the system SHALL send another clarification request to the user
5. WHEN a user provides multiple revisions THEN the system SHALL process each revision without limit
