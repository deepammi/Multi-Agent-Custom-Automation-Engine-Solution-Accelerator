# Design Document

## Overview

This design document outlines the integration of Google's LangExtract library with Gemini AI models to add structured data extraction capabilities to the Invoice Agent. The solution will extract specific fields (vendor, amounts, dates, line items) from unstructured invoice text and return them in a validated, structured format suitable for programmatic processing and integration with accounting systems.

The design follows the existing LangGraph multi-agent architecture and extends the Invoice Agent with extraction capabilities while maintaining backward compatibility with the current text-based analysis.

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│   Frontend      │
│   (React)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │
│   Backend       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Invoice Agent   │
│   (Enhanced)    │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌─────────┐ ┌──────────────┐
│   LLM   │ │ LangExtract  │
│ Service │ │   Service    │
└─────────┘ └──────┬───────┘
                   │
                   ▼
            ┌──────────────┐
            │ Gemini API   │
            │ (Pro/Flash)  │
            └──────────────┘
```

### Component Interaction Flow

1. **User submits invoice text** → Frontend sends to FastAPI
2. **Invoice Agent receives task** → Determines if extraction is needed
3. **LangExtract Service called** → Extracts structured data using Gemini
4. **Validation applied** → Checks business rules and constraints
5. **Results formatted** → Combines structured data with analysis
6. **Response sent** → Both structured data and summary returned
7. **Data stored** → Structured data saved to database

## Components and Interfaces

### 1. Validation Rules Configuration (`backend/app/config/validation_rules.py`)

**Purpose**: Centralized, configurable validation rules that can be easily enabled/disabled.

```python
from typing import List, Callable, Optional
from decimal import Decimal
from datetime import date
from pydantic import BaseModel
from enum import Enum


class ValidationSeverity(str, Enum):
    """Severity levels for validation failures."""
    ERROR = "error"      # Blocks approval
    WARNING = "warning"  # Shows warning but allows approval
    INFO = "info"        # Informational only


class ValidationRule(BaseModel):
    """Configuration for a single validation rule."""
    id: str
    name: str
    description: str
    enabled: bool = True
    severity: ValidationSeverity = ValidationSeverity.ERROR
    validator_func: Optional[Callable] = None
    
    class Config:
        arbitrary_types_allowed = True


class ValidationRulesConfig:
    """Configurable validation rules for invoice extraction."""
    
    # Rule definitions with enable/disable flags
    RULES = {
        "date_ordering": ValidationRule(
            id="date_ordering",
            name="Date Ordering Check",
            description="Verify that due date is after invoice date",
            enabled=True,  # Can be set to False to disable
            severity=ValidationSeverity.ERROR
        ),
        "total_calculation": ValidationRule(
            id="total_calculation",
            name="Total Calculation Check",
            description="Verify that total = subtotal + tax",
            enabled=True,
            severity=ValidationSeverity.ERROR
        ),
        "line_items_sum": ValidationRule(
            id="line_items_sum",
            name="Line Items Sum Check",
            description="Verify that line items sum to subtotal",
            enabled=True,
            severity=ValidationSeverity.WARNING  # Warning only
        ),
        "positive_amounts": ValidationRule(
            id="positive_amounts",
            name="Positive Amounts Check",
            description="Verify all amounts are positive",
            enabled=True,
            severity=ValidationSeverity.ERROR
        ),
        "required_fields": ValidationRule(
            id="required_fields",
            name="Required Fields Check",
            description="Verify all required fields are present",
            enabled=True,
            severity=ValidationSeverity.ERROR
        ),
        "invoice_number_format": ValidationRule(
            id="invoice_number_format",
            name="Invoice Number Format Check",
            description="Verify invoice number follows expected format",
            enabled=False,  # Disabled by default - can be enabled
            severity=ValidationSeverity.WARNING
        ),
        "vendor_name_length": ValidationRule(
            id="vendor_name_length",
            name="Vendor Name Length Check",
            description="Verify vendor name is reasonable length",
            enabled=False,  # Disabled by default
            severity=ValidationSeverity.INFO
        ),
        "future_date_check": ValidationRule(
            id="future_date_check",
            name="Future Date Check",
            description="Warn if invoice date is in the future",
            enabled=True,
            severity=ValidationSeverity.WARNING
        ),
        "duplicate_line_items": ValidationRule(
            id="duplicate_line_items",
            name="Duplicate Line Items Check",
            description="Check for duplicate line item descriptions",
            enabled=False,  # Can be enabled if needed
            severity=ValidationSeverity.INFO
        ),
        "tax_rate_reasonableness": ValidationRule(
            id="tax_rate_reasonableness",
            name="Tax Rate Reasonableness Check",
            description="Verify tax rate is within reasonable range (0-30%)",
            enabled=True,
            severity=ValidationSeverity.WARNING
        )
    }
    
    @classmethod
    def get_enabled_rules(cls) -> List[ValidationRule]:
        """Get list of enabled validation rules."""
        return [rule for rule in cls.RULES.values() if rule.enabled]
    
    @classmethod
    def is_rule_enabled(cls, rule_id: str) -> bool:
        """Check if a specific rule is enabled."""
        rule = cls.RULES.get(rule_id)
        return rule.enabled if rule else False
    
    @classmethod
    def enable_rule(cls, rule_id: str):
        """Enable a validation rule."""
        if rule_id in cls.RULES:
            cls.RULES[rule_id].enabled = True
    
    @classmethod
    def disable_rule(cls, rule_id: str):
        """Disable a validation rule."""
        if rule_id in cls.RULES:
            cls.RULES[rule_id].enabled = False
    
    @classmethod
    def load_from_env(cls):
        """Load rule configuration from environment variables."""
        import os
        
        # Example: VALIDATION_RULE_date_ordering=false
        for rule_id in cls.RULES.keys():
            env_var = f"VALIDATION_RULE_{rule_id}"
            env_value = os.getenv(env_var)
            
            if env_value is not None:
                enabled = env_value.lower() in ('true', '1', 'yes', 'on')
                cls.RULES[rule_id].enabled = enabled
    
    @classmethod
    def load_from_config_file(cls, config_path: str = "validation_rules.json"):
        """Load rule configuration from JSON file."""
        import json
        import os
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            for rule_id, rule_config in config.items():
                if rule_id in cls.RULES:
                    if 'enabled' in rule_config:
                        cls.RULES[rule_id].enabled = rule_config['enabled']
                    if 'severity' in rule_config:
                        cls.RULES[rule_id].severity = ValidationSeverity(rule_config['severity'])


