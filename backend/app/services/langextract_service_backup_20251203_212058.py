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
from langextract.data import ExampleData
from app.models.invoice_schema import InvoiceData
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
    _visualizations: Dict[str, str] = {}  # Cache for HTML visualizations by plan_id
    _annotated_docs: Dict[str, Any] = {}  # Cache for AnnotatedDocuments by plan_id
    

   

    
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
            logger.info(f"📊 ===== EXTRACTION START ===== [plan={plan_id}]")
            logger.info(f"📊 Invoice length: {len(invoice_text)} chars [plan={plan_id}]")
            logger.info(f"📊 Model: {cls._model_name} [plan={plan_id}]")
            
            # Define extraction prompt - simplified to reduce JSON parsing errors
            prompt = """Extract invoice entities. Only extract what is explicitly present in the text.

CRITICAL: Do NOT include null, None, or empty values. Omit any entity not found.

Extract these entities:
- INVOICE_ID: Invoice number (e.g., "INV-001")
- INVOICE_DATE: Date in YYYY-MM-DD format only
- VENDOR_NAME: Vendor company name
- VENDOR_ADDRESS: Full vendor address if present
- TOTAL_AMOUNT: Total as number without $ or commas (e.g., "1000.00")
- CURRENCY: Currency code (e.g., "USD")
- DUE_DATE: Due date in YYYY-MM-DD format only
- TAX_AMOUNT: Tax as number without $ or commas
- SUBTOTAL: Subtotal as number without $ or commas
- TERMS: Payment terms (e.g., "Net 30")
- NOTES: Additional notes if present

Return only valid JSON. Use simple string values."""
            
            # Create simple example (DataCamp style)
            INVOICE_SNIPPET = (
                "Invoice #: INV-2024-001. Date: 2024-01-15. "
                "From: Tech Solutions Inc., 456 Innovation Dr, SF, CA. "
                "Total: $5,940.00 USD. Subtotal: $5,500.00. Tax: $440.00."
            )
            
            example = lx.data.ExampleData(
                text=INVOICE_SNIPPET,
                extractions=[
                    lx.data.Extraction(
                        extraction_class="INVOICE_ID",
                        extraction_text="INV-2024-001"
                    ),
                    lx.data.Extraction(
                        extraction_class="INVOICE_DATE",
                        extraction_text="2024-01-15"
                    ),
                    lx.data.Extraction(
                        extraction_class="VENDOR_NAME",
                        extraction_text="Tech Solutions Inc."
                    ),
                    lx.data.Extraction(
                        extraction_class="TOTAL_AMOUNT",
                        extraction_text="5940.00"
                    ),
                    lx.data.Extraction(
                        extraction_class="CURRENCY",
                        extraction_text="USD"
                    ),
                    lx.data.Extraction(
                        extraction_class="SUBTOTAL",
                        extraction_text="5500.00"
                    ),
                    lx.data.Extraction(
                        extraction_class="TAX_AMOUNT",
                        extraction_text="440.00"
                    ),
                ]
            )
            
            logger.info(f"🔍 Extracting from {len(invoice_text)} chars [plan={plan_id}]")
            
            # Call langextract with timeout handling
            import asyncio
            import concurrent.futures
            
            # Create a wrapper function for extraction with retry logic
            def extract_with_logging():
                logger.info(f"🔄 Thread started - calling lx.extract() [plan={plan_id}]")
                extraction_start = time.time()
                
                # Try extraction with retry on JSON parsing errors
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        if attempt > 0:
                            logger.info(f"🔄 Retry attempt {attempt + 1}/{max_retries} [plan={plan_id}]")
                        
                        result = lx.extract(
                            invoice_text,
                            prompt_description=prompt,
                            examples=[example],
                            model_id=cls._model_name,
                            debug=False
                        )
                        extraction_elapsed = time.time() - extraction_start
                        logger.info(f"✅ lx.extract() completed in {extraction_elapsed:.2f}s [plan={plan_id}]")
                        return result
                        
                    except Exception as e:
                        error_name = type(e).__name__
                        error_msg = str(e)
                        
                        # Check if it's a JSON parsing error
                        is_json_error = (
                            "ResolverParsingError" in error_name or
                            "JSON" in error_msg or
                            "parse" in error_msg.lower()
                        )
                        
                        if is_json_error and attempt < max_retries - 1:
                            logger.warning(f"⚠️ JSON parsing error on attempt {attempt + 1}, retrying... [plan={plan_id}]")
                            continue
                        else:
                            extraction_elapsed = time.time() - extraction_start
                            logger.error(f"❌ lx.extract() failed after {extraction_elapsed:.2f}s: {error_name}: {error_msg} [plan={plan_id}]")
                            raise
            
            try:
                # Get the current event loop
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.get_event_loop()
                
                # Run extraction in thread pool with timeout
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = loop.run_in_executor(executor, extract_with_logging)
                    
                    # Wait with timeout (90 seconds)
                    logger.info(f"⏱️ Waiting for extraction (timeout=90s) [plan={plan_id}]")
                    annotated_doc = await asyncio.wait_for(future, timeout=90.0)
                    logger.info(f"✅ Extraction returned successfully [plan={plan_id}]")
                    
            except asyncio.TimeoutError:
                logger.error(f"❌ Extraction timed out after 90s [plan={plan_id}]")
                raise ValueError("Extraction timed out after 90 seconds. The invoice may be too large or complex.")
            except concurrent.futures.CancelledError:
                logger.error(f"❌ Extraction was cancelled [plan={plan_id}]")
                raise ValueError("Extraction was cancelled")
            except Exception as e:
                logger.error(f"❌ Extraction error: {type(e).__name__}: {e} [plan={plan_id}]")
                raise
            
            # Log extraction results
            extraction_count = len(annotated_doc.extractions) if annotated_doc and annotated_doc.extractions else 0
            logger.info(f"✅ Extracted {extraction_count} entities [plan={plan_id}]")
            
            extraction_time = time.time() - start_time
            
            # Validate extraction results
            if not annotated_doc:
                raise ValueError("No extraction result returned from langextract")
            
            if not annotated_doc.extractions or len(annotated_doc.extractions) == 0:
                logger.warning(f"No extractions found in result [plan={plan_id}]")
                raise ValueError("No entities extracted from invoice. The invoice format may not be recognized.")
            
            # Build InvoiceData from entity-level extractions
            from datetime import date
            from decimal import Decimal, InvalidOperation
            
            extraction_dict = {}
            field_mapping = {
                'invoice_id': 'invoice_number',
                'invoice_date': 'invoice_date',
                'vendor_name': 'vendor_name',
                'vendor_address': 'vendor_address',
                'total_amount': 'total_amount',
                'currency': 'currency',
                'due_date': 'due_date',
                'tax_amount': 'tax_amount',
                'subtotal': 'subtotal',
                'terms': 'payment_terms',
                'notes': 'notes'
            }
            
            for extraction in annotated_doc.extractions:
                field_name = extraction.extraction_class.lower()
                field_value = extraction.extraction_text
                
                # Skip null, None, or empty values
                if not field_value or str(field_value).strip() in ('', 'null', 'None', 'N/A'):
                    continue
                
                if field_name in field_mapping:
                    mapped_name = field_mapping[field_name]
                    
                    try:
                        # Convert date strings to date objects
                        if 'date' in mapped_name:
                            extraction_dict[mapped_name] = date.fromisoformat(str(field_value).strip())
                        # Convert amounts to Decimal
                        elif 'amount' in mapped_name or mapped_name == 'subtotal':
                            # Clean numeric string (remove commas, currency symbols)
                            clean_value = str(field_value).replace(',', '').replace('$', '').strip()
                            extraction_dict[mapped_name] = Decimal(clean_value)
                        else:
                            extraction_dict[mapped_name] = str(field_value).strip()
                    except (ValueError, InvalidOperation) as e:
                        logger.warning(f"Failed to convert {field_name}='{field_value}': {e}")
                        continue
            
            # Validate required fields before creating InvoiceData
            required_fields = ['invoice_number', 'invoice_date', 'vendor_name', 'total_amount', 'subtotal']
            missing_fields = [f for f in required_fields if f not in extraction_dict]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Create InvoiceData with extracted fields
            invoice_data = InvoiceData(**extraction_dict)
            logger.info(f"📄 Invoice: {invoice_data.invoice_number} | Vendor: {invoice_data.vendor_name} | Total: {invoice_data.currency} {invoice_data.total_amount}")
            
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
            
            status_icon = '✅' if success else '⚠️'
            logger.info(
                f"{status_icon} Completed in {extraction_time:.2f}s | "
                f"Errors: {len(validation_result['errors'])} | "
                f"Warnings: {len(validation_result['warnings'])} [plan={plan_id}]"
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
                    html_content = cls.visualize_extraction(annotated_doc, plan_id)
                    if html_content and plan_id:
                        cls._visualizations[plan_id] = html_content
                        logger.info(f"📊 Visualization cached ({len(html_content)} bytes) [plan={plan_id}]")
                except Exception as viz_error:
                    logger.warning(f"Visualization failed: {viz_error} [plan={plan_id}]")
            
            return extraction_result
            
        except Exception as e:
            extraction_time = time.time() - start_time
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"❌ Extraction failed: {error_type}: {error_msg} [plan={plan_id}]")
            
            # Provide user-friendly error messages based on error type
            if "timeout" in error_msg.lower():
                user_msg = "Extraction timed out. The invoice may be too complex or the service is slow."
            elif "ResolverParsingError" in error_type or "JSON" in error_msg or "parse" in error_msg.lower():
                user_msg = (
                    "Failed to parse the AI response. This can happen with complex invoice formats. "
                    "Please try simplifying the invoice or contact support."
                )
            elif "missing required fields" in error_msg.lower():
                user_msg = f"Could not extract all required invoice fields. {error_msg}"
            elif "no entities extracted" in error_msg.lower():
                user_msg = "No invoice data could be extracted. Please check the invoice format."
            elif "API" in error_msg or "key" in error_msg.lower():
                user_msg = "API authentication error. Please check your API key configuration."
            else:
                user_msg = f"Extraction failed: {error_msg}"
            
            return ExtractionResult(
                success=False,
                invoice_data=None,
                validation_errors=[user_msg],
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
                return None
            
            # Use langextract's built-in visualize function
            html_content = lx.visualize(annotated_doc)
            return html_content
            
        except Exception as e:
            logger.warning(f"Visualization failed: {e}")
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
        cls._initialized = False
        cls._visualizations = {}
        cls._annotated_docs = {}
        logger.info("LangExtract service reset")
