# Requirements Document

## Introduction

This feature enhances the Invoice Agent to extract structured data from invoice documents using Google's LangExtract library with Gemini AI models. Instead of just analyzing invoices with free-form text responses, the agent will extract specific fields (vendor name, amount, due date, line items, etc.) into a structured format that can be validated, stored, and processed programmatically.

## Glossary

- **LangExtract**: Google's library for extracting structured data from unstructured text using LLMs
- **Gemini**: Google's family of AI models (Gemini Pro, Gemini Flash)
- **Structured Extraction**: Converting unstructured invoice text into structured data with defined fields
- **Invoice Schema**: A Pydantic model defining the expected structure of invoice data
- **Extraction Pipeline**: The workflow that takes invoice text and returns structured data
- **Validation**: Checking that extracted data meets business rules and constraints

## Requirements

### Requirement 1

**User Story:** As a user, I want to upload or paste invoice text and get structured data extracted, so that I can validate and process invoice information programmatically.

#### Acceptance Criteria

1. WHEN a user provides invoice text THEN the system SHALL extract structured fields using LangExtract
2. WHEN extraction completes THEN the system SHALL return data in a defined schema with vendor, amount, date, and line items
3. WHEN the invoice text is incomplete THEN the system SHALL mark missing fields as null or empty
4. WHEN extraction fails THEN the system SHALL return a clear error message with the reason
5. WHEN structured data is returned THEN the system SHALL include confidence scores for extracted fields

### Requirement 2

**User Story:** As a developer, I want to use Gemini AI models for extraction, so that I can leverage Google's latest AI capabilities for invoice processing.

#### Acceptance Criteria

1. WHEN the system initializes THEN it SHALL configure LangExtract with Gemini Flash
2. WHEN a Gemini API key is provided THEN the system SHALL authenticate with Google's AI services
3. WHEN the Gemini model is unavailable THEN the system SHALL fall back to OpenAI or return an error

### Requirement 3

**User Story:** As a user, I want the extracted invoice data to follow a consistent schema, so that I can integrate it with my accounting systems.

#### Acceptance Criteria

1. WHEN defining the invoice schema THEN the system SHALL include vendor name, invoice number, date, due date, total amount, and line items
2. WHEN extracting line items THEN the system SHALL capture description, quantity, unit price, and total for each item
3. WHEN extracting dates THEN the system SHALL parse them into ISO 8601 format
4. WHEN extracting amounts THEN the system SHALL parse them as decimal numbers with currency
5. WHEN the schema is defined THEN it SHALL be extensible for custom fields

### Requirement 4

**User Story:** As a user, I want validation rules applied to extracted data, so that I can catch errors and inconsistencies automatically.

#### Acceptance Criteria

1. WHEN line items are extracted THEN the system SHALL verify that line totals sum to the invoice total
2. WHEN dates are extracted THEN the system SHALL verify that due date is after invoice date
3. WHEN amounts are extracted THEN the system SHALL verify they are positive numbers
4. WHEN required fields are missing THEN the system SHALL flag the invoice for manual review
5. WHEN validation fails THEN the system SHALL provide specific error messages for each issue

### Requirement 5

**User Story:** As a user, I want to see both the structured data and the original analysis, so that I have context for the extracted information.

#### Acceptance Criteria

1. WHEN extraction completes THEN the system SHALL return both structured data and a natural language summary
2. WHEN displaying results THEN the system SHALL show extracted fields in a formatted table
3. WHEN validation issues exist THEN the system SHALL highlight them in the response
4. WHEN confidence is low THEN the system SHALL indicate which fields need verification
5. WHEN the user requests it THEN the system SHALL provide the raw extraction response

### Requirement 6

**User Story:** As a developer, I want to handle different invoice formats, so that the system works with various vendor invoice styles.

#### Acceptance Criteria

1. WHEN processing invoices THEN the system SHALL handle plain text formats
2. WHEN invoice format varies THEN the system SHALL adapt extraction based on detected structure
3. WHEN multiple currencies are present THEN the system SHALL extract and identify each currency
4. WHEN invoices have multiple pages THEN the system SHALL combine information across pages
5. WHEN invoice language varies THEN the system SHALL extract data from English invoices initially

### Requirement 7

**User Story:** As a user, I want extraction results stored with the plan, so that I can review and export structured invoice data later.

#### Acceptance Criteria

1. WHEN extraction completes THEN the system SHALL store structured data in the database
2. WHEN storing data THEN the system SHALL link it to the plan_id for retrieval
3. WHEN the user views a plan THEN the system SHALL display the extracted structured data
4. WHEN exporting data THEN the system SHALL provide JSON and CSV formats
5. WHEN data is stored THEN the system SHALL include extraction timestamp and model used

### Requirement 8

**User Story:** As a developer, I want to configure extraction behavior, so that I can optimize for speed, cost, or accuracy based on use case.

#### Acceptance Criteria

1. WHEN configuring extraction THEN the system SHALL allow selection between Gemini Flash (fast) and OpenAI GPT-4o-mini (accurate)
2. WHEN configuring extraction THEN the system SHALL allow setting temperature for creativity vs consistency
3. WHEN configuring extraction THEN the system SHALL allow enabling/disabling validation rules
4. WHEN configuring extraction THEN the system SHALL allow custom schema extensions
5. WHEN configuration changes THEN the system SHALL apply them without requiring code changes

### Requirement 9

**User Story:** As a user, I want to test multiple invoices in sequence through the UI, so that I can validate the extraction system with various invoice formats efficiently.

#### Acceptance Criteria

1. WHEN a user submits an invoice for extraction THEN the system SHALL process it and display results in the UI
2. WHEN extraction completes THEN the system SHALL allow the user to submit another invoice without refreshing
3. WHEN multiple invoices are processed THEN the system SHALL maintain a history of recent extractions in the session
4. WHEN viewing extraction history THEN the system SHALL display invoice number, vendor, and extraction status for each
5. WHEN a user selects a previous extraction THEN the system SHALL display the full details and validation results

### Requirement 10

**User Story:** As a user, I want to see validation results clearly in the UI, so that I can quickly identify and fix issues with extracted invoice data.

#### Acceptance Criteria

1. WHEN validation errors exist THEN the system SHALL display them prominently with error severity indicators
2. WHEN validation warnings exist THEN the system SHALL display them with warning severity indicators
3. WHEN validation info messages exist THEN the system SHALL display them with info severity indicators
4. WHEN displaying validation issues THEN the system SHALL group them by severity (errors, warnings, info)
5. WHEN a validation issue is shown THEN the system SHALL include the rule name and specific field affected