class InvoiceValidator:
    """Validator that applies configured rules to invoice data."""
    
    def __init__(self, invoice_data: 'InvoiceData'):
        self.invoice_data = invoice_data
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def validate(self) -> dict:
        """
        Run all enabled validation rules.
        
        Returns:
            dict with errors, warnings, and info messages
        """
        # Get enabled rules
        enabled_rules = ValidationRulesConfig.get_enabled_rules()
        
        # Run each enabled rule
        for rule in enabled_rules:
            try:
                self._run_rule(rule)
            except Exception as e:
                self.errors.append(f"Validation rule '{rule.name}' failed: {str(e)}")
        
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "has_errors": len(self.errors) > 0,
            "has_warnings": len(self.warnings) > 0
        }
    
    def _run_rule(self, rule: ValidationRule):
        """Run a specific validation rule."""
        rule_id = rule.id
        
        # Date ordering check
        if rule_id == "date_ordering":
            if self.invoice_data.due_date and self.invoice_data.invoice_date:
                if self.invoice_data.due_date < self.invoice_data.invoice_date:
                    self._add_issue(rule, "Due date is before invoice date")
        
        # Total calculation check
        elif rule_id == "total_calculation":
            expected_total = self.invoice_data.subtotal
            if self.invoice_data.tax_amount:
                expected_total += self.invoice_data.tax_amount
            
            if abs(self.invoice_data.total_amount - expected_total) > Decimal('0.01'):
                self._add_issue(
                    rule,
                    f"Total {self.invoice_data.total_amount} doesn't match "
                    f"subtotal + tax ({expected_total})"
                )
        
        # Line items sum check
        elif rule_id == "line_items_sum":
            if self.invoice_data.line_items:
                line_items_total = sum(item.total for item in self.invoice_data.line_items)
                if abs(line_items_total - self.invoice_data.subtotal) > Decimal('0.01'):
                    self._add_issue(
                        rule,
                        f"Line items sum ({line_items_total}) doesn't match "
                        f"subtotal ({self.invoice_data.subtotal})"
                    )
        
        # Positive amounts check
        elif rule_id == "positive_amounts":
            if self.invoice_data.subtotal <= 0:
                self._add_issue(rule, "Subtotal must be positive")
            if self.invoice_data.total_amount <= 0:
                self._add_issue(rule, "Total amount must be positive")
            if self.invoice_data.tax_amount and self.invoice_data.tax_amount < 0:
                self._add_issue(rule, "Tax amount cannot be negative")
        
        # Required fields check
        elif rule_id == "required_fields":
            if not self.invoice_data.vendor_name:
                self._add_issue(rule, "Vendor name is required")
            if not self.invoice_data.invoice_number:
                self._add_issue(rule, "Invoice number is required")
        
        # Invoice number format check
        elif rule_id == "invoice_number_format":
            # Example: Check if invoice number matches pattern
            import re
            if not re.match(r'^[A-Z]{2,4}-\d{3,6}$', self.invoice_data.invoice_number):
                self._add_issue(
                    rule,
                    f"Invoice number '{self.invoice_data.invoice_number}' "
                    f"doesn't match expected format (e.g., INV-12345)"
                )
        
        # Vendor name length check
        elif rule_id == "vendor_name_length":
            if len(self.invoice_data.vendor_name) < 2:
                self._add_issue(rule, "Vendor name is too short")
            elif len(self.invoice_data.vendor_name) > 100:
                self._add_issue(rule, "Vendor name is too long")
        
        # Future date check
        elif rule_id == "future_date_check":
            from datetime import date as date_class
            today = date_class.today()
            if self.invoice_data.invoice_date > today:
                self._add_issue(rule, "Invoice date is in the future")
        
        # Duplicate line items check
        elif rule_id == "duplicate_line_items":
            descriptions = [item.description for item in self.invoice_data.line_items]
            duplicates = [desc for desc in descriptions if descriptions.count(desc) > 1]
            if duplicates:
                self._add_issue(rule, f"Duplicate line items found: {set(duplicates)}")
        
        # Tax rate reasonableness check
        elif rule_id == "tax_rate_reasonableness":
            if self.invoice_data.tax_amount and self.invoice_data.subtotal > 0:
                tax_rate = (self.invoice_data.tax_amount / self.invoice_data.subtotal) * 100
                if tax_rate < 0 or tax_rate > 30:
                    self._add_issue(
                        rule,
                        f"Tax rate ({tax_rate:.1f}%) seems unusual (expected 0-30%)"
                    )
    
    def _add_issue(self, rule: ValidationRule, message: str):
        """Add a validation issue based on severity."""
        full_message = f"[{rule.name}] {message}"
        
        if rule.severity == ValidationSeverity.ERROR:
            self.errors.append(full_message)
        elif rule.severity == ValidationSeverity.WARNING:
            self.warnings.append(full_message)
        else:  # INFO
            self.info.append(full_message)
```

### 2. Invoice Schema (`backend/app/models/invoice_schema.py`)

**Purpose**: Define the structure of extracted invoice data using Pydantic.

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import date
from decimal import Decimal


class InvoiceLineItem(BaseModel):
    """Single line item on an invoice."""
    description: str = Field(..., description="Item description")
    quantity: Decimal = Field(..., description="Quantity ordered")
    unit_price: Decimal = Field(..., description="Price per unit")
    total: Decimal = Field(..., description="Line item total")
    
    @validator('total')
    def validate_total(cls, v, values):
        """Validate that total = quantity * unit_price."""
        if 'quantity' in values and 'unit_price' in values:
            expected = values['quantity'] * values['unit_price']
            if abs(v - expected) > Decimal('0.01'):
                raise ValueError(f"Total {v} doesn't match quantity * unit_price")
        return v


class InvoiceData(BaseModel):
    """Structured invoice data extracted from text."""
    vendor_name: str = Field(..., description="Vendor/supplier name")
    vendor_address: Optional[str] = Field(None, description="Vendor address")
    invoice_number: str = Field(..., description="Invoice number")
    invoice_date: date = Field(..., description="Invoice date")
    due_date: Optional[date] = Field(None, description="Payment due date")
    currency: str = Field(default="USD", description="Currency code")
    subtotal: Decimal = Field(..., description="Subtotal before tax")
    tax_amount: Optional[Decimal] = Field(None, description="Tax amount")
    total_amount: Decimal = Field(..., description="Total amount due")
    line_items: List[InvoiceLineItem] = Field(default_factory=list)
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    # Note: Validation is now handled by ValidationRulesConfig
    # This keeps the model clean and validation rules configurable


class ExtractionResult(BaseModel):
    """Result of invoice extraction."""
    success: bool
    invoice_data: Optional[InvoiceData] = None
    validation_errors: List[str] = Field(default_factory=list)
    confidence_scores: dict = Field(default_factory=dict)
    extraction_time: float
    model_used: str
```

### 2. LangExtract Service (`backend/app/services/langextract_service.py`)

**Purpose**: Service for structured data extraction using LangExtract and Gemini.

