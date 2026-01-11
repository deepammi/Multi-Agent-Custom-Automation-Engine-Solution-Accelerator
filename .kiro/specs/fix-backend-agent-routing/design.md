# Design Document

## Overview

This design addresses the critical backend routing issue where user queries are bypassing the Planner agent and going directly to domain-specific agents. The fix ensures all tasks follow the intended multi-agent workflow: Planner → Domain Agents → Analysis.

## Architecture

### Current Problematic Flow
```
User Task → AI Planner Service → [email, invoice, crm, analysis] → Direct Execution
```

### Fixed Flow
```
User Task → AI Planner Service → [planner, domain_agents, analysis] → Planner Analysis → Domain Execution
```

## Components and Interfaces

### AI Planner Service Updates

**File**: `backend/app/services/ai_planner_service.py`

**Changes Required**:
1. Add "planner" to `available_agents` list
2. Add planner capabilities to `agent_capabilities` mapping
3. Update sequence generation to always start with "planner"
4. Update fallback logic to include planner agent

### Agent Capabilities Mapping

**New Planner Agent Definition**:
```python
"planner": "Task analysis, plan creation, and agent coordination. Analyzes user requests, decomposes them into actionable steps, and determines the optimal sequence of specialized agents to execute."
```

### Sequence Generation Logic

**Updated Agent Sequence Pattern**:
- **Simple Tasks**: `["planner", "domain_agent"]`
- **Medium Tasks**: `["planner", "domain_agent1", "domain_agent2", "analysis"]`
- **Complex Tasks**: `["planner", "domain_agent1", "domain_agent2", "domain_agent3", "analysis"]`

## Data Models

### AgentSequence Updates

No changes required to the `AgentSequence` model structure. The model already supports variable-length agent lists.

### TaskAnalysis Updates

No changes required to the `TaskAnalysis` model. The existing fields support planner agent integration.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Planner-First Routing
*For any* user task submission, the generated agent sequence should always start with the "planner" agent as the first element.
**Validates: Requirements 1.1, 2.1**

### Property 2: Agent Availability Consistency
*For any* AI Planner service instance, the available_agents list should contain "planner" and the agent_capabilities mapping should include planner capabilities.
**Validates: Requirements 1.3, 3.1, 3.2**

### Property 3: Fallback Sequence Integrity
*For any* fallback sequence generation, the resulting sequence should include "planner" as the first agent regardless of the task type or failure reason.
**Validates: Requirements 2.5, 4.2**

### Property 4: Sequence Validation
*For any* generated agent sequence, validation should confirm that "planner" is present and positioned as the first agent before allowing execution.
**Validates: Requirements 2.4, 4.4**

### Property 5: Mock Mode Consistency
*For any* mock mode execution, the generated sequences should follow the same planner-first pattern as production mode.
**Validates: Requirements 4.3, 6.4**

## Error Handling

### AI Planner Service Errors

**Sequence Generation Failures**:
- If LLM fails to generate sequence, fallback to `["planner", "analysis"]`
- Log the failure and include planner agent in recovery sequence
- Ensure planner agent is never omitted from error recovery

**Agent Validation Errors**:
- Validate that "planner" is first in all generated sequences
- Reject sequences that don't start with planner agent
- Log validation failures for debugging

### Backward Compatibility

**Existing Agent Support**:
- Maintain support for all existing domain agents
- Preserve existing agent capabilities and interfaces
- Ensure no breaking changes to agent execution logic

## Testing Strategy

### Unit Tests

**AI Planner Service Tests**:
- Test that available_agents includes "planner"
- Test that agent_capabilities includes planner definition
- Test sequence generation always starts with "planner"
- Test fallback sequences include planner agent

**Sequence Validation Tests**:
- Test validation rejects sequences without planner
- Test validation accepts valid planner-first sequences
- Test error handling for invalid sequences

### Integration Tests

**End-to-End Workflow Tests**:
- Test complete task execution with planner-first routing
- Test WebSocket message flow with planner agent
- Test database persistence with planner agent sequences

**Mock Mode Tests**:
- Test mock sequences follow planner-first pattern
- Test mock planner agent capabilities
- Test mock fallback behavior

### Property-Based Tests

**Sequence Generation Properties**:
- Property test: all generated sequences start with "planner"
- Property test: fallback sequences always include planner
- Property test: agent validation correctly identifies planner-first sequences

**Configuration Properties**:
- Property test: available_agents always contains "planner"
- Property test: agent_capabilities always includes planner definition

## Implementation Plan

### Phase 1: AI Planner Service Updates
1. Update `available_agents` list to include "planner"
2. Add planner capabilities to `agent_capabilities` mapping
3. Update sequence generation prompts to emphasize planner-first routing

### Phase 2: Sequence Generation Logic
1. Modify `_create_sequence_prompt()` to require planner as first agent
2. Update `_parse_sequence_response()` to validate planner-first sequences
3. Update fallback logic in `get_fallback_sequence()` to include planner

### Phase 3: Mock Mode Updates
1. Update `_get_mock_sequence()` to always start with planner
2. Update `_get_mock_analysis()` to include planner in estimated agents
3. Ensure mock mode follows same routing patterns as production

### Phase 4: Testing and Validation
1. Add unit tests for updated AI Planner service
2. Add integration tests for planner-first routing
3. Add property-based tests for sequence validation
4. Verify backward compatibility with existing functionality

### Phase 5: Deployment and Monitoring
1. Deploy changes with comprehensive logging
2. Monitor agent sequence generation in production
3. Verify planner agent is being used in all task executions
4. Add alerts for any sequences that bypass planner agent