"""
Bill.com MCP tools service.

This service provides Bill.com API integration tools for invoice data access,
search functionality, and vendor information retrieval.
"""

from typing import Any, Dict, List, Optional
import logging
from datetime import datetime

from core.factory import Domain, MCPToolBase
from services.bill_com_service import get_bill_com_service
from utils.formatters import format_error_response, format_success_response

logger = logging.getLogger(__name__)


class BillComService(MCPToolBase):
    """Bill.com tools for invoice and vendor data access."""

    def __init__(self):
        super().__init__(Domain.BILL_COM)

    def register_tools(self, mcp) -> None:
        """Register Bill.com tools with the MCP server."""

        @mcp.tool(tags={self.domain.value})
        async def get_bill_com_bills(
            limit: int = 20,
            start_date: str | None = None,
            end_date: str | None = None,
            vendor_name: str | None = None,
            status: str | None = None
        ) -> str:
            """
            Get bills from Bill.com with optional filtering.
            
            Args:
                limit: Maximum number of bills (default 20, max 100)
                start_date: Start date filter (YYYY-MM-DD format)
                end_date: End date filter (YYYY-MM-DD format)  
                vendor_name: Filter by vendor name (partial match)
                status: Filter by status (draft, sent, viewed, approved, paid)
            
            Returns:
                Formatted response with bills list and metadata
            """
            try:
                # Use tool context for enhanced logging
                service = await get_bill_com_service(agent="get_bill_com_bills")
                
                # Validate limit
                limit = min(max(1, limit), 100)
                
                # Validate status if provided
                valid_statuses = ["draft", "sent", "viewed", "approved", "paid"]
                if status and status.lower() not in valid_statuses:
                    return format_error_response(
                        f"Invalid status '{status}'. Valid options: {', '.join(valid_statuses)}",
                        "validating bill status filter"
                    )
                
                # Get bills from Bill.com (Bill.com API uses "bills" not "invoices")
                invoices = await service.get_bills(
                    limit=limit,
                    start_date=start_date,
                    end_date=end_date,
                    status=status.lower() if status else None
                )
                
                # Filter by vendor name if provided (client-side filtering)
                if vendor_name and invoices:
                    vendor_name_lower = vendor_name.lower()
                    invoices = [
                        inv for inv in invoices 
                        if vendor_name_lower in inv.get("vendorName", "").lower()
                    ]
                
                # Format response
                formatted_bills = []
                for bill in invoices:
                    formatted_bills.append({
                        "id": bill.get("id"),
                        "invoice_number": bill.get("invoiceNumber"),
                        "vendor_name": bill.get("vendorName"),
                        "invoice_date": bill.get("invoiceDate"),
                        "due_date": bill.get("dueDate"),
                        "total_amount": bill.get("amount"),
                        "status": bill.get("status"),
                        "currency": bill.get("currency", "USD"),
                        "description": bill.get("description", "")
                    })
                
                # Create response details
                details = {
                    "count": len(formatted_bills),
                    "filters_applied": {
                        "limit": limit,
                        "start_date": start_date or "None",
                        "end_date": end_date or "None", 
                        "vendor_name": vendor_name or "None",
                        "status": status or "None"
                    },
                    "bills": formatted_bills,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                summary = f"Retrieved {len(formatted_bills)} bills from Bill.com"
                if vendor_name:
                    summary += f" for vendor '{vendor_name}'"
                if status:
                    summary += f" with status '{status}'"
                
                return format_success_response(
                    action="Bill.com Bills Retrieved",
                    details=details,
                    summary=summary
                )
                
            except Exception as e:
                logger.error(f"Failed to get Bill.com bills: {e}")
                return format_error_response(
                    str(e),
                    "retrieving bills from Bill.com"
                )

        @mcp.tool(tags={self.domain.value})
        async def get_bill_com_invoice_details(invoice_id: str) -> str:
            """
            Get comprehensive detailed information for a specific Bill.com invoice.
            
            This tool retrieves complete invoice details including:
            - Basic invoice information (number, vendor, amounts, dates)
            - Line items with quantities, prices, and account codes
            - Payment history and remaining balance calculations
            - Invoice attachments (URLs and metadata)
            - Approval workflow status and timestamps
            - Data availability indicators for incomplete information
            
            Args:
                invoice_id: Bill.com invoice ID
            
            Returns:
                Formatted response with comprehensive invoice information
            """
            try:
                # Use tool context for enhanced logging
                service = await get_bill_com_service(agent="get_bill_com_invoice_details")
                
                # Get complete invoice details
                complete_details = await service.get_complete_bill_details(invoice_id)
                
                if not complete_details:
                    return format_error_response(
                        f"Invoice {invoice_id} not found or could not be retrieved",
                        "retrieving complete invoice details from Bill.com"
                    )
                
                # Create summary information
                data_availability = complete_details.get("data_availability", {})
                completeness_score = complete_details.get("data_completeness_score", 0.0)
                
                # Build response details
                details = {
                    "invoice": complete_details,
                    "data_summary": {
                        "completeness_score": completeness_score,
                        "available_data": [
                            key for key, available in data_availability.items() 
                            if available
                        ],
                        "missing_data": [
                            key for key, available in data_availability.items() 
                            if not available
                        ]
                    },
                    "financial_summary": {
                        "total_amount": complete_details.get("total_amount", 0),
                        "total_payments": complete_details.get("total_payments", 0),
                        "remaining_balance": complete_details.get("remaining_balance", 0),
                        "is_fully_paid": complete_details.get("is_fully_paid", False)
                    },
                    "counts": {
                        "line_items": complete_details.get("line_items_count", 0),
                        "payments": complete_details.get("payment_count", 0),
                        "attachments": complete_details.get("attachment_count", 0)
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Create contextual summary
                invoice_number = complete_details.get("invoice_number", invoice_id)
                vendor_name = complete_details.get("vendor_name", "Unknown Vendor")
                
                summary_parts = [
                    f"Retrieved comprehensive details for invoice {invoice_number} from {vendor_name}"
                ]
                
                if completeness_score < 1.0:
                    summary_parts.append(f"Data completeness: {int(completeness_score * 100)}%")
                
                if complete_details.get("is_fully_paid"):
                    summary_parts.append("Status: Fully paid")
                elif complete_details.get("remaining_balance", 0) > 0:
                    summary_parts.append(f"Outstanding balance: ${complete_details.get('remaining_balance', 0):.2f}")
                
                summary = " | ".join(summary_parts)
                
                return format_success_response(
                    action="Bill.com Complete Invoice Details Retrieved",
                    details=details,
                    summary=summary
                )
                
            except Exception as e:
                logger.error(f"Failed to get Bill.com complete invoice details for {invoice_id}: {e}")
                return format_error_response(
                    str(e),
                    f"retrieving complete details for invoice {invoice_id}"
                )

        @mcp.tool(tags={self.domain.value})
        async def search_bill_com_bills(
            query: str,
            search_type: str = "invoice_number"
        ) -> str:
            """
            Search Bill.com bills by various criteria.
            
            Args:
                query: Search query string
                search_type: Type of search (invoice_number, vendor_name, amount_range)
            
            Returns:
                Formatted response with search results
            """
            try:
                # Use tool context for enhanced logging
                service = await get_bill_com_service(agent="search_bill_com_bills")
                
                # Validate search type
                valid_search_types = ["invoice_number", "vendor_name", "amount_range"]
                if search_type not in valid_search_types:
                    return format_error_response(
                        f"Invalid search type '{search_type}'. Valid options: {', '.join(valid_search_types)}",
                        "validating search parameters"
                    )
                
                if search_type == "invoice_number":
                    # Search by invoice number
                    invoices = await service.search_bills_by_number(query)
                    
                elif search_type == "vendor_name":
                    # Search by vendor name (get all bills and filter)
                    all_invoices = await service.get_bills(limit=100)
                    query_lower = query.lower()
                    invoices = [
                        inv for inv in all_invoices
                        if query_lower in inv.get("vendorName", "").lower()
                    ]
                    
                elif search_type == "amount_range":
                    # Parse amount range (e.g., "100-500" or ">1000")
                    try:
                        if "-" in query:
                            min_amount, max_amount = map(float, query.split("-"))
                            all_invoices = await service.get_bills(limit=100)
                            invoices = [
                                inv for inv in all_invoices
                                if min_amount <= float(inv.get("amount", 0)) <= max_amount
                            ]
                        elif query.startswith(">"):
                            min_amount = float(query[1:])
                            all_invoices = await service.get_bills(limit=100)
                            invoices = [
                                inv for inv in all_invoices
                                if float(inv.get("amount", 0)) > min_amount
                            ]
                        elif query.startswith("<"):
                            max_amount = float(query[1:])
                            all_invoices = await service.get_bills(limit=100)
                            invoices = [
                                inv for inv in all_invoices
                                if float(inv.get("amount", 0)) < max_amount
                            ]
                        else:
                            exact_amount = float(query)
                            all_invoices = await service.get_bills(limit=100)
                            invoices = [
                                inv for inv in all_invoices
                                if abs(float(inv.get("amount", 0)) - exact_amount) < 0.01
                            ]
                    except ValueError:
                        return format_error_response(
                            f"Invalid amount range format: {query}. Use formats like '100-500', '>1000', '<500', or '250'",
                            "parsing amount range query"
                        )
                
                # Format results
                formatted_bills = []
                for bill in invoices:
                    formatted_bills.append({
                        "id": bill.get("id"),
                        "invoice_number": bill.get("invoiceNumber"),
                        "vendor_name": bill.get("vendorName"),
                        "invoice_date": bill.get("invoiceDate"),
                        "due_date": bill.get("dueDate"),
                        "total_amount": bill.get("amount"),
                        "status": bill.get("status"),
                        "currency": bill.get("currency", "USD")
                    })
                
                details = {
                    "count": len(formatted_bills),
                    "search_query": query,
                    "search_type": search_type,
                    "bills": formatted_bills,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                summary = f"Found {len(formatted_bills)} bills matching {search_type} search for '{query}'"
                
                return format_success_response(
                    action="Bill.com Bill Search Completed",
                    details=details,
                    summary=summary
                )
                
            except Exception as e:
                logger.error(f"Failed to search Bill.com bills: {e}")
                return format_error_response(
                    str(e),
                    f"searching bills with {search_type} for '{query}'"
                )

        @mcp.tool(tags={self.domain.value})
        async def get_bill_com_vendors() -> str:
            """
            Get list of vendors from Bill.com.
            
            Returns:
                Formatted response with vendors list
            """
            try:
                # Use tool context for enhanced logging
                service = await get_bill_com_service(agent="get_bill_com_vendors")
                
                vendors = await service.get_vendors(limit=100)
                
                # Format vendors
                formatted_vendors = []
                for vendor in vendors:
                    formatted_vendors.append({
                        "id": vendor.get("id"),
                        "name": vendor.get("name"),
                        "email": vendor.get("email"),
                        "phone": vendor.get("phone"),
                        "address": vendor.get("address"),
                        "status": "Active" if vendor.get("isActive", True) else "Inactive",
                        "created_time": vendor.get("createdTime")
                    })
                
                details = {
                    "count": len(formatted_vendors),
                    "vendors": formatted_vendors,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                summary = f"Retrieved {len(formatted_vendors)} vendors from Bill.com"
                
                return format_success_response(
                    action="Bill.com Vendors Retrieved",
                    details=details,
                    summary=summary
                )
                
            except Exception as e:
                logger.error(f"Failed to get Bill.com vendors: {e}")
                return format_error_response(
                    str(e),
                    "retrieving vendors from Bill.com"
                )

    @property
    def tool_count(self) -> int:
        """Return the number of tools provided by this service."""
        return 4