```python
import os
import time
import logging
from typing import Optional
from langextract import LangExtract
from google.generativeai import configure, GenerativeModel

from app.models.invoice_schema import InvoiceData, ExtractionResult

logger = logging.getLogger(__name__)


class LangExtractService:
    """Service for structured invoice data extraction using LangExtract."""
    
    _extractor: Optional[LangExtract] = None
    _model_name: Optional[str] = None
    
    @classmethod
    def get_few_shot_examples(cls) -> List[dict]:
        """
        Get few-shot examples for invoice extraction.
        These examples help the model understand the expected output format.
        """
        return [
            {
                "input": """
                INVOICE
                ABC Company
                Invoice #: 001
                Date: 2024-01-15
                Total: $1,000.00
                """,
                "output": {
                    "vendor_name": "ABC Company",
                    "invoice_number": "001",
                    "invoice_date": "2024-01-15",
                    "total_amount": 1000.00,
                    "currency": "USD"
                }
            },
            {
                "input": """
                Invoice Number: INV-2024-002
                From: XYZ Corp
                Date: March 10, 2024
                Amount Due: €500.00
                """,
                "output": {
                    "vendor_name": "XYZ Corp",
                    "invoice_number": "INV-2024-002",
                    "invoice_date": "2024-03-10",
                    "total_amount": 500.00,
                    "currency": "EUR"
                }
            }
        ]
    
    @classmethod
    def initialize(cls):
        """Initialize LangExtract with Gemini API and few-shot examples."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        # Configure Gemini
        configure(api_key=api_key)
        
        # Get model preference (flash for speed, pro for accuracy)
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        cls._model_name = model_name
        
        # Get few-shot examples
        examples = cls.get_few_shot_examples()
        
        # Initialize LangExtract with examples
        cls._extractor = LangExtract(
            model=GenerativeModel(model_name),
            schema=InvoiceData,
            examples=examples  # Few-shot examples for better accuracy
        )
        
        logger.info(
            f"✅ LangExtract initialized with {model_name} "
            f"and {len(examples)} few-shot examples"
        )
    
    @classmethod
    def get_extractor(cls) -> LangExtract:
        """Get or create LangExtract instance."""
        if cls._extractor is None:
            cls.initialize()
        return cls._extractor
    
    @classmethod
    async def extract_invoice_data(
        cls,
        invoice_text: str,
        plan_id: str
    ) -> ExtractionResult:
        """
        Extract structured data from invoice text with configurable validation.
        
        Args:
            invoice_text: Raw invoice text
            plan_id: Plan ID for logging
            
        Returns:
            ExtractionResult with structured data and validation results
        """
        logger.info(f"📊 Extracting invoice data [plan_id={plan_id}]")
        start_time = time.time()
        
        try:
            extractor = cls.get_extractor()
            
            # Extract structured data
            result = await extractor.extract_async(invoice_text)
            
            # Parse into InvoiceData model
            invoice_data = InvoiceData(**result)
            
            # Run configurable validation rules
            validator = InvoiceValidator(invoice_data)
            validation_result = validator.validate()
            
            # Calculate extraction time
            extraction_time = time.time() - start_time
            
            # Determine success based on validation errors
            success = not validation_result['has_errors']
            
            # Combine all validation messages
            all_validation_messages = (
                validation_result['errors'] +
                validation_result['warnings'] +
                validation_result['info']
            )
            
            logger.info(
                f"{'✅' if success else '⚠️'} Extraction completed [plan_id={plan_id}, "
                f"duration={extraction_time:.2f}s, vendor={invoice_data.vendor_name}, "
                f"errors={len(validation_result['errors'])}, "
                f"warnings={len(validation_result['warnings'])}]"
            )
            
            return ExtractionResult(
                success=success,
                invoice_data=invoice_data if success else None,
                validation_errors=all_validation_messages,
                confidence_scores=result.get('_confidence', {}),
                extraction_time=extraction_time,
                model_used=cls._model_name
            )
            
        except ValueError as e:
            # Schema validation error
            extraction_time = time.time() - start_time
            logger.error(f"❌ Schema validation failed [plan_id={plan_id}]: {e}")
            
            return ExtractionResult(
                success=False,
                validation_errors=[f"Schema validation failed: {str(e)}"],
                extraction_time=extraction_time,
                model_used=cls._model_name
            )
            
        except Exception as e:
            # Extraction error
            extraction_time = time.time() - start_time
            logger.error(f"❌ Extraction failed [plan_id={plan_id}]: {e}")
            
            return ExtractionResult(
                success=False,
                validation_errors=[f"Extraction failed: {str(e)}"],
                extraction_time=extraction_time,
                model_used=cls._model_name
            )
    
    @classmethod
    def format_extraction_result(cls, result: ExtractionResult) -> str:
        """Format extraction result as human-readable text."""
        if not result.success:
            return f"❌ Extraction failed:\n" + "\n".join(result.validation_errors)
        
        invoice = result.invoice_data
        output = []
        
        output.append("📊 **Extracted Invoice Data**\n")
        output.append(f"**Vendor:** {invoice.vendor_name}")
        output.append(f"**Invoice #:** {invoice.invoice_number}")
        output.append(f"**Date:** {invoice.invoice_date}")
        if invoice.due_date:
            output.append(f"**Due Date:** {invoice.due_date}")
        output.append(f"**Total:** {invoice.currency} {invoice.total_amount}")
        
        if invoice.line_items:
            output.append(f"\n**Line Items:** ({len(invoice.line_items)} items)")
            for i, item in enumerate(invoice.line_items, 1):
                output.append(
                    f"  {i}. {item.description} - "
                    f"{item.quantity} × {invoice.currency}{item.unit_price} = "
                    f"{invoice.currency}{item.total}"
                )
        
        if result.validation_errors:
            output.append(f"\n⚠️ **Validation Warnings:**")
            for error in result.validation_errors:
                output.append(f"  - {error}")
        
        output.append(f"\n⏱️ Extracted in {result.extraction_time:.2f}s using {result.model_used}")
        
        return "\n".join(output)
```

### 3. Enhanced Invoice Agent Node

**Purpose**: Update Invoice Agent to support both text analysis and structured extraction.

```python
async def invoice_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Invoice agent node - handles invoice management with structured extraction.
    Extraction results are stored in state for HITL approval before database storage.
    """
    task = state["task_description"]
    plan_id = state["plan_id"]
    websocket_manager = state.get("websocket_manager")
    
    logger.info(f"Invoice Agent processing task for plan {plan_id}")
    
    # Check if task includes invoice text for extraction
    needs_extraction = detect_invoice_text(task)
    
    if needs_extraction:
        # Extract structured data
        extraction_result = await LangExtractService.extract_invoice_data(
            invoice_text=task,
            plan_id=plan_id
        )
        
        # Format extraction result for display
        structured_response = LangExtractService.format_extraction_result(extraction_result)
        
        # Also get AI analysis if not in mock mode
        if not LLMService.is_mock_mode():
            prompt = build_invoice_analysis_prompt(task, extraction_result)
            ai_analysis = await LLMService.call_llm_streaming(
                prompt=prompt,
                plan_id=plan_id,
                websocket_manager=websocket_manager,
                agent_name="Invoice"
            )
            
            # Combine structured data with AI analysis
            response = f"{structured_response}\n\n**AI Analysis:**\n{ai_analysis}"
        else:
            response = structured_response
        
        # Store extraction result in state for HITL approval
        # DO NOT store to database yet - wait for human approval
        return {
            "messages": [response],
            "current_agent": "Invoice",
            "final_result": response,
            "extraction_result": extraction_result,  # Store for HITL
            "requires_extraction_approval": True  # Flag for HITL
        }
        
    else:
        # Regular text analysis (existing behavior)
        if LLMService.is_mock_mode():
            response = LLMService.get_mock_response("Invoice", task)
        else:
            prompt = build_invoice_prompt(task)
            response = await LLMService.call_llm_streaming(
                prompt=prompt,
                plan_id=plan_id,
                websocket_manager=websocket_manager,
                agent_name="Invoice"
            )
        
        return {
            "messages": [response],
            "current_agent": "Invoice",
            "final_result": response
        }
```

