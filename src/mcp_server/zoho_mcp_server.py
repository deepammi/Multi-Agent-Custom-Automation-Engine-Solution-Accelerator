#!/usr/bin/env python3
"""
Zoho Invoice MCP Server

This server provides MCP (Model Context Protocol) access to Zoho Invoice functionality.
It replaces direct HTTP requests with proper MCP protocol implementation.

**Feature: mcp-client-standardization, Property 1: MCP Protocol Compliance**
**Validates: Requirements 1.1, 1.3, 1.5**
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

# Add the parent directories to the path to import services
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.append(grandparent_dir)

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP SDK not available. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Import Zoho service
from backend.app.services.zoho_mcp_service import ZohoMCPService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("zoho-invoice")

# Global Zoho service instance
zoho_service: Optional[ZohoMCPService] = None


async def get_zoho_service() -> ZohoMCPService:
    """Get or create Zoho service instance."""
    global zoho_service
    
    if zoho_service is None:
        zoho_service = ZohoMCPService()
        await zoho_service.initialize()
    
    return zoho_service


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available Zoho Invoice tools."""
    return [
        Tool(
            name="zoho_list_invoices",
            description="List invoices from Zoho Invoice with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by invoice status (sent, paid, overdue, draft, etc.)",
                        "enum": ["sent", "paid", "overdue", "draft", "void", "unpaid"]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of invoices to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date filter in YYYY-MM-DD format"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date filter in YYYY-MM-DD format"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="zoho_get_invoice",
            description="Get detailed information about a specific invoice",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {
                        "type": "string",
                        "description": "Zoho invoice ID or invoice number (e.g., 'INV-000001')"
                    }
                },
                "required": ["invoice_id"]
            }
        ),
        Tool(
            name="zoho_list_customers",
            description="List customers/contacts from Zoho Invoice",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of customers to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by customer status",
                        "enum": ["active", "inactive"]
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="zoho_get_customer",
            description="Get detailed information about a specific customer",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Zoho customer/contact ID"
                    }
                },
                "required": ["customer_id"]
            }
        ),
        Tool(
            name="zoho_search_invoices",
            description="Search invoices in Zoho Invoice",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "Search term or query"
                    },
                    "search_type": {
                        "type": "string",
                        "description": "Type of search to perform",
                        "enum": ["invoice_number", "customer_name", "amount", "all"],
                        "default": "all"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": ["search_term"]
            }
        ),
        Tool(
            name="zoho_get_invoice_summary",
            description="Get summary statistics for invoices in Zoho Invoice",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_breakdown": {
                        "type": "boolean",
                        "description": "Include status breakdown in summary",
                        "default": True
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="zoho_list_payments",
            description="List payments from Zoho Invoice",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of payments to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date filter in YYYY-MM-DD format"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date filter in YYYY-MM-DD format"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="zoho_get_payment",
            description="Get detailed information about a specific payment",
            inputSchema={
                "type": "object",
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "description": "Zoho payment ID"
                    }
                },
                "required": ["payment_id"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls for Zoho Invoice operations."""
    try:
        service = await get_zoho_service()
        
        logger.info(f"Calling Zoho tool: {name} with arguments: {arguments}")
        
        if name == "zoho_list_invoices":
            result = await service.list_invoices(
                status=arguments.get("status"),
                limit=arguments.get("limit", 10)
            )
        
        elif name == "zoho_get_invoice":
            result = await service.get_invoice(
                invoice_identifier=arguments["invoice_id"]
            )
        
        elif name == "zoho_list_customers":
            result = await service.list_customers(
                limit=arguments.get("limit", 10)
            )
        
        elif name == "zoho_get_customer":
            # This would need to be implemented in ZohoMCPService
            result = {
                "success": False,
                "error": "get_customer not yet implemented in ZohoMCPService"
            }
        
        elif name == "zoho_search_invoices":
            search_term = arguments["search_term"]
            search_type = arguments.get("search_type", "all")
            limit = arguments.get("limit", 10)
            
            # For now, use list_invoices and filter results
            # This could be enhanced with proper search API
            all_invoices = await service.list_invoices(limit=100)
            
            if all_invoices.get("success"):
                invoices = all_invoices.get("invoices", [])
                
                # Filter based on search type
                filtered_invoices = []
                search_lower = search_term.lower()
                
                for invoice in invoices:
                    match = False
                    
                    if search_type in ["invoice_number", "all"]:
                        if search_lower in invoice.get("invoice_number", "").lower():
                            match = True
                    
                    if search_type in ["customer_name", "all"]:
                        if search_lower in invoice.get("customer_name", "").lower():
                            match = True
                    
                    if search_type in ["amount", "all"]:
                        if search_term in str(invoice.get("total", 0)):
                            match = True
                    
                    if match:
                        filtered_invoices.append(invoice)
                
                # Apply limit
                filtered_invoices = filtered_invoices[:limit]
                
                result = {
                    "success": True,
                    "invoices": filtered_invoices,
                    "total": len(filtered_invoices),
                    "search_term": search_term,
                    "search_type": search_type
                }
            else:
                result = all_invoices
        
        elif name == "zoho_get_invoice_summary":
            result = await service.get_invoice_summary()
        
        elif name == "zoho_list_payments":
            # This would need to be implemented in ZohoMCPService
            result = {
                "success": False,
                "error": "list_payments not yet implemented in ZohoMCPService"
            }
        
        elif name == "zoho_get_payment":
            # This would need to be implemented in ZohoMCPService
            result = {
                "success": False,
                "error": "get_payment not yet implemented in ZohoMCPService"
            }
        
        else:
            result = {
                "success": False,
                "error": f"Unknown tool: {name}"
            }
        
        logger.info(f"Zoho tool {name} completed with success: {result.get('success', False)}")
        
        # Return result as JSON string
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error calling Zoho tool {name}: {e}", exc_info=True)
        
        error_result = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "tool_name": name
        }
        
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def main():
    """Main entry point for the Zoho MCP server."""
    logger.info("Starting Zoho Invoice MCP Server...")
    
    # Verify Zoho service can be initialized
    try:
        service = await get_zoho_service()
        logger.info(f"Zoho service initialized. Enabled: {service.is_enabled()}, Mock mode: {service.is_mock_mode()}")
    except Exception as e:
        logger.error(f"Failed to initialize Zoho service: {e}")
        # Continue anyway - service might work in mock mode
    
    # Run the MCP server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Zoho Invoice MCP Server is running...")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Zoho Invoice MCP Server stopped by user")
    except Exception as e:
        logger.error(f"Zoho Invoice MCP Server error: {e}", exc_info=True)
        sys.exit(1)