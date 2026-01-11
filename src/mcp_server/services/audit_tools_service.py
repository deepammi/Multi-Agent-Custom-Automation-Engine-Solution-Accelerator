"""
Audit tools service for MCP server integration.
Provides audit functionality as MCP tools.
"""

import logging
from typing import Dict, Any

from core.audit_tools import (
    get_audit_trail,
    get_modification_history,
    detect_audit_exceptions,
    generate_audit_report,
    get_audit_providers,
    audit_health_check
)
from core.factory import MCPToolBase, Domain

logger = logging.getLogger(__name__)


class AuditToolsService(MCPToolBase):
    """Service that provides audit functionality as MCP tools."""
    
    def __init__(self):
        super().__init__(Domain.GENERAL)
        logger.info("AuditToolsService initialized")
    
    def register_tools(self, mcp) -> None:
        """Register audit tools with the MCP server."""
        
        @mcp.tool(tags={self.domain.value})
        async def get_audit_trail_tool(
            entity_id: str,
            entity_type: str,
            start_date: str = None,
            end_date: str = None,
            event_types: str = None,
            limit: int = None,
            provider: str = None
        ) -> str:
            """Retrieve audit trail for a specific entity."""
            return await self.get_audit_trail(
                entity_id, entity_type, start_date, end_date, event_types, limit, provider
            )
        
        @mcp.tool(tags={self.domain.value})
        async def get_modification_history_tool(
            entity_id: str,
            entity_type: str,
            field_names: str = None,
            provider: str = None
        ) -> str:
            """Get detailed modification history for an entity."""
            return await self.get_modification_history(entity_id, entity_type, field_names, provider)
        
        @mcp.tool(tags={self.domain.value})
        async def detect_audit_exceptions_tool(
            entity_type: str,
            criteria: str = None,
            start_date: str = None,
            end_date: str = None,
            severity_filter: str = None,
            provider: str = None
        ) -> str:
            """Detect audit exceptions based on criteria."""
            return await self.detect_audit_exceptions(
                entity_type, criteria, start_date, end_date, severity_filter, provider
            )
        
        @mcp.tool(tags={self.domain.value})
        async def generate_audit_report_tool(
            entity_ids: str,
            entity_type: str,
            start_date: str = None,
            end_date: str = None,
            include_exceptions: bool = True,
            format_type: str = "json",
            provider: str = None
        ) -> str:
            """Generate comprehensive audit report."""
            return await self.generate_audit_report(
                entity_ids, entity_type, start_date, end_date, include_exceptions, format_type, provider
            )
        
        @mcp.tool(tags={self.domain.value})
        async def get_audit_providers_tool() -> str:
            """Get information about available audit providers."""
            return await self.get_audit_providers()
        
        @mcp.tool(tags={self.domain.value})
        async def audit_health_check_tool(provider: str = None) -> str:
            """Check health of audit providers."""
            return await self.audit_health_check(provider)
    
    @property
    def tool_count(self) -> int:
        """Return the number of tools provided by this service."""
        return 6
    
    async def get_audit_trail(
        self,
        entity_id: str,
        entity_type: str,
        start_date: str = None,
        end_date: str = None,
        event_types: str = None,
        limit: int = None,
        provider: str = None
    ) -> str:
        """
        Retrieve audit trail for a specific entity.
        
        Args:
            entity_id: ID of the entity to audit (e.g., invoice ID)
            entity_type: Type of entity (invoice, vendor, payment, bill)
            start_date: Start date in ISO format (optional)
            end_date: End date in ISO format (optional)
            event_types: Comma-separated list of event types to filter (optional)
            limit: Maximum number of events to return (optional)
            provider: Specific audit provider to use (optional)
        
        Returns:
            JSON string containing audit events
        """
        return await get_audit_trail(
            entity_id=entity_id,
            entity_type=entity_type,
            start_date=start_date,
            end_date=end_date,
            event_types=event_types,
            limit=limit,
            provider=provider
        )
    
    async def get_modification_history(
        self,
        entity_id: str,
        entity_type: str,
        field_names: str = None,
        provider: str = None
    ) -> str:
        """
        Get detailed modification history for an entity.
        
        Args:
            entity_id: ID of the entity
            entity_type: Type of entity (invoice, vendor, payment, bill)
            field_names: Comma-separated list of field names to track (optional)
            provider: Specific audit provider to use (optional)
        
        Returns:
            JSON string containing modification events with old/new values
        """
        return await get_modification_history(
            entity_id=entity_id,
            entity_type=entity_type,
            field_names=field_names,
            provider=provider
        )
    
    async def detect_audit_exceptions(
        self,
        entity_type: str,
        criteria: str = None,
        start_date: str = None,
        end_date: str = None,
        severity_filter: str = None,
        provider: str = None
    ) -> str:
        """
        Detect audit exceptions based on criteria.
        
        Args:
            entity_type: Type of entities to check (invoice, vendor, payment, bill)
            criteria: JSON string with exception detection criteria (optional)
            start_date: Start date in ISO format (optional)
            end_date: End date in ISO format (optional)
            severity_filter: Filter by severity (low, medium, high, critical) (optional)
            provider: Specific audit provider to use (optional)
        
        Returns:
            JSON string containing detected exceptions
        """
        return await detect_audit_exceptions(
            entity_type=entity_type,
            criteria=criteria,
            start_date=start_date,
            end_date=end_date,
            severity_filter=severity_filter,
            provider=provider
        )
    
    async def generate_audit_report(
        self,
        entity_ids: str,
        entity_type: str,
        start_date: str = None,
        end_date: str = None,
        include_exceptions: bool = True,
        format_type: str = "json",
        provider: str = None
    ) -> str:
        """
        Generate comprehensive audit report.
        
        Args:
            entity_ids: Comma-separated list of entity IDs to include
            entity_type: Type of entities (invoice, vendor, payment, bill)
            start_date: Start date in ISO format (optional)
            end_date: End date in ISO format (optional)
            include_exceptions: Whether to include exception detection (default: True)
            format_type: Output format (json, summary) (default: json)
            provider: Specific audit provider to use (optional)
        
        Returns:
            JSON string containing comprehensive audit report
        """
        return await generate_audit_report(
            entity_ids=entity_ids,
            entity_type=entity_type,
            start_date=start_date,
            end_date=end_date,
            include_exceptions=include_exceptions,
            format_type=format_type,
            provider=provider
        )
    
    async def get_audit_providers(self) -> str:
        """
        Get information about available audit providers.
        
        Returns:
            JSON string containing provider information and capabilities
        """
        return await get_audit_providers()
    
    async def audit_health_check(self, provider: str = None) -> str:
        """
        Check health of audit providers.
        
        Args:
            provider: Specific provider to check (optional, checks all if not specified)
        
        Returns:
            JSON string containing health status
        """
        return await audit_health_check(provider=provider)