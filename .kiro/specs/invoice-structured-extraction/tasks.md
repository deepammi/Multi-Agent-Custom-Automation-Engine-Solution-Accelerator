# Implementation Plan - Phased Approach

This implementation is organized into testable phases. Each phase ends with a checkpoint where you can test the components before moving forward.

## Phase 1: Data Models & Validation (Standalone Testing)

**Goal**: Create and test data models and validation rules independently

- [x] 1.1. Install dependencies
  - Add langextract and google-generativeai to requirements.txt
  - Create validation_rules.json configuration file
  - _Requirements: 2.1, 8.1_

- [ ] 1.2. Create invoice data models
  - Create backend/app/models/__init__.py
  - Create backend/app/models/invoice_schema.py
  - Define InvoiceLineItem Pydantic model
  - Define InvoiceData Pydantic model
  - Define ExtractionResult model
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 1.3. Create validation rules configuration
  - Create backend/app/config/__init__.py
  - Create backend/app/config/validation_rules.py
  - Define ValidationSeverity enum
  - Define ValidationRule model
  - Implement ValidationRulesConfig class with 10 rules
  - Add enable/disable methods
  - Add load_from_env() and load_from_config_file()
  - _Requirements: 4.1, 4.2, 4.3, 8.2, 8.3, 8.5_

- [ ] 1.4. Implement invoice validator
  - Add InvoiceValidator class to validation_rules.py
  - Implement validate() method
  - Implement _run_rule() for all 10 validation rules
  - Implement _add_issue() for severity handling
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 1.5. **CHECKPOINT**: Test data models and validation
  - Create test script to validate InvoiceData model
  - Test validation rules with sample data
  - Test enable/disable functionality
  - Test loading from JSON config
  - **Verify**: Models work, validation rules trigger correctly

## Phase 2: LangExtract Service (Mock Testing)

**Goal**: Create LangExtract service and test with mock data

- [ ] 2.1. Create LangExtract service skeleton
  - Create backend/app/services/langextract_service.py
  - Implement LangExtractService class structure
  - Add get_few_shot_examples() with 2+ examples
  - Add placeholder for initialize() method
  - _Requirements: 2.1, 8.1_

- [ ] 2.2. Implement Gemini initialization
  - Implement initialize() method with Gemini config
  - Add get_extractor() method
  - Handle API key validation
  - Add error handling for missing config
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 2.3. Implement extraction logic
  - Add extract_invoice_data() async method
  - Integrate with LangExtract
  - Apply InvoiceValidator after extraction
  - Return ExtractionResult with metadata
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 2.4. Add extraction formatting
  - Implement format_extraction_result() method
  - Format structured data as readable text
  - Include validation errors/warnings
  - Show confidence scores
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 2.5. **CHECKPOINT**: Test LangExtract service
  - Create test script with sample invoice text
  - Test with mock Gemini responses (if no API key)
  - Test with real Gemini API (if API key available)
  - Test validation integration
  - Test formatting output
  - **Verify**: Extraction works, validation applies, output formats correctly

## Phase 3: Invoice Detection & Agent Integration (No Database Yet)

**Goal**: Integrate extraction into Invoice Agent without database storage

- [ ] 3.1. Add invoice detection logic
  - Create detect_invoice_text() function in agents/nodes.py
  - Use keywords/patterns to identify invoices
  - Return boolean for extraction decision
  - _Requirements: 1.1_

- [ ] 3.2. Update AgentState
  - Add extraction_result field to backend/app/agents/state.py
  - Add requires_extraction_approval field
  - Add extraction_approved field
  - Update type hints
  - _Requirements: 1.1_

- [ ] 3.3. Update Invoice Agent node (basic)
  - Modify invoice_agent_node() in backend/app/agents/nodes.py
  - Add invoice detection check
  - Call LangExtractService for invoice text
  - Store extraction_result in state (not database)
  - Set requires_extraction_approval flag
  - Keep backward compatibility
  - _Requirements: 1.1, 1.2, 5.1_

- [ ] 3.4. **CHECKPOINT**: Test agent integration
  - Submit invoice text via agent
  - Verify extraction runs
  - Verify result stored in state
  - Verify non-invoice tasks still work
  - Check logs for extraction messages
  - **Verify**: Agent detects invoices, extracts data, maintains compatibility

## Phase 4: HITL Approval Workflow (Without Frontend)

**Goal**: Implement approval workflow, test via API/logs

- [ ] 4.1. Implement HITL approval handlers
  - Add send_extraction_approval_request() to agent_service.py
  - Add handle_extraction_approval() to agent_service.py
  - Send extraction as JSON via WebSocket
  - Handle approval/rejection
  - _Requirements: 7.1, 7.2_

- [ ] 4.2. Add API endpoint for extraction approval
  - Create POST /api/v3/extraction_approval in routes.py
  - Accept approval/rejection with feedback
  - Call handle_extraction_approval()
  - Return confirmation
  - _Requirements: 7.1_

