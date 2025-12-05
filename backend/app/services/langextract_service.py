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
            
            # Enhanced prompt with line items extraction
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
        - DISCOUNT_AMOUNT: Discount amount as number (if present)
        - SUBTOTAL: Subtotal as number
        - TERMS: Payment terms if stated
        - NOTES: Additional notes if present
        - LINE_ITEMS: A JSON array of line items. Each line item must be a JSON object with:
          * 'description': Item description (string)
          * 'unit_price': Price per unit (number)
          * 'quantity': Number of units (number)
          * 'total': Line item total (number)
        """
            
            # Example with discount and line items to help LLM learn the pattern
            import json
            INVOICE_SNIPPET = (
                "Invoice #: INV-2024-001. Date: 2024-01-15. "
                "From: Tech Solutions Inc., 456 Innovation Dr, SF, CA. "
                "Line Items:\n"
                "2x Consulting Service at $100.00 each = $200.00\n"
                "1x Software License at $50.00 each = $50.00\n"
                "Subtotal: $250.00. Discount: $25.00. Tax: $18.00. Total: $243.00 USD."
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
                        extraction_class="LINE_ITEMS",
                        extraction_text=json.dumps([
                            {
                                "description": "Consulting Service",
                                "unit_price": 100.00,
                                "quantity": 2.0,
                                "total": 200.00
                            },
                            {
                                "description": "Software License",
                                "unit_price": 50.00,
                                "quantity": 1.0,
                                "total": 50.00
                            }
                        ])
                    ),
                    lx.data.Extraction(
                        extraction_class="SUBTOTAL",
                        extraction_text="250.00"
                    ),
                    lx.data.Extraction(
                        extraction_class="DISCOUNT_AMOUNT",
                        extraction_text="25.00"
                    ),
                    lx.data.Extraction(
                        extraction_class="TAX_AMOUNT",
                        extraction_text="18.00"
                    ),
                    lx.data.Extraction(
                        extraction_class="TOTAL_AMOUNT",
                        extraction_text="243.00"
                    ),
                    lx.data.Extraction(
                        extraction_class="CURRENCY",
                        extraction_text="USD"
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
            
            # ===== GENERATE VISUALIZATION =====
            # Generate and store visualization HTML
            try:
                cls.visualize_extraction(annotated_doc, plan_id)
            except Exception as viz_err:
                logger.warning(f"⚠️ Visualization generation failed: {viz_err}")
            
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
                elif field_name == 'discount_amount':
                    try:
                        clean_value = str(field_value).replace(',', '').replace('$', '').strip()
                        extraction_dict['discount_amount'] = Decimal(clean_value)
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
                elif field_name == 'line_items':
                    # Parse LINE_ITEMS JSON array
                    try:
                        import json
                        from app.models.invoice_schema import InvoiceLineItem
                        
                        # Parse the JSON string
                        line_items_data = json.loads(str(field_value))
                        
                        # Convert to InvoiceLineItem objects
                        line_items = []
                        for item_data in line_items_data:
                            try:
                                line_item = InvoiceLineItem(
                                    description=item_data.get('description', ''),
                                    quantity=Decimal(str(item_data.get('quantity', 0))),
                                    unit_price=Decimal(str(item_data.get('unit_price', 0))),
                                    total=Decimal(str(item_data.get('total', 0)))
                                )
                                line_items.append(line_item)
                            except Exception as item_err:
                                logger.warning(f"⚠️ Failed to parse line item: {item_err}")
                                continue
                        
                        if line_items:
                            extraction_dict['line_items'] = line_items
                            logger.info(f"✅ Parsed {len(line_items)} line items")
                        
                    except json.JSONDecodeError as json_err:
                        logger.warning(f"⚠️ Failed to parse LINE_ITEMS JSON: {json_err}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to process LINE_ITEMS: {e}")
            
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
            
            # ===== RUN VALIDATION RULES =====
            logger.info(f"🔍 Running validation rules [plan={plan_id}]")
            validator = InvoiceValidator(invoice_data)
            validation_result = validator.validate()
            
            # Log validation results
            if validation_result['has_errors']:
                logger.warning(f"⚠️ Validation found {len(validation_result['errors'])} errors")
                for error in validation_result['errors']:
                    logger.warning(f"   ERROR: {error}")
            
            if validation_result['has_warnings']:
                logger.info(f"ℹ️ Validation found {len(validation_result['warnings'])} warnings")
                for warning in validation_result['warnings']:
                    logger.info(f"   WARNING: {warning}")
            
            if validation_result['info']:
                logger.info(f"ℹ️ Validation found {len(validation_result['info'])} info messages")
                for info in validation_result['info']:
                    logger.info(f"   INFO: {info}")
            
            # Combine all validation messages
            all_validation_messages = (
                validation_result['errors'] +
                validation_result['warnings'] +
                validation_result['info']
            )
            
            # Determine success - only errors block success, warnings are OK
            success = not validation_result['has_errors']
            
            extraction_time = time.time() - start_time
            logger.info(
                f"{'✅' if success else '❌'} Extraction complete in {extraction_time:.2f}s "
                f"[plan={plan_id}, errors={len(validation_result['errors'])}, "
                f"warnings={len(validation_result['warnings'])}, "
                f"info={len(validation_result['info'])}]"
            )
            
            # IMPORTANT: Return invoice_data even if validation fails
            # This allows users to see what was extracted and fix the issues
            return ExtractionResult(
                success=success,
                invoice_data=invoice_data,  # Always return data, even if validation fails
                validation_errors=all_validation_messages,
                extraction_time=extraction_time,
                model_used=cls._model_name
            )
            
        except Exception as e:
            extraction_time = time.time() - start_time
            
            # Detailed error logging
            logger.error(f"❌ Extraction failed: {type(e).__name__}: {e} [plan={plan_id}]")
            logger.error(f"   Invoice length: {len(invoice_text)} chars")
            logger.error(f"   Model: {cls._model_name}")
            
            # Log full traceback for debugging
            import traceback
            logger.error(f"   Traceback:\n{traceback.format_exc()}")
            
            # User-friendly error message
            error_msg = str(e)
            if "JSON" in error_msg or "parse" in error_msg.lower():
                user_msg = "The AI model returned invalid data. This may be due to invoice complexity. Try a simpler invoice or different model."
            elif "timeout" in error_msg.lower():
                user_msg = "Extraction timed out. The invoice may be too complex."
            elif "API" in error_msg or "key" in error_msg.lower():
                user_msg = "API error. Check your API key and network connection."
            else:
                user_msg = f"Extraction failed: {error_msg}"
            
            return ExtractionResult(
                success=False,
                invoice_data=None,
                validation_errors=[user_msg],
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
        """Format result as text with validation details."""
        lines = []
        
        # Header
        if result.success:
            lines.append("✅ **Extraction Successful**\n")
        else:
            lines.append("❌ **Extraction Failed**\n")
        
        # Invoice data (if available)
        if result.invoice_data:
            invoice = result.invoice_data
            lines.append("📊 **Extracted Invoice Data**\n")
            lines.append(f"**Vendor:** {invoice.vendor_name}")
            if invoice.vendor_address:
                lines.append(f"**Address:** {invoice.vendor_address}")
            lines.append(f"**Invoice #:** {invoice.invoice_number}")
            lines.append(f"**Date:** {invoice.invoice_date}")
            if invoice.due_date:
                lines.append(f"**Due Date:** {invoice.due_date}")
            lines.append(f"**Subtotal:** {invoice.currency} {invoice.subtotal}")
            if invoice.tax_amount:
                lines.append(f"**Tax:** {invoice.currency} {invoice.tax_amount}")
            if invoice.discount_amount:
                lines.append(f"**Discount:** {invoice.currency} {invoice.discount_amount}")
            lines.append(f"**Total:** {invoice.currency} {invoice.total_amount}")
            
            if invoice.line_items:
                lines.append(f"\n**Line Items:** ({len(invoice.line_items)} items)")
                for i, item in enumerate(invoice.line_items, 1):
                    lines.append(
                        f"  {i}. {item.description} - "
                        f"{item.quantity} × {invoice.currency}{item.unit_price} = "
                        f"{invoice.currency}{item.total}"
                    )
            
            if invoice.payment_terms:
                lines.append(f"\n**Payment Terms:** {invoice.payment_terms}")
            
            if invoice.notes:
                lines.append(f"**Notes:** {invoice.notes}")
        
        # Validation results (grouped by severity)
        if result.validation_errors:
            lines.append("\n" + "="*50)
            lines.append("**Validation Results**\n")
            
            # Separate by severity
            errors = [msg for msg in result.validation_errors if msg.startswith('[') and 'Check]' in msg and any(
                rule in msg for rule in ['Date Ordering', 'Total Calculation', 'Positive Amounts', 'Required Fields']
            )]
            warnings = [msg for msg in result.validation_errors if msg.startswith('[') and 'Check]' in msg and any(
                rule in msg for rule in ['Line Items Sum', 'Future Date', 'Tax Rate']
            )]
            info = [msg for msg in result.validation_errors if msg.startswith('[') and 'Check]' in msg and any(
                rule in msg for rule in ['Vendor Name Length', 'Duplicate Line Items']
            )]
            
            # If we can't categorize, treat as errors
            uncategorized = [msg for msg in result.validation_errors if msg not in errors + warnings + info]
            errors.extend(uncategorized)
            
            if errors:
                lines.append(f"❌ **ERRORS ({len(errors)})**")
                for error in errors:
                    lines.append(f"  • {error}")
                lines.append("")
            
            if warnings:
                lines.append(f"⚠️  **WARNINGS ({len(warnings)})**")
                for warning in warnings:
                    lines.append(f"  • {warning}")
                lines.append("")
            
            if info:
                lines.append(f"ℹ️  **INFO ({len(info)})**")
                for i in info:
                    lines.append(f"  • {i}")
                lines.append("")
        
        # Metadata
        lines.append("="*50)
        lines.append(f"⏱️ Extracted in {result.extraction_time:.2f}s using Nolij AI Invoice Model")
        
        return "\n".join(lines)
    
    # Visualization storage
    _visualizations: dict = {}
    _annotated_docs: dict = {}
    
    @classmethod
    def visualize_extraction(cls, annotated_doc, plan_id: str = None):
        """
        Generate HTML visualization of extraction with highlighted text.
        Shows start_char and end_char for each extracted field.
        
        Args:
            annotated_doc: The AnnotatedDocument from lx.extract()
            plan_id: Plan ID for storage and retrieval
            
        Returns:
            HTML string with visualization
        """
        try:
            logger.info(f"🎨 Generating visualization [plan={plan_id}]")
            
            # Store the annotated doc for later retrieval
            if plan_id:
                cls._annotated_docs[plan_id] = annotated_doc
            
            # Use langextract's built-in visualization
            import langextract as lx
            html_content = lx.visualize(annotated_doc)
            
            # Store the visualization
            if plan_id:
                cls._visualizations[plan_id] = html_content
            
            logger.info(f"✅ Visualization generated [plan={plan_id}]")
            return html_content
            
        except Exception as e:
            logger.error(f"❌ Visualization failed [plan={plan_id}]: {e}")
            
            # Return fallback HTML with error message
            return f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>Visualization Error</h2>
                <p>Failed to generate visualization: {str(e)}</p>
                <p>The extraction may have succeeded, but visualization failed.</p>
            </body>
            </html>
            """
    
    @classmethod
    def get_visualization(cls, plan_id: str):
        """
        Get stored visualization HTML for a plan.
        
        Args:
            plan_id: Plan ID to retrieve visualization for
            
        Returns:
            HTML string or None if not found
        """
        visualization = cls._visualizations.get(plan_id)
        
        if visualization:
            logger.debug(f"✅ Retrieved visualization [plan={plan_id}]")
        else:
            logger.debug(f"⚠️ No visualization found [plan={plan_id}]")
        
        return visualization
    
    @classmethod
    def get_annotated_doc(cls, plan_id: str):
        """
        Get stored annotated document for a plan.
        
        Args:
            plan_id: Plan ID to retrieve document for
            
        Returns:
            AnnotatedDocument or None if not found
        """
        return cls._annotated_docs.get(plan_id)
    
    @classmethod
    def reset(cls):
        """Reset service."""
        cls._initialized = False
        cls._model_name = None
        logger.info("Service reset")
