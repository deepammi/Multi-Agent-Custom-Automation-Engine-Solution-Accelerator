"""
Bill.com health tools service for MCP server integration.
Provides health check and configuration validation tools.
"""

import logging
from typing import Dict, Any

from core.bill_com_health_tools import (
    bill_com_health_check,
    bill_com_config_validation,
    bill_com_setup_guide,
    bill_com_connection_test,
    bill_com_diagnostics
)
from core.factory import MCPToolBase, Domain

logger = logging.getLogger(__name__)


class BillComHealthToolsService(MCPToolBase):
    """Service that provides Bill.com health check functionality as MCP tools."""
    
    def __init__(self):
        super().__init__(Domain.GENERAL)
        logger.info("BillComHealthToolsService initialized")
    
    def register_tools(self, mcp) -> None:
        """Register Bill.com health tools with the MCP server."""
        
        @mcp.tool(tags={self.domain.value})
        async def bill_com_health_check_tool(comprehensive: bool = False) -> str:
            """Check Bill.com service health and connectivity."""
            return await self.bill_com_health_check(comprehensive)
        
        @mcp.tool(tags={self.domain.value})
        async def bill_com_config_validation_tool() -> str:
            """Validate Bill.com configuration and environment variables."""
            return await self.bill_com_config_validation()
        
        @mcp.tool(tags={self.domain.value})
        async def bill_com_setup_guide_tool() -> str:
            """Get Bill.com setup instructions and configuration guide."""
            return await self.bill_com_setup_guide()
        
        @mcp.tool(tags={self.domain.value})
        async def bill_com_connection_test_tool() -> str:
            """Test Bill.com API connection and basic functionality."""
            return await self.bill_com_connection_test()
        
        @mcp.tool(tags={self.domain.value})
        async def bill_com_diagnostics_tool() -> str:
            """Get comprehensive Bill.com integration diagnostics."""
            return await self.bill_com_diagnostics()
    
    @property
    def tool_count(self) -> int:
        """Return the number of tools provided by this service."""
        return 5
    
    async def bill_com_health_check(self, comprehensive: bool = False) -> str:
        """
        Check Bill.com service health and connectivity.
        
        Args:
            comprehensive: If True, performs full health check. If False, uses cached results when available.
        
        Returns:
            JSON string containing health status and diagnostics
        """
        return await bill_com_health_check(comprehensive=comprehensive)
    
    async def bill_com_config_validation(self) -> str:
        """
        Validate Bill.com configuration and environment variables.
        
        Returns:
            JSON string containing configuration validation results
        """
        return await bill_com_config_validation()
    
    async def bill_com_setup_guide(self) -> str:
        """
        Get Bill.com setup instructions and configuration guide.
        
        Returns:
            JSON string containing setup instructions
        """
        return await bill_com_setup_guide()
    
    async def bill_com_connection_test(self) -> str:
        """
        Test Bill.com API connection and basic functionality.
        
        Returns:
            JSON string containing connection test results
        """
        return await bill_com_connection_test()
    
    async def bill_com_diagnostics(self) -> str:
        """
        Get comprehensive Bill.com integration diagnostics.
        
        Returns:
            JSON string containing detailed diagnostic information
        """
        return await bill_com_diagnostics()