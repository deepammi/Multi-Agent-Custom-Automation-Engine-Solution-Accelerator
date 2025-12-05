"""LangExtract service for structured invoice data extraction.

This service uses the langextract library which provides:
- Strict schema adherence
- Built-in validation
- Automatic visualization
- Support for multiple LLM providers
"""
import logging
import os
import time
from typing import Optional, Dict, Any
from datetime import datetime

import langextract as lx
from app.models.invoice_schema import InvoiceData ## looks wrong. Should be from lx.data library
from app.config.validation_rules import InvoiceValidator

logger = logging.getLogger(__name__)


class ExtractionResult:
    """Result of invoice extraction."""
    
    def __init__(
        self,
        success: bool,
        invoice_data: Optional[InvoiceData],
        validation_errors: list,
        extraction_time: float,
        model_used: str,
        confidence_scores: dict = None
    ):
        self.success = success
        self.invoice_data = invoice_data
        self.validation_errors = validation_errors
        self.extraction_time = extraction_time
        self.model_used = model_used
        self.confidence_scores = confidence_scores or {}


class LangExtractService:
    """Service for structured invoice data extraction using LangExtract library."""
    
    _initialized: bool = False
    _extractor: Optional[Any] = None
    _model_name: Optional[str] = None
    _schema: Optional[Any] = None
    _api_key: Optional[str] = None
    _examples: list = []
    _visualizations: Dict[str, str] = {}  # Cache for HTML visualizations by plan_id
    _annotated_docs: Dict[str, Any] = {}  # Cache for AnnotatedDocuments by plan_id
    

    
    @classmethod
    def _create_examples(cls):
        """Create example data for langextract."""
        from decimal import Decimal
        from datetime import date
        from app.models.invoice_schema import InvoiceLineItem ##?? check this code to understtand
        
        # Create example extractions
        examples = []
        
        # Example 1: Invoice with line items showing proper structure
        ## ?? Looks wrong compared to examples. It should follow lx.data.Extractions() class to define instead of InvoiceData
        example1_text = """INVOICE

        Acme Corporation
        123 Business Street
        New York, NY 10001

        Invoice Number: INV-2024-001
        Invoice Date: January 15, 2024
        Due Date: February 15, 2024

        DESCRIPTION                 QTY    UNIT PRICE    TOTAL
        Professional Services        40      $125.00    $5,000.00
        Software License              1      $500.00      $500.00

                           SUBTOTAL:           $5,500.00
                           TAX (8%):             $440.00
                           TOTAL:              $5,940.00

        Payment Terms: Net 30"""
        
        example1_data = InvoiceData(
            vendor_name="Acme Corporation",
            vendor_address="123 Business Street, New York, NY 10001",
            invoice_number="INV-2024-001",
            invoice_date=date(2024, 1, 15),
            due_date=date(2024, 2, 15),
            currency="USD",
            subtotal=Decimal("5500.00"),
            tax_amount=Decimal("440.00"),
            total_amount=Decimal("5940.00"),
            line_items=[
                InvoiceLineItem(
                    description="Professional Services",
                    quantity=Decimal("40"),
                    unit_price=Decimal("125.00"),
                    total=Decimal("5000.00")
                ),
                InvoiceLineItem(
                    description="Software License",
                    quantity=Decimal("1"),
                    unit_price=Decimal("500.00"),
                    total=Decimal("500.00")
                )
            ],
            payment_terms="Net 30",
            notes=None
        )
        
        # Create Extraction object with extraction_class and extraction_text
        extraction1 = lx.data.Extraction(
            extraction_class="InvoiceData",
            extraction_text=example1_data.model_dump_json()
        )
        
        examples.append(lx.data.ExampleData(
            text=example1_text,
            extractions=[extraction1]
        ))
        
        return examples
    
    @classmethod
    def initialize(cls):
        """
        Initialize LangExtract with Gemini configuration.
        
        Raises:
            ValueError: If GEMINI_API_KEY is not set or initialization fails
        """
        if cls._initialized:
            logger.info("LangExtract service already initialized")
            return
        
        logger.info("Initializing LangExtract service...")
        
        # Check for API key
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY or GEMINI_API_KEY environment variable is required. "
                "Please set it in your .env file."
            )
        
        try:
            # Set API key for langextract (it looks for LANGEXTRACT_API_KEY)
            os.environ["LANGEXTRACT_API_KEY"] = api_key
            os.environ["GOOGLE_API_KEY"] = api_key
            
            # Get model preference
            cls._model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
            
            # Store the schema for later use
            cls._schema = InvoiceData
            
            # Store API key for passing to extract function
            cls._api_key = api_key
            
            # Create examples for langextract
            cls._examples = cls._create_examples()
            
            cls._initialized = True
            logger.info(f"✅ LangExtract initialized successfully with {cls._model_name}")
            
        except Exception as e:
            error_msg = f"Failed to initialize LangExtract: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if service is initialized."""
        return cls._initialized


    @classmethod
    async def extract_invoice_data(
        cls,
        invoice_text: str,
        plan_id: str = None
    ) -> ExtractionResult:
        """
        Extract structured invoice data using langextract library.
        
        Args:
            invoice_text: Raw invoice text to extract from
            plan_id: Optional plan identifier for tracking
            
        Returns:
            ExtractionResult with extracted data and validation results
        """
        if not cls._initialized:
            cls.initialize()
        
        start_time = time.time()
        
        try:
            logger.info(f"📊 Starting langextract extraction [plan_id={plan_id}]")
            
            # Use langextract to extract data
            # For Gemini with schema constraints: format_type must be JSON
            # The API key should be set in LANGEXTRACT_API_KEY environment variable
            # Enable fuzzy alignment to ensure extractions are aligned with source text
            from langextract.data import FormatType
            
            logger.info("Calling lx.extract with Gemini structured output...")
            annotated_doc = lx.extract(
                invoice_text,
                cls._schema,  # Pass schema as 2nd positional arg (prompt_description accepts schema)
                examples=cls._examples,
                format_type=FormatType.JSON,  # Must be JSON for Gemini structured output
                model_id=cls._model_name,
                use_schema_constraints=True,  # Enable schema constraints for Gemini
                resolver_params={
                    'enable_fuzzy_alignment': True,
                    'fuzzy_alignment_threshold': 0.75,
                    'accept_match_lesser': True
                },
                debug=False  # Set to True to see detailed langextract logs
            )
            logger.info(f"lx.extract returned: type={type(annotated_doc)}, has_text={hasattr(annotated_doc, 'text')}")
            
            extraction_time = time.time() - start_time
            
            # langextract returns an AnnotatedDocument with extractions attribute
            if annotated_doc and annotated_doc.extractions and len(annotated_doc.extractions) > 0:
                # Get the first extraction
                extraction = annotated_doc.extractions[0]
                # The extraction has extraction_text which is JSON string
                import json
                extraction_dict = json.loads(extraction.extraction_text)
                # Parse into InvoiceData model
                invoice_data = InvoiceData(**extraction_dict)
            else:
                raise ValueError("No extraction result returned")
            
            # Perform additional custom validation
            validator = InvoiceValidator(invoice_data)
            validation_result = validator.validate()
            
            # Determine success based on validation errors
            success = len(validation_result['errors']) == 0
            
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
            
            extraction_result = ExtractionResult(
                success=success,
                invoice_data=invoice_data,  # Always include data
                validation_errors=all_validation_messages,
                extraction_time=extraction_time,
                model_used=cls._model_name or "unknown"
            )
            
            # Store the annotated document for visualization
            if plan_id:
                cls._annotated_docs[plan_id] = annotated_doc
            
            # Generate visualization if enabled
            if os.getenv("ENABLE_EXTRACTION_VISUALIZATION", "false").lower() == "true":
                try:
                    logger.info(f"Generating visualization for plan {plan_id}...")
                    html_content = cls.visualize_extraction(annotated_doc, plan_id)
                    if html_content and plan_id:
                        cls._visualizations[plan_id] = html_content
                        logger.info(f"📊 Visualization cached for plan {plan_id} ({len(html_content)} bytes)")
                    else:
                        logger.warning(f"Visualization generation returned empty for plan {plan_id}")
                except Exception as viz_error:
                    logger.error(f"Failed to generate visualization for plan {plan_id}: {viz_error}")
            else:
                logger.debug("Visualization disabled via ENABLE_EXTRACTION_VISUALIZATION")
            
            return extraction_result
            
        except Exception as e:
            extraction_time = time.time() - start_time
            logger.error(f"❌ Extraction failed [plan_id={plan_id}]: {e}")
            
            return ExtractionResult(
                success=False,
                invoice_data=None,
                validation_errors=[f"Extraction failed: {str(e)}"],
                extraction_time=extraction_time,
                model_used=cls._model_name or "unknown"
            )
    
    @classmethod
    def format_extraction_result(cls, result) -> str:
        """
        Format extraction result as human-readable text.
        
        Args:
            result: ExtractionResult instance
            
        Returns:
            Formatted string for display
        """
        if not result.success:
            output = ["❌ **Extraction Failed**\n"]
            output.append("**Errors:**")
            for error in result.validation_errors:
                output.append(f"  - {error}")
            return "\n".join(output)
        
        invoice = result.invoice_data
        output = []
        
        output.append("📊 **Extracted Invoice Data**\n")
        output.append(f"**Vendor:** {invoice.vendor_name}")
        if invoice.vendor_address:
            output.append(f"**Address:** {invoice.vendor_address}")
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
        
        if invoice.payment_terms:
            output.append(f"\n**Payment Terms:** {invoice.payment_terms}")
        
        if result.validation_errors:
            output.append(f"\n⚠️ **Validation Issues:**")
            for error in result.validation_errors:
                output.append(f"  - {error}")
        
        output.append(
            f"\n⏱️ Extracted in {result.extraction_time:.2f}s using {result.model_used}"
        )
        
        return "\n".join(output)
    
    @classmethod
    def visualize_extraction(cls, annotated_doc: Any, plan_id: str = None) -> Optional[str]:
        """
        Create HTML visualization using langextract's built-in visualize() method.
        
        Args:
            annotated_doc: AnnotatedDocument from langextract
            plan_id: Plan identifier (used for logging)
            
        Returns:
            HTML content as string, or None if failed
        """
        try:
            if not annotated_doc:
                logger.warning("No annotated document to visualize")
                return None
            
            # Debug: Check if extractions have alignment data
            logger.info(f"Annotated doc has {len(annotated_doc.extractions) if annotated_doc.extractions else 0} extractions")
            if annotated_doc.extractions:
                for i, ext in enumerate(annotated_doc.extractions):
                    logger.info(f"Extraction {i}: char_interval={ext.char_interval}, alignment_status={ext.alignment_status}")
            
            # Use langextract's built-in visualize function
            # This will show the original text with highlighted extractions
            html_content = lx.visualize(annotated_doc)
            
            logger.info(f"✅ Visualization generated for plan {plan_id} ({len(html_content)} bytes)")
            return html_content
            
        except Exception as e:
            logger.error(f"Failed to create visualization: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @classmethod
    def get_visualization(cls, plan_id: str) -> Optional[str]:
        """
        Get cached visualization HTML for a plan.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            HTML content or None if not found
        """
        return cls._visualizations.get(plan_id)
    
    @classmethod
    def reset(cls):
        """Reset the service (useful for testing or reconfiguration)."""
        cls._extractor = None
        cls._model_name = None
        cls._schema = None
        cls._api_key = None
        cls._examples = []
        cls._initialized = False
        cls._visualizations = {}
        cls._annotated_docs = {}
        logger.info("LangExtract service reset")