### 4. HITL Approval Handler (`backend/app/services/agent_service.py`)

**Purpose**: Handle extraction approval requests and responses.

```python
async def handle_extraction_approval(
    plan_id: str,
    request_id: str,
    approved: bool,
    feedback: str = None
) -> Dict[str, Any]:
    """
    Handle extraction approval from HITL.
    
    Args:
        plan_id: Plan identifier
        request_id: Approval request ID
        approved: Whether extraction was approved
        feedback: Optional feedback from user
        
    Returns:
        Status of approval handling
    """
    logger.info(f"Processing extraction approval for plan {plan_id}: approved={approved}")
    
    # Get execution state
    execution_state = AgentService._pending_executions.get(plan_id)
    if not execution_state:
        logger.error(f"No execution state found for plan {plan_id}")
        return {"status": "error", "message": "Cannot process approval - no state found"}
    
    # Get extraction result from state
    extraction_result = execution_state.get("extraction_result")
    if not extraction_result:
        logger.error(f"No extraction result found for plan {plan_id}")
        return {"status": "error", "message": "No extraction result to approve"}
    
    try:
        if approved:
            # Store extraction to database
            await InvoiceExtractionRepository.store_extraction(
                plan_id=plan_id,
                extraction_result=extraction_result
            )
            
            logger.info(f"✅ Extraction approved and stored for plan {plan_id}")
            
            # Send confirmation
            await websocket_manager.send_message(plan_id, {
                "type": "extraction_approval_confirmed",
                "data": {
                    "plan_id": plan_id,
                    "message": "Extraction data approved and stored successfully",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            })
            
            return {"status": "approved", "stored": True}
        else:
            # Extraction rejected - don't store
            logger.info(f"❌ Extraction rejected for plan {plan_id}: {feedback}")
            
            # Send rejection confirmation
            await websocket_manager.send_message(plan_id, {
                "type": "extraction_approval_confirmed",
                "data": {
                    "plan_id": plan_id,
                    "message": f"Extraction rejected: {feedback or 'No reason provided'}",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            })
            
            return {"status": "rejected", "stored": False}
            
    except Exception as e:
        logger.error(f"Failed to process extraction approval for plan {plan_id}: {e}")
        raise


async def send_extraction_approval_request(
    plan_id: str,
    extraction_result: ExtractionResult
) -> str:
    """
    Send extraction approval request via WebSocket.
    
    Args:
        plan_id: Plan identifier
        extraction_result: Extraction result to approve
        
    Returns:
        Request ID for tracking
    """
    request_id = str(uuid.uuid4())
    
    # Format the extraction result for display
    formatted_view = LangExtractService.format_extraction_result(extraction_result)
    
    # Prepare approval request message
    approval_msg = {
        "type": "extraction_approval_request",
        "data": {
            "request_id": request_id,
            "plan_id": plan_id,
            "extraction_result": {
                "success": extraction_result.success,
                "invoice_data": extraction_result.invoice_data.dict() if extraction_result.invoice_data else None,
                "validation_errors": extraction_result.validation_errors,
                "confidence_scores": extraction_result.confidence_scores,
                "extraction_time": extraction_result.extraction_time,
                "model_used": extraction_result.model_used
            },
            "formatted_view": formatted_view,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    logger.info(f"🔔 Sending extraction approval request for plan {plan_id}")
    await websocket_manager.send_message(plan_id, approval_msg)
    
    return request_id
```

### 5. Database Storage

**Purpose**: Store approved extraction data for later retrieval and export.

```python
# Add to backend/app/db/repositories.py

class InvoiceExtractionRepository:
    """Repository for invoice extraction results."""
    
    @staticmethod
    async def store_extraction(plan_id: str, extraction_result: ExtractionResult):
        """Store extraction result linked to plan (only after approval)."""
        collection = MongoDB.get_collection("invoice_extractions")
        
        document = {
            "plan_id": plan_id,
            "success": extraction_result.success,
            "invoice_data": extraction_result.invoice_data.dict() if extraction_result.invoice_data else None,
            "validation_errors": extraction_result.validation_errors,
            "confidence_scores": extraction_result.confidence_scores,
            "extraction_time": extraction_result.extraction_time,
            "model_used": extraction_result.model_used,
            "approved_at": datetime.utcnow(),  # Timestamp of approval
            "created_at": datetime.utcnow()
        }
        
        await collection.insert_one(document)
        logger.info(f"💾 Stored approved extraction for plan {plan_id}")
    
    @staticmethod
    async def get_extraction(plan_id: str) -> Optional[dict]:
        """Retrieve extraction result for a plan."""
        collection = MongoDB.get_collection("invoice_extractions")
        return await collection.find_one({"plan_id": plan_id})
    
    @staticmethod
    async def export_extraction_json(plan_id: str) -> Optional[str]:
        """Export extraction as JSON string."""
        extraction = await InvoiceExtractionRepository.get_extraction(plan_id)
        if extraction:
            return json.dumps(extraction["invoice_data"], indent=2)
        return None
    
    @staticmethod
    async def export_extraction_csv(plan_id: str) -> Optional[str]:
        """Export extraction as CSV string."""
        extraction = await InvoiceExtractionRepository.get_extraction(plan_id)
        if not extraction or not extraction.get("invoice_data"):
            return None
        
        # Convert to CSV format
        invoice_data = extraction["invoice_data"]
        # Implementation details for CSV conversion
        # ...
        return csv_string
```

## Data Models

### AgentState Extension

```python
class AgentState(TypedDict):
    """State for agent workflow."""
    # Existing fields
    messages: Annotated[Sequence[str], operator.add]
    plan_id: str
    session_id: str
    task_description: str
    current_agent: str
    next_agent: Optional[str]
    final_result: str
    approval_required: bool
    approved: Optional[bool]
    websocket_manager: Optional[Any]
    llm_provider: Optional[str]
    llm_temperature: Optional[float]
    
    # New fields for extraction
    extraction_result: Optional[ExtractionResult]  # Stores extraction for HITL
    requires_extraction_approval: Optional[bool]  # Flag for HITL approval
    extraction_approved: Optional[bool]  # Approval status
```

### Validation Rules Configuration File (`backend/validation_rules.json`)

**Purpose**: JSON file for easy editing of validation rules without code changes.

