"""Pydantic models for invoice data extraction."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from decimal import Decimal


class InvoiceLineItem(BaseModel):
    """Single line item on an invoice."""
    description: str = Field(..., description="Item description")
    quantity: Decimal = Field(..., description="Quantity ordered")
    unit_price: Decimal = Field(..., description="Price per unit")
    total: Decimal = Field(..., description="Line item total")
    
    class Config:
        json_schema_extra = {
            "example": {
                "description": "Professional Services",
                "quantity": 40,
                "unit_price": 125.00,
                "total": 5000.00
            }
        }


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
    discount_amount: Optional[Decimal] = Field(None, description="Discount amount")
    total_amount: Decimal = Field(..., description="Total amount due")
    line_items: List[InvoiceLineItem] = Field(default_factory=list, description="Invoice line items")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    class Config:
        json_schema_extra = {
            "example": {
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
                    }
                ],
                "payment_terms": "Net 30"
            }
        }


class ExtractionResult(BaseModel):
    """Result of invoice extraction."""
    success: bool = Field(..., description="Whether extraction was successful")
    invoice_data: Optional[InvoiceData] = Field(None, description="Extracted invoice data")
    validation_errors: List[str] = Field(default_factory=list, description="Validation error messages")
    confidence_scores: dict = Field(default_factory=dict, description="Confidence scores for extracted fields")
    extraction_time: float = Field(..., description="Time taken for extraction in seconds")
    model_used: str = Field(..., description="Model used for extraction")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "invoice_data": {
                    "vendor_name": "Acme Corp",
                    "invoice_number": "INV-001",
                    "invoice_date": "2024-11-15",
                    "total_amount": 5000.00,
                    "currency": "USD"
                },
                "validation_errors": [],
                "confidence_scores": {
                    "vendor_name": 0.98,
                    "invoice_number": 0.99
                },
                "extraction_time": 2.1,
                "model_used": "gemini-1.5-flash"
            }
        }
