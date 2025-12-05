# Requirements Document

## Introduction

This feature addresses a critical bug in the invoice extraction workflow where the frontend times out waiting for the Invoice Agent's response. The issue occurs because the Invoice Agent node returns with an extraction approval request without first sending its agent message via WebSocket, causing the frontend to never receive the expected agent message and resulting in a 30-second spinner timeout.

## Glossary

- **Invoice Agent**: The specialized agent responsible for processing invoice-related tasks and performing structured data extraction
- **WebSocket Manager**: The service responsible for sending real-time messages to the frontend
- **Extraction Approval Request**: A message sent to the frontend requesting user approval of extracted invoice data
- **Agent Message**: A message sent from an agent to the frontend indicating the agent's current processing status
- **Spinner Timeout**: A 30-second timeout in the frontend that hides the loading spinner if no response is received

## Requirements

### Requirement 1

**User Story:** As a user submitting an invoice for extraction, I want to see the Invoice Agent's processing message before the extraction approval dialog, so that I understand the system is working and don't experience a timeout.

#### Acceptance Criteria

1. WHEN the Invoice Agent detects invoice text requiring extraction THEN the system SHALL send an agent message via WebSocket before initiating extraction
2. WHEN the Invoice Agent completes extraction THEN the system SHALL send the extraction approval request only after the agent message has been sent
3. WHEN the frontend receives messages THEN the system SHALL ensure agent messages appear in chronological order before extraction approval requests
4. WHEN extraction is initiated THEN the system SHALL include the agent name "Invoice" in all WebSocket messages
5. WHEN the extraction approval request is sent THEN the system SHALL ensure the frontend has already received and displayed the Invoice Agent's processing message

### Requirement 2

**User Story:** As a developer debugging the invoice extraction flow, I want clear logging of message sending order, so that I can verify the correct sequence of events.

#### Acceptance Criteria

1. WHEN the Invoice Agent sends a message THEN the system SHALL log the message type and timestamp
2. WHEN extraction approval is requested THEN the system SHALL log that the agent message was sent first
3. WHEN messages are sent via WebSocket THEN the system SHALL log the plan_id and message type for each transmission
4. WHEN the extraction process completes THEN the system SHALL log the total time taken and success status