```json
{
  "date_ordering": {
    "enabled": true,
    "severity": "error"
  },
  "total_calculation": {
    "enabled": true,
    "severity": "error"
  },
  "line_items_sum": {
    "enabled": true,
    "severity": "warning"
  },
  "positive_amounts": {
    "enabled": true,
    "severity": "error"
  },
  "required_fields": {
    "enabled": true,
    "severity": "error"
  },
  "invoice_number_format": {
    "enabled": false,
    "severity": "warning"
  },
  "vendor_name_length": {
    "enabled": false,
    "severity": "info"
  },
  "future_date_check": {
    "enabled": true,
    "severity": "warning"
  },
  "duplicate_line_items": {
    "enabled": false,
    "severity": "info"
  },
  "tax_rate_reasonableness": {
    "enabled": true,
    "severity": "warning"
  }
}
```

### Environment Configuration

```bash
# Gemini Configuration
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-flash  # or gemini-1.5-pro
GEMINI_TEMPERATURE=0.1  # Low for consistency

# Feature Flags
ENABLE_STRUCTURED_EXTRACTION=true
EXTRACTION_VALIDATION=true
EXTRACTION_REQUIRES_APPROVAL=true  # Require HITL approval before storage

# Few-Shot Examples
USE_FEW_SHOT_EXAMPLES=true
FEW_SHOT_EXAMPLE_COUNT=2

# Validation Rules (can override JSON config)
VALIDATION_RULE_date_ordering=true
VALIDATION_RULE_total_calculation=true
VALIDATION_RULE_line_items_sum=true
# VALIDATION_RULE_invoice_number_format=false  # Disabled
```

### API Response Format

```json
{
  "success": true,
  "invoice_data": {
    "vendor_name": "Acme Corp",
    "invoice_number": "INV-12345",
    "invoice_date": "2024-11-15",
    "due_date": "2024-12-15",
    "currency": "USD",
    "subtotal": 5000.00,
    "tax_amount": 400.00,
    "total_amount": 5400.00,
    "line_items": [
      {
        "description": "Professional Services",
        "quantity": 40,
        "unit_price": 125.00,
        "total": 5000.00
      }
    ]
  },
  "validation_errors": [],
  "confidence_scores": {
    "vendor_name": 0.95,
    "total_amount": 0.98
  },
  "extraction_time": 2.3,
  "model_used": "gemini-1.5-flash"
}
```

## Data Flow

### Extraction Flow with HITL Approval

```
Invoice Text → LangExtract Service → Gemini API
                                    ↓
                            Structured Data
                                    ↓
                            Validation Rules
                                    ↓
                        ┌───────────┴───────────┐
                        ▼                       ▼
                   Success                   Failure
                        ↓                       ↓
              Store in Agent State      Return Errors
                        ↓
              Format for Display
                        ↓
              Send to HITL Window
              (JSON + Formatted View)
                        ↓
              Wait for Human Approval
                        ↓
                ┌───────┴───────┐
                ▼               ▼
            Approved        Rejected
                ↓               ↓
        Store in DB      Discard Data
                ↓
        Send to Frontend
```

### HITL Approval Flow

**Step 1: Extraction Complete**
- Agent extracts structured data
- Stores ExtractionResult in agent state
- Sets `requires_extraction_approval` flag

**Step 2: HITL Request**
- System sends `extraction_approval_request` via WebSocket
- Includes both JSON and formatted views of extracted data
- Frontend displays in HITL modal window

**Step 3: Human Review**
- User reviews extracted data in JSON format
- User can see validation errors if any
- User can approve or reject

**Step 4: Approval Response**
- If approved: Store to database and continue
- If rejected: Discard extraction, optionally retry
- Send confirmation to frontend

### WebSocket Message Format for HITL

**Extraction Approval Request**:
```json
{
  "type": "extraction_approval_request",
  "data": {
    "request_id": "uuid",
    "plan_id": "uuid",
    "extraction_result": {
      "success": true,
      "invoice_data": {
        "vendor_name": "Acme Corp",
        "invoice_number": "INV-001",
        "invoice_date": "2024-11-15",
        "total_amount": 5000.00,
        "currency": "USD",
        "line_items": [...]
      },
      "validation_errors": [],
      "confidence_scores": {...},
      "extraction_time": 2.1,
      "model_used": "gemini-1.5-flash"
    },
    "formatted_view": "📊 **Extracted Invoice Data**\n...",
    "timestamp": "2024-11-29T12:00:00Z"
  }
}
```

**Extraction Approval Response**:
```json
{
  "type": "extraction_approval_response",
  "data": {
    "request_id": "uuid",
    "plan_id": "uuid",
    "approved": true,
    "feedback": "Looks good, approved",
    "timestamp": "2024-11-29T12:01:00Z"
  }
}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Schema Compliance

*For any* invoice text that is successfully extracted, the returned data should conform to the InvoiceData schema with all required fields present (vendor_name, invoice_number, invoice_date, total_amount).

**Validates: Requirements 1.2, 3.1**

### Property 2: Line Item Structure

*For any* extracted invoice with line items, each line item should contain description, quantity, unit_price, and total fields.

**Validates: Requirements 3.2**

### Property 3: Date Format Consistency

*For any* extracted dates (invoice_date, due_date), they should be in ISO 8601 format (YYYY-MM-DD).

**Validates: Requirements 3.3**

### Property 4: Amount Parsing

*For any* extracted monetary amounts, they should be parsed as Decimal numbers with associated currency code.

**Validates: Requirements 3.4**

### Property 5: Line Total Validation

*For any* invoice with line items, the sum of all line item totals should equal the invoice subtotal (within 0.01 tolerance for rounding).

**Validates: Requirements 4.1**

### Property 6: Date Ordering Validation

*For any* invoice with both invoice_date and due_date, the due_date should be equal to or after the invoice_date.

**Validates: Requirements 4.2**

### Property 7: Positive Amount Validation

*For any* extracted monetary amount (subtotal, tax, total, line item prices), the value should be a positive number.

**Validates: Requirements 4.3**

### Property 8: Missing Field Handling

*For any* invoice text with incomplete information, missing optional fields should be set to None/null without causing extraction failure.

**Validates: Requirements 1.3**

### Property 9: Error Message Specificity

*For any* validation failure, the error message should specifically identify which field or rule failed validation.

**Validates: Requirements 4.5**

### Property 10: Confidence Score Presence

*For any* successful extraction, the result should include confidence scores for extracted fields.

**Validates: Requirements 1.5**

### Property 11: Dual Output Format

*For any* extraction request, the system should return both structured data (InvoiceData) and a formatted natural language summary.

**Validates: Requirements 5.1**

### Property 12: Database Persistence

*For any* successful extraction, the structured data should be stored in the database linked to the plan_id and be retrievable later.

**Validates: Requirements 7.1, 7.2**

### Property 13: Metadata Completeness

*For any* stored extraction result, it should include extraction_time, model_used, and created_at timestamp.

**Validates: Requirements 7.5**

### Property 14: Multi-Currency Support

*For any* invoice containing amounts in a specific currency, the extracted data should correctly identify and store the currency code.

**Validates: Requirements 6.3**

## Error Handling

### Error Categories

1. **Extraction Errors**
   - Gemini API unavailable
   - API key invalid or expired
   - Rate limiting
   - Malformed invoice text
   - **Handling**: Return ExtractionResult with success=False and specific error message

2. **Validation Errors**
   - Line totals don't match invoice total
   - Due date before invoice date
   - Negative amounts
   - Required fields missing
   - **Handling**: Return ExtractionResult with validation_errors list

3. **Schema Errors**
   - Extracted data doesn't match schema
   - Type conversion failures
   - Invalid date formats
   - **Handling**: Catch Pydantic ValidationError and return user-friendly message

4. **Database Errors**
   - Storage failure
   - Retrieval failure
   - **Handling**: Log error, return extraction result but warn about storage failure

### Fallback Strategy

When Gemini extraction fails:
1. Log the error with full context
2. Attempt fallback to OpenAI structured output (if configured)
3. If all extraction fails, return text-only analysis
4. Never crash the agent - always return a response

## Testing Strategy

### Unit Tests

1. **Schema Validation Tests**
   - Test InvoiceData model with valid data
   - Test validation rules (date ordering, amount positivity)
   - Test line item total calculation
   - Test missing optional fields

2. **Extraction Service Tests**
   - Test initialization with different models
   - Test extraction with mock Gemini responses
   - Test error handling for API failures
   - Test confidence score parsing

3. **Formatting Tests**
   - Test format_extraction_result with various data
   - Test handling of validation errors in formatting
   - Test currency display
   - Test line item formatting

### Property-Based Tests

Property-based tests will use `hypothesis` library to generate random invoice data and verify properties hold.

**Configuration**:
- Minimum 100 iterations per property test
- Use custom generators for invoice data
- Tag each test with property number

**Test Tagging Format**:
```python
# Feature: invoice-structured-extraction, Property 5: Line Total Validation
# Validates: Requirements 4.1
@given(invoice_data=invoice_generator())
def test_line_totals_sum_to_subtotal(invoice_data):
    line_total = sum(item.total for item in invoice_data.line_items)
    assert abs(line_total - invoice_data.subtotal) < Decimal('0.01')
