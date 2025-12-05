"""
ULTRA-SIMPLIFIED LangExtract service
Matches EXACTLY the working test_langextract_raw.py pattern
NO DEVIATIONS from the working test
"""
import logging
import os
import time
from typing import Optional
from datetime import date
from decimal import Decimal

import langextract as lx
from app.models.invoice_schema import InvoiceData

logger = logging.getLogger(__name__)


class ExtractionResult:
    """Result of invoice extraction."""
    
    def __init__(
        self,
        success: bool,
        invoice_data: Optional[InvoiceData],
        validation_errors: list,
        extraction_time: float,
        model_used: str
    ):
        self.success = success
        self.invoice_data = invoice_data
        self.validation_errors = validation_errors
        self.extraction_time = extraction_time
        self.model_used = model_used


class LangExtractService:
    """Service matching EXACTLY the working test pattern."""
    
    _initialized: bool = False
    _model_name: str = None
    
    @classmethod
    def initialize(cls):
        """Initialize - EXACT same as working test."""
        if cls._initialized:
            return
        
        # Get API key
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY required")
        
        # Set for langextract - EXACT same as working test
        os.environ["LANGEXTRACT_API_KEY"] = api_key
        os.environ["GOOGLE_API_KEY"] = api_key
        
        # Get model - NO DEFAULT, use exactly what's in .env
        cls._model_name = os.getenv("GEMINI_MODEL")
        if not cls._model_name:
            raise ValueError("GEMINI_MODEL environment variable is required")
        
        cls._initialized = True
        logger.info(f"✅ Initialized with {cls._model_name}")
    
    @classmethod
    def extract_invoice_data_sync(
        cls,
        invoice_text: str,
        plan_id: str = None
    ) -> ExtractionResult:
        """
        Extract invoice data - SYNCHRONOUS VERSION.
        EXACT same as working test_langextract_raw.py
        """
        if not cls._initialized:
            cls.initialize()
        
        start_time = time.time()
        
        try:
            logger.info(f"📊 Starting extraction [plan={plan_id}]")
            
            # EXACT SAME PROMPT as working test
            prompt = """
        Extract invoice entities from the text. Only extract entities that are explicitly present.
        
        **IMPORTANT: Do NOT return null or None values. If an entity is not found, omit it.**
        
        Extract these entities:
        - INVOICE_ID: Invoice number
        - INVOICE_DATE: Invoice date in YYYY-MM-DD format
        - VENDOR_NAME: Vendor company name
        - VENDOR_ADDRESS: Vendor address
        - TOTAL_AMOUNT: Total amount as number without currency symbol
        - CURRENCY: Currency code (e.g., 'USD')
        - DUE_DATE: Due date in YYYY-MM-DD format
        - TAX_AMOUNT: Tax amount as number
        - SUBTOTAL: Subtotal as number
        - TERMS: Payment terms if stated
        - NOTES: Additional notes if present
        """
            
            # EXACT SAME EXAMPLE as working test
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
            
            # ===== INPUT VALIDATION & DEBUG =====
            logger.info(f"🔍 Validating inputs before lx.extract() [plan={plan_id}]")
            
            # 1. Validate invoice_text
            if not invoice_text:
                raise ValueError("invoice_text is empty or None")
            if not isinstance(invoice_text, str):
                raise ValueError(f"invoice_text must be string, got {type(invoice_text)}")
            
            # Check encoding
            try:
                invoice_text.encode('utf-8')
                logger.info(f"✅ invoice_text is valid UTF-8 ({len(invoice_text)} chars)")
            except UnicodeEncodeError as e:
                raise ValueError(f"invoice_text has invalid UTF-8 encoding: {e}")
            
            # 2. Validate prompt
            if not prompt or not isinstance(prompt, str):
                raise ValueError("prompt is empty or not a string")
            logger.info(f"✅ prompt is valid ({len(prompt)} chars)")
            
            # 3. Validate example
            if not example:
                raise ValueError("example is None")
            if not isinstance(example, lx.data.ExampleData):
                raise ValueError(f"example must be ExampleData, got {type(example)}")
            if not example.text:
                raise ValueError("example.text is empty")
            if not example.extractions:
                raise ValueError("example.extractions is empty")
            logger.info(f"✅ example is valid ({len(example.extractions)} extractions)")
            
            # 4. Validate model_id
            if not cls._model_name:
                raise ValueError("model_name is not set")
            logger.info(f"✅ model_id is valid: {cls._model_name}")
            
            # 5. Debug: Print first 200 chars of invoice
            preview = invoice_text[:200].replace('\n', '\\n')
            logger.info(f"📄 Invoice preview: {preview}...")
            
            # 6. Debug: Check for common JSON issues in invoice text
            if invoice_text.strip().startswith('{') or invoice_text.strip().startswith('['):
                logger.warning(f"⚠️ Invoice text looks like JSON - this might cause issues")
            
            # All validations passed
            logger.info(f"✅ All inputs validated successfully [plan={plan_id}]")
            logger.info(f"🔍 Calling lx.extract() [plan={plan_id}]")
            
            # Enable debug to see what's happening
            debug_mode = os.getenv("LANGEXTRACT_DEBUG", "false").lower() == "true"
            
            # EXACT SAME CALL as working test - NO ASYNC
            try:
                annotated_doc = lx.extract(
                    invoice_text,
                    prompt_description=prompt,
                    examples=[example],
                    model_id=cls._model_name,
                    debug=debug_mode
                )
            except Exception as extract_error:
                # Log the error details
                logger.error(f"❌ lx.extract() failed: {extract_error}")
                logger.error(f"   Error type: {type(extract_error).__name__}")
                
                # Check if it's a JSON parsing error
                error_str = str(extract_error)
                if "JSON" in error_str or "parse" in error_str.lower():
                    logger.error(f"   This is a JSON parsing error from langextract library")
                    logger.error(f"   The LLM likely returned malformed JSON")
                    logger.error(f"   Invoice length: {len(invoice_text)} chars")
                
                raise
            
            logger.info(f"✅ lx.extract() returned [plan={plan_id}]")
            
            # ===== OUTPUT VALIDATION & DEBUG =====
            logger.info(f"🔍 Validating lx.extract() output [plan={plan_id}]")
            
            # 1. Check annotated_doc exists
            if not annotated_doc:
                raise ValueError("lx.extract() returned None")
            logger.info(f"✅ annotated_doc exists: {type(annotated_doc)}")
            
            # 2. Check has extractions attribute
            if not hasattr(annotated_doc, 'extractions'):
                raise ValueError("annotated_doc has no 'extractions' attribute")
            logger.info(f"✅ annotated_doc has extractions attribute")
            
            # 3. Check extractions is not empty
            if not annotated_doc.extractions:
                raise ValueError("annotated_doc.extractions is empty or None")
            logger.info(f"✅ Got {len(annotated_doc.extractions)} extractions")
            
            # 4. Debug: Print each extraction
            for i, ext in enumerate(annotated_doc.extractions, 1):
                logger.info(f"   Extraction {i}: {ext.extraction_class} = '{ext.extraction_text}'")
            
            # ===== BUILD INVOICE DATA =====
            logger.info(f"🔨 Building InvoiceData from extractions [plan={plan_id}]")
            extraction_dict = {}
            
            for extraction in annotated_doc.extractions:
                field_name = extraction.extraction_class.lower()
                field_value = extraction.extraction_text
                
                # Skip empty
                if not field_value or str(field_value).strip() == '':
                    continue
                
                # Map to InvoiceData fields
                if field_name == 'invoice_id':
                    extraction_dict['invoice_number'] = str(field_value).strip()
                elif field_name == 'invoice_date':
                    try:
                        extraction_dict['invoice_date'] = date.fromisoformat(str(field_value).strip())
                    except:
                        pass
                elif field_name == 'vendor_name':
                    extraction_dict['vendor_name'] = str(field_value).strip()
                elif field_name == 'vendor_address':
                    extraction_dict['vendor_address'] = str(field_value).strip()
                elif field_name == 'total_amount':
                    try:
                        clean_value = str(field_value).replace(',', '').replace('$', '').strip()
                        extraction_dict['total_amount'] = Decimal(clean_value)
                    except:
                        pass
                elif field_name == 'currency':
                    extraction_dict['currency'] = str(field_value).strip()
                elif field_name == 'due_date':
                    try:
                        extraction_dict['due_date'] = date.fromisoformat(str(field_value).strip())
                    except:
                        pass
                elif field_name == 'tax_amount':
                    try:
                        clean_value = str(field_value).replace(',', '').replace('$', '').strip()
                        extraction_dict['tax_amount'] = Decimal(clean_value)
                    except:
                        pass
                elif field_name == 'subtotal':
                    try:
                        clean_value = str(field_value).replace(',', '').replace('$', '').strip()
                        extraction_dict['subtotal'] = Decimal(clean_value)
                    except:
                        pass
                elif field_name == 'terms':
                    extraction_dict['payment_terms'] = str(field_value).strip()
                elif field_name == 'notes':
                    extraction_dict['notes'] = str(field_value).strip()
            
            # Check required fields
            required = ['invoice_number', 'invoice_date', 'vendor_name', 'total_amount', 'subtotal']
            missing = [f for f in required if f not in extraction_dict]
            
            if missing:
                logger.error(f"❌ Missing required fields: {missing}")
                logger.error(f"   Available fields: {list(extraction_dict.keys())}")
                raise ValueError(f"Missing required fields: {', '.join(missing)}")
            
            logger.info(f"✅ All required fields present: {list(extraction_dict.keys())}")
            
            # Create InvoiceData with validation
            try:
                logger.info(f"🔨 Creating InvoiceData object [plan={plan_id}]")
                invoice_data = InvoiceData(**extraction_dict)
                logger.info(f"✅ InvoiceData created successfully")
                
                # Validate it can be serialized to JSON (common issue)
                import json
                try:
                    json.dumps(invoice_data.model_dump(), default=str)
                    logger.info(f"✅ InvoiceData is JSON-serializable")
                except Exception as json_err:
                    logger.warning(f"⚠️ InvoiceData cannot be JSON-serialized: {json_err}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to create InvoiceData: {e}")
                logger.error(f"   extraction_dict: {extraction_dict}")
                raise
            
            extraction_time = time.time() - start_time
            logger.info(f"✅ Extraction complete in {extraction_time:.2f}s [plan={plan_id}]")
            
            return ExtractionResult(
                success=True,
                invoice_data=invoice_data,
                validation_errors=[],
                extraction_time=extraction_time,
                model_used=cls._model_name
            )
            
        except Exception as e:
            extraction_time = time.time() - start_time
            logger.error(f"❌ Extraction failed: {e} [plan={plan_id}]")
            
            return ExtractionResult(
                success=False,
                invoice_data=None,
                validation_errors=[f"Extraction failed: {str(e)}"],
                extraction_time=extraction_time,
                model_used=cls._model_name
            )
    
    @classmethod
    async def extract_invoice_data(
        cls,
        invoice_text: str,
        plan_id: str = None
    ) -> ExtractionResult:
        """
        Async wrapper around sync extraction.
        Just runs sync version in thread pool.
        """
        import asyncio
        return await asyncio.to_thread(
            cls.extract_invoice_data_sync,
            invoice_text,
            plan_id
        )
    
    @classmethod
    def format_extraction_result(cls, result: ExtractionResult) -> str:
        """Format result as text."""
        if not result.success:
            return f"❌ Extraction Failed\n\nErrors:\n" + "\n".join(f"  - {e}" for e in result.validation_errors)
        
        invoice = result.invoice_data
        lines = [
            "📊 **Extracted Invoice Data**\n",
            f"**Vendor:** {invoice.vendor_name}",
            f"**Invoice #:** {invoice.invoice_number}",
            f"**Date:** {invoice.invoice_date}",
            f"**Total:** {invoice.currency} {invoice.total_amount}",
        ]
        
        if invoice.vendor_address:
            lines.insert(2, f"**Address:** {invoice.vendor_address}")
        if invoice.due_date:
            lines.insert(-1, f"**Due Date:** {invoice.due_date}")
        if invoice.payment_terms:
            lines.append(f"\n**Payment Terms:** {invoice.payment_terms}")
        
        lines.append(f"\n⏱️ Extracted in {result.extraction_time:.2f}s using {result.model_used}")
        
        return "\n".join(lines)
    
    @classmethod
    def reset(cls):
        """Reset service."""
        cls._initialized = False
        cls._model_name = None
        logger.info("Service reset")