- [ ] 4.3. **CHECKPOINT**: Test HITL workflow
  - Submit invoice task
  - Check WebSocket for approval request
  - Send approval via API endpoint
  - Verify workflow completes
  - Test rejection flow
  - **Verify**: Approval requests sent, responses handled correctly

## Phase 5: Database Storage & Export

**Goal**: Add persistence after approval

- [ ] 5.1. Create database repository
  - Add InvoiceExtractionRepository to backend/app/db/repositories.py
  - Implement store_extraction() method
  - Implement get_extraction() method
  - _Requirements: 7.1, 7.2, 7.3, 7.5_

- [ ] 5.2. Integrate storage with approval
  - Update handle_extraction_approval() to store on approval
  - Add approved_at timestamp
  - Test storage only happens after approval
  - _Requirements: 7.1, 7.2_

- [ ] 5.3. Add export functionality
  - Implement export_extraction_json() method
  - Implement export_extraction_csv() method
  - Create GET /api/v3/extraction/{plan_id}/json endpoint
  - Create GET /api/v3/extraction/{plan_id}/csv endpoint
  - _Requirements: 7.4_

- [ ] 5.4. **CHECKPOINT**: Test database and export
  - Submit and approve invoice extraction
  - Verify data stored in MongoDB
  - Test JSON export endpoint
  - Test CSV export endpoint
  - Verify rejected extractions not stored
  - **Verify**: Storage works, exports work, approval gates storage

## Phase 6: Configuration & Environment

**Goal**: Make everything configurable

- [ ] 6.1. Update environment configuration
  - Add GEMINI_API_KEY to .env.example
  - Add GEMINI_MODEL, GEMINI_TEMPERATURE
  - Add ENABLE_STRUCTURED_EXTRACTION flag
  - Add EXTRACTION_VALIDATION flag
  - Add EXTRACTION_REQUIRES_APPROVAL flag
  - Add validation rule overrides
  - _Requirements: 2.1, 8.1, 8.2, 8.5_

- [ ] 6.2. Create initialization logic
  - Load validation rules on startup
  - Initialize LangExtract service
  - Log configuration status
  - _Requirements: 2.1, 8.5_

- [ ] 6.3. **CHECKPOINT**: Test configuration
  - Test with different Gemini models
  - Test enabling/disabling validation rules
  - Test feature flags
  - Test environment variable overrides
  - **Verify**: All configuration options work

## Phase 7: Testing & Documentation

**Goal**: Comprehensive testing and docs

- [ ] 7.1. Create test invoice samples
  - Create sample invoice texts
  - Include various formats
  - Include edge cases
  - _Requirements: 6.1_

- [ ] 7.2. Write unit tests
  - Test validation rules
  - Test data models
  - Test extraction service
  - Test formatting
  - _Requirements: All_

- [ ] 7.3. Write integration tests
  - Test end-to-end flow
  - Test HITL workflow
  - Test database storage
  - Test exports
  - _Requirements: All_

- [ ] 7.4. Create documentation
  - Document LangExtract integration
  - Document validation rules system
  - Document how to add custom rules
  - Document HITL workflow
  - Create Gemini API setup guide
  - _Requirements: All_

- [ ] 7.5. **CHECKPOINT**: Manual end-to-end test
  - Test with real Gemini API
  - Test complete workflow
  - Test all validation rules
  - Test exports
  - **Verify**: Everything works end-to-end

## Phase 8: Final Integration

**Goal**: Polish and production-ready

- [ ] 8.1. Performance testing
  - Test extraction speed
  - Test with large invoices
  - Optimize if needed
  - _Requirements: All_

- [ ] 8.2. Error handling review
  - Test all error scenarios
  - Verify error messages are clear
  - Test fallback behaviors
  - _Requirements: 1.4, 1.5_

- [ ] 8.3. **FINAL CHECKPOINT**: Production readiness
  - All tests passing
  - Documentation complete
  - Configuration verified
  - Performance acceptable
  - **Verify**: Ready for production use

---

## Testing Strategy Per Phase

### Phase 1 Test Script
```python
# Test data models and validation
from app.models.invoice_schema import InvoiceData, InvoiceLineItem
from app.config.validation_rules import InvoiceValidator

# Create sample invoice
invoice = InvoiceData(...)
validator = InvoiceValidator(invoice)
result = validator.validate()
print(result)
```

### Phase 2 Test Script
```python
# Test LangExtract service
from app.services.langextract_service import LangExtractService

invoice_text = "INVOICE..."
result = await LangExtractService.extract_invoice_data(invoice_text, "test-123")
print(result)
```

### Phase 3 Test Script
```bash
# Test via API
curl -X POST http://localhost:8000/api/v3/process_request \
  -d '{"description": "INVOICE\nAcme Corp\n..."}'
```

### Phase 4 Test Script
```bash
# Test approval
curl -X POST http://localhost:8000/api/v3/extraction_approval \
  -d '{"plan_id": "...", "approved": true}'
```

### Phase 5 Test Script
```bash
# Test export
curl http://localhost:8000/api/v3/extraction/{plan_id}/json
```