```

**Property Test Coverage**:
- Property 1: Schema compliance (test with random valid data)
- Property 2: Line item structure (test with random line items)
- Property 3: Date format (test with various date inputs)
- Property 4: Amount parsing (test with various amount formats)
- Property 5: Line total validation (test with random line items)
- Property 6: Date ordering (test with random date pairs)
- Property 7: Positive amounts (test with random amounts)
- Property 8: Missing fields (test with incomplete data)
- Property 9: Error messages (test with invalid data)
- Property 12: Database persistence (test with random extractions)

### Integration Tests

1. **End-to-End Extraction**
   - Test complete flow from invoice text to stored data
   - Test with real Gemini API (using test key)
   - Test with various invoice formats
   - Test error scenarios

2. **Agent Integration**
   - Test Invoice Agent with extraction-enabled tasks
   - Test fallback to text analysis for non-invoice tasks
   - Test WebSocket message delivery
   - Test database storage and retrieval

3. **Validation Integration**
   - Test validation rules with real extracted data
   - Test handling of validation failures
   - Test confidence score thresholds

## Performance Considerations

### Response Time Targets

- **Gemini Flash**: < 3 seconds for typical invoice
- **Gemini Pro**: < 5 seconds for typical invoice
- **Database Storage**: < 100ms
- **Formatting**: < 50ms

### Optimization Strategies

1. **Model Selection**: Use Gemini Flash by default, Pro for complex invoices
2. **Caching**: Cache schema definitions and formatters
3. **Async Operations**: Use async for all I/O (API calls, database)
4. **Batch Processing**: Support batch extraction for multiple invoices
5. **Streaming**: Consider streaming extraction results for large invoices

## Security Considerations

### API Key Management

- Store Gemini API key in environment variables only
- Never log API keys
- Use different keys for dev/staging/production
- Rotate keys regularly
- Monitor API usage for anomalies

### Data Privacy

- Don't store sensitive invoice data longer than necessary
- Implement data retention policies
- Consider encryption for stored invoice data
- Comply with data protection regulations (GDPR, etc.)
- Allow users to delete their extraction data

### Input Validation

- Validate invoice text length (max 50,000 characters)
- Sanitize input before sending to Gemini
- Rate limit extraction requests per user
- Implement circuit breaker for Gemini API

## Deployment Considerations

### Environment Setup

**Development**:
```bash
GEMINI_API_KEY=your-dev-key
GEMINI_MODEL=gemini-1.5-flash
ENABLE_STRUCTURED_EXTRACTION=true
EXTRACTION_VALIDATION=true
```

**Production**:
```bash
GEMINI_API_KEY=your-prod-key
GEMINI_MODEL=gemini-1.5-pro
ENABLE_STRUCTURED_EXTRACTION=true
EXTRACTION_VALIDATION=true
GEMINI_TEMPERATURE=0.1
```

### Monitoring

**Metrics to Track**:
- Extraction success rate
- Extraction latency (p50, p95, p99)
- Validation failure rate
- Gemini API error rate
- Cost per extraction
- Confidence score distribution

**Alerts**:
- Extraction success rate < 95%
- Extraction latency p95 > 10 seconds
- Gemini API error rate > 5%
- Daily cost exceeds budget

### Cost Management

**Gemini Pricing** (as of Nov 2024):
- Gemini 1.5 Flash: $0.075 per 1M input tokens, $0.30 per 1M output tokens
- Gemini 1.5 Pro: $1.25 per 1M input tokens, $5.00 per 1M output tokens

**Typical Invoice**:
- Input: ~1,000 tokens (invoice text)
- Output: ~200 tokens (structured data)
- Cost per invoice (Flash): ~$0.0001
- Cost per invoice (Pro): ~$0.002

**Cost Optimization**:
1. Use Flash for simple invoices, Pro for complex ones
2. Cache extraction results for duplicate invoices
3. Set monthly budget limits
4. Monitor usage per user/organization

## Managing Validation Rules

### How to Enable/Disable Rules

**Method 1: Edit JSON Configuration File** (Recommended)

Edit `backend/validation_rules.json`:
```json
{
  "invoice_number_format": {
    "enabled": true,  // Change to false to disable
    "severity": "warning"
  }
}
```

**Method 2: Environment Variables**

Set in `backend/.env`:
```bash
VALIDATION_RULE_invoice_number_format=false
```

**Method 3: Programmatically**

```python
from app.config.validation_rules import ValidationRulesConfig

# Disable a rule
ValidationRulesConfig.disable_rule("invoice_number_format")

# Enable a rule
ValidationRulesConfig.enable_rule("tax_rate_reasonableness")

# Check if rule is enabled
if ValidationRulesConfig.is_rule_enabled("date_ordering"):
    print("Date ordering check is active")
```

### How to Add New Validation Rules

**Step 1**: Add rule definition to `ValidationRulesConfig.RULES`:

```python
"custom_vendor_check": ValidationRule(
    id="custom_vendor_check",
    name="Custom Vendor Check",
    description="Check if vendor is in approved list",
    enabled=True,
    severity=ValidationSeverity.WARNING
)
```

**Step 2**: Implement validation logic in `InvoiceValidator._run_rule()`:

```python
elif rule_id == "custom_vendor_check":
    approved_vendors = ["Acme Corp", "XYZ Inc", "ABC Company"]
    if self.invoice_data.vendor_name not in approved_vendors:
        self._add_issue(
            rule,
            f"Vendor '{self.invoice_data.vendor_name}' is not in approved list"
        )
```

**Step 3**: Add to configuration file:

```json
{
  "custom_vendor_check": {
    "enabled": true,
    "severity": "warning"
  }
}
```

### Validation Rule Severity Levels

- **ERROR**: Blocks approval, must be fixed
- **WARNING**: Shows warning but allows approval
- **INFO**: Informational only, doesn't affect approval

### Example: Temporarily Suspend All Validation

```bash
# In .env file
EXTRACTION_VALIDATION=false
```

Or disable specific rules:
```bash
VALIDATION_RULE_date_ordering=false
VALIDATION_RULE_total_calculation=false
VALIDATION_RULE_line_items_sum=false
```

### Example: Add Industry-Specific Rules

For healthcare invoices:
```python
"hipaa_compliance_check": ValidationRule(
    id="hipaa_compliance_check",
    name="HIPAA Compliance Check",
    description="Verify invoice doesn't contain PHI",
    enabled=True,
    severity=ValidationSeverity.ERROR
)
```

For construction invoices:
```python
"retention_amount_check": ValidationRule(
    id="retention_amount_check",
    name="Retention Amount Check",
    description="Verify retention amount is within 5-10% range",
    enabled=True,
    severity=ValidationSeverity.WARNING
)
```

## Multiple Invoice Testing UI

### Overview

To support efficient testing of the extraction system with multiple invoices, the UI will maintain a session-based history of recent extractions and allow users to quickly submit and review multiple invoices without page refreshes.

### Components

#### 1. Extraction History Panel

**Purpose**: Display recent extractions in the current session for quick reference.

**Location**: Sidebar or collapsible panel in the main UI

**Display Format**:
```
Recent Extractions (Session)
┌─────────────────────────────────┐
│ ✅ INV-001 | Acme Corp          │
│    $5,940.00 | 2 warnings       │
├─────────────────────────────────┤
│ ❌ INV-002 | XYZ Inc            │
│    Extraction failed             │
├─────────────────────────────────┤
│ ✅ INV-003 | Tech Solutions     │
│    $12,500.00 | No issues       │
└─────────────────────────────────┘
```

**Data Structure**:
```typescript
interface ExtractionHistoryItem {
  plan_id: string;
  invoice_number: string;
  vendor_name: string;
  total_amount: number;
  currency: string;
  status: 'success' | 'failed' | 'pending';
  error_count: number;
  warning_count: number;
  timestamp: string;
}
```

#### 2. Quick Submit Interface

**Purpose**: Allow rapid submission of multiple invoices for testing.

**Features**:
- Large text area for invoice text
- "Submit & Clear" button to process and reset for next invoice
- "Submit & Keep" button to process without clearing
- Keyboard shortcut (Ctrl+Enter) for quick submission
- Auto-focus on text area after submission

**Implementation**:
```typescript
const handleQuickSubmit = async (clearAfter: boolean) => {
  const result = await submitInvoice(invoiceText);
  
  // Add to history
  addToHistory(result);
  
  // Clear if requested
  if (clearAfter) {
    setInvoiceText('');
    textAreaRef.current?.focus();
  }
  
  // Show result notification
  showNotification(result);
};
```

#### 3. Extraction Detail View

**Purpose**: Display full details when user clicks on a history item.

**Content**:
- Full extracted invoice data
- Validation results (errors, warnings, info)
- Confidence scores
- Extraction metadata (time, model used)
- Original invoice text
- Option to re-extract or export

### Session Management

**Storage**: Use React state + sessionStorage for persistence across page refreshes

```typescript
interface ExtractionSession {
  session_id: string;
  started_at: string;
  extractions: ExtractionHistoryItem[];
  total_count: number;
  success_count: number;
  failed_count: number;
}

// Save to sessionStorage on each extraction
const updateSession = (extraction: ExtractionHistoryItem) => {
  const session = getSession();
  session.extractions.push(extraction);
  session.total_count++;
  
  if (extraction.status === 'success') {
    session.success_count++;
  } else {
    session.failed_count++;
  }
  
  sessionStorage.setItem('extraction_session', JSON.stringify(session));
};
```

### UI Workflow

**Step 1: User pastes invoice text**
- Text area auto-expands to fit content
- Character count displayed
- Validation indicator (e.g., "Ready to extract")

**Step 2: User submits**
- Loading indicator appears
- Text area disabled during processing
- Progress message: "Extracting invoice data..."

**Step 3: Result received**
- Success/failure notification appears
- Extraction added to history panel
- Text area cleared (if "Submit & Clear" used)
- Focus returns to text area for next invoice

**Step 4: User reviews history**
- Click any history item to view details
- Details shown in modal or side panel
- Can export, re-extract, or delete

### Validation Results Display

#### Severity-Based Grouping

Display validation issues grouped by severity with visual indicators:

```
Validation Results
┌─────────────────────────────────────┐
│ ❌ ERRORS (2)                       │
│   • [Date Ordering] Due date is     │
│     before invoice date             │
│   • [Required Fields] Vendor name   │
│     is required                     │
├─────────────────────────────────────┤
│ ⚠️  WARNINGS (1)                    │
│   • [Tax Rate] Tax rate (35%)       │
│     seems unusual (expected 0-30%)  │
├─────────────────────────────────────┤
│ ℹ️  INFO (1)                        │
│   • [Vendor Name] Vendor name is    │
│     longer than typical             │
└─────────────────────────────────────┘
```

#### Visual Indicators

**Error Badge**: Red background, white text
```tsx
<Badge color="error" icon={<ErrorIcon />}>
  2 Errors
</Badge>
```

**Warning Badge**: Orange background, dark text
```tsx
<Badge color="warning" icon={<WarningIcon />}>
  1 Warning
</Badge>
```

**Info Badge**: Blue background, white text
```tsx
<Badge color="info" icon={<InfoIcon />}>
  1 Info
</Badge>
```

#### Field-Level Highlighting

When displaying extracted data, highlight fields with issues:

```tsx
<DataField 
  label="Due Date" 
  value={invoice.due_date}
  error={hasError('due_date')}
  errorMessage="Due date is before invoice date"
/>
```

**CSS Styling**:
```css
.data-field--error {
  border-left: 3px solid #d32f2f;
  background-color: #ffebee;
  padding-left: 8px;
}

.data-field--warning {
  border-left: 3px solid #f57c00;
  background-color: #fff3e0;
  padding-left: 8px;
}
```

#### Expandable Validation Details

```tsx
<ValidationSection>
  <ValidationHeader onClick={toggleExpand}>
    <ErrorIcon /> 2 Errors
    <ExpandIcon />
  </ValidationHeader>
  
  {expanded && (
    <ValidationList>
      {errors.map(error => (
        <ValidationItem key={error.id}>
          <RuleName>{error.rule_name}</RuleName>
          <Message>{error.message}</Message>
          <AffectedField>{error.field}</AffectedField>
        </ValidationItem>
      ))}
    </ValidationList>
  )}
</ValidationSection>
```

### API Enhancements

#### Get Extraction History

```
GET /api/v3/extractions/history?session_id={session_id}

Response:
{
  "session_id": "uuid",
  "extractions": [
    {
      "plan_id": "uuid",
      "invoice_number": "INV-001",
      "vendor_name": "Acme Corp",
      "total_amount": 5940.00,
      "currency": "USD",
      "status": "success",
      "validation_summary": {
        "error_count": 0,
        "warning_count": 2,
        "info_count": 1
      },
      "timestamp": "2024-11-29T12:00:00Z"
    }
  ],
  "summary": {
    "total_count": 10,
    "success_count": 8,
    "failed_count": 2
  }
}
```

#### Get Extraction Details

```
GET /api/v3/extractions/{plan_id}

Response:
{
  "plan_id": "uuid",
  "extraction_result": {
    "success": true,
    "invoice_data": {...},
    "validation_errors": [...],
    "confidence_scores": {...}
  },
  "validation_details": {
    "errors": [
      {
        "rule_id": "date_ordering",
        "rule_name": "Date Ordering Check",
        "severity": "error",
        "message": "Due date is before invoice date",
        "affected_fields": ["due_date", "invoice_date"]
      }
    ],
    "warnings": [...],
    "info": [...]
  },
  "original_text": "INVOICE\n..."
}
```

### Testing Workflow Example

**Scenario**: Developer wants to test extraction with 5 different invoice formats

1. Open extraction testing page
2. Paste first invoice → Submit & Clear
3. See result in history (✅ Success, 0 errors)
4. Paste second invoice → Submit & Clear
5. See result in history (⚠️ Success, 2 warnings)
6. Click on second invoice to review warnings
7. See warning details: "Tax rate seems unusual"
8. Continue with remaining invoices
9. Review session summary: 5 total, 4 success, 1 failed
10. Export all results as CSV for analysis

### Property 15: Multiple Invoice Session Tracking

*For any* extraction session, all submitted invoices should be tracked with their status, validation results, and timestamp.

**Validates: Requirements 9.3, 9.4**

### Property 16: Validation Display Completeness

*For any* extraction with validation issues, the UI should display all errors, warnings, and info messages grouped by severity.

**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

## Future Enhancements

1. **Multi-Language Support**: Extract from invoices in multiple languages
2. **PDF Direct Processing**: Accept PDF files directly instead of text
3. **OCR Integration**: Extract from scanned invoice images
4. **Confidence-Based Routing**: Auto-route low-confidence extractions to human review
5. **Learning from Corrections**: Improve extraction based on user corrections
6. **Batch Processing**: Extract from multiple invoices in parallel
7. **Custom Schema Builder**: UI for defining custom invoice schemas
8. **Export Templates**: Customizable export formats for different accounting systems
9. **Duplicate Detection**: Identify duplicate invoices automatically
10. **Anomaly Detection**: Flag unusual patterns in invoice data
11. **Bulk Import**: Upload multiple invoice files at once for batch testing
12. **Comparison View**: Side-by-side comparison of multiple extractions
13. **Validation Rule Editor**: UI for enabling/disabling validation rules
14. **Test Suite Builder**: Save sets of test invoices for regression testing

## Migration Path from Current Implementation

### Phase 1: Add LangExtract Service (Non-Breaking)
- Install langextract and google-generativeai packages
- Create LangExtractService class
- Create InvoiceData schema
- Add database repository for extractions
- **No changes to existing Invoice Agent behavior**

### Phase 2: Add Detection Logic
- Add function to detect if task contains invoice text
- Add feature flag ENABLE_STRUCTURED_EXTRACTION
- **Still no changes to existing behavior when flag is off**

### Phase 3: Enable Extraction
- Update Invoice Agent to call LangExtract when invoice detected
- Combine structured data with AI analysis
- Store extraction results
- **Existing text-only analysis still works for non-invoice tasks**

### Phase 4: Add Export and UI
- Add API endpoints for exporting extraction data
- Update frontend to display structured data
- Add validation error highlighting
- **Backward compatible - old plans still work**

## Example Usage

### Input: Invoice Text

```
INVOICE

Acme Corporation
123 Business St
New York, NY 10001

Invoice #: INV-2024-001
Date: November 15, 2024
Due Date: December 15, 2024

Bill To:
Customer Corp
456 Client Ave
Los Angeles, CA 90001

Description                 Qty    Unit Price    Total
Professional Services       40     $125.00       $5,000.00
Software License           1      $500.00       $500.00

Subtotal:                                        $5,500.00
Tax (8%):                                        $440.00
Total:                                           $5,940.00

Payment Terms: Net 30
```

### Output: Structured Data + Analysis

```json
{
  "success": true,
  "invoice_data": {
    "vendor_name": "Acme Corporation",
    "vendor_address": "123 Business St, New York, NY 10001",
    "invoice_number": "INV-2024-001",
    "invoice_date": "2024-11-15",
    "due_date": "2024-12-15",
    "currency": "USD",
    "subtotal": 5500.00,
    "tax_amount": 440.00,
    "total_amount": 5940.00,
    "line_items": [
      {
        "description": "Professional Services",
        "quantity": 40,
        "unit_price": 125.00,
        "total": 5000.00
      },
      {
        "description": "Software License",
        "quantity": 1,
        "unit_price": 500.00,
        "total": 500.00
      }
    ],
    "payment_terms": "Net 30"
  },
  "validation_errors": [],
  "confidence_scores": {
    "vendor_name": 0.98,
    "invoice_number": 0.99,
    "total_amount": 0.97
  },
  "extraction_time": 2.1,
  "model_used": "gemini-1.5-flash"
}
```

**Formatted Display**:
```
📊 **Extracted Invoice Data**

**Vendor:** Acme Corporation
**Invoice #:** INV-2024-001
**Date:** 2024-11-15
**Due Date:** 2024-12-15
**Total:** USD 5940.00

**Line Items:** (2 items)
  1. Professional Services - 40 × USD125.00 = USD5000.00
  2. Software License - 1 × USD500.00 = USD500.00

⏱️ Extracted in 2.10s using gemini-1.5-flash

**AI Analysis:**
This invoice from Acme Corporation appears to be properly formatted and complete. 
The line items total correctly to the subtotal, and the tax calculation (8%) is 
accurate. Payment terms are Net 30, meaning payment is due by December 15, 2024. 
All required information is present for processing.
```
