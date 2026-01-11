"""
Category-Based Agent Router for Unified Tool Discovery and Execution.

This router replaces brand-specific agent routing with category-based routing
that uses service parameters to route operations to appropriate backends.

**Feature: mcp-client-standardization, Property 5: Interface Consistency**
**Validates: Requirements 2.2, 4.1, 4.2**
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from app.agents.crm_agent import get_crm_agent
from app.agents.email_agent import get_email_agent
from app.agents.accounts_payable_agent import get_accounts_payable_agent
from app.services.mcp_client_service import get_mcp_manager, MCPError

logger = logging.getLogger(__name__)


class CategoryBasedRouter:
    """
    Category-based agent router that provides unified tool discovery and execution.
    
    This router maps functional categories to appropriate agents and services,
    allowing for service-parameterized tool calls while maintaining backward
    compatibility with existing agent node interfaces.
    """
    
    def __init__(self):
        """Initialize the category-based router."""
        self.mcp_manager = get_mcp_manager()
        
        # Category to agent mapping
        self.category_agents = {
            'crm': get_crm_agent(),
            'email': get_email_agent(),
            'accounts_payable': get_accounts_payable_agent()
        }
        
        # Service to category mapping for backward compatibility
        self.service_category_mapping = {
            'salesforce': 'crm',
            'gmail': 'email',
            'zoho': 'accounts_payable',
            'bill_com': 'accounts_payable'
        }
        
        # Category to default service mapping
        self.category_default_services = {
            'crm': 'salesforce',
            'email': 'gmail',
            'accounts_payable': 'zoho'
        }
        
        logger.info(
            "Category-based router initialized",
            extra={
                "categories": list(self.category_agents.keys()),
                "service_mappings": self.service_category_mapping
            }
        )
    
    def get_category_for_service(self, service: str) -> Optional[str]:
        """
        Get the functional category for a given service.
        
        Args:
            service: Service name (e.g., 'salesforce', 'gmail')
            
        Returns:
            Category name or None if not found
        """
        return self.service_category_mapping.get(service)
    
    def get_default_service_for_category(self, category: str) -> Optional[str]:
        """
        Get the default service for a given category.
        
        Args:
            category: Category name (e.g., 'crm', 'email')
            
        Returns:
            Default service name or None if not found
        """
        return self.category_default_services.get(category)
    
    def get_agent_for_category(self, category: str):
        """
        Get the agent instance for a given category.
        
        Args:
            category: Category name (e.g., 'crm', 'email')
            
        Returns:
            Agent instance or None if not found
        """
        return self.category_agents.get(category)
    
    def get_agent_for_service(self, service: str):
        """
        Get the agent instance for a given service.
        
        Args:
            service: Service name (e.g., 'salesforce', 'gmail')
            
        Returns:
            Agent instance or None if not found
        """
        category = self.get_category_for_service(service)
        if category:
            return self.get_agent_for_category(category)
        return None
    
    async def discover_tools_by_category(self, category: str) -> Dict[str, Any]:
        """
        Discover all available tools for a specific category.
        
        Args:
            category: Category name (e.g., 'crm', 'email')
            
        Returns:
            Dictionary containing tool information by service
        """
        try:
            agent = self.get_agent_for_category(category)
            if not agent:
                raise ValueError(f"No agent found for category: {category}")
            
            # Get all services info for this category
            services_info = agent.get_all_services_info()
            
            # Discover tools from MCP manager for each service
            tools_by_service = {}
            for service_id, service_info in services_info.items():
                try:
                    # Get tools from MCP manager
                    service_tools = await self.mcp_manager.discover_tools()
                    if service_id in service_tools:
                        tools_by_service[service_id] = {
                            'service_info': service_info,
                            'tools': service_tools[service_id],
                            'health': await agent.check_service_health(service_id)
                        }
                except Exception as e:
                    logger.warning(f"Failed to discover tools for {service_id}: {e}")
                    tools_by_service[service_id] = {
                        'service_info': service_info,
                        'tools': [],
                        'health': {'is_healthy': False, 'error': str(e)}
                    }
            
            return {
                'category': category,
                'services': tools_by_service,
                'total_services': len(tools_by_service)
            }
            
        except Exception as e:
            logger.error(f"Failed to discover tools for category {category}: {e}")
            return {
                'category': category,
                'services': {},
                'total_services': 0,
                'error': str(e)
            }
    
    async def discover_all_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover all available tools across all categories.
        
        Returns:
            Dictionary mapping categories to their tool information
        """
        all_tools = {}
        
        for category in self.category_agents.keys():
            all_tools[category] = await self.discover_tools_by_category(category)
        
        return all_tools
    
    async def execute_tool_by_category(
        self,
        category: str,
        operation: str,
        service: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a tool operation using category-based routing.
        
        Args:
            category: Category name (e.g., 'crm', 'email')
            operation: Operation name (e.g., 'get_accounts', 'send_message')
            service: Optional service name (uses default if not specified)
            **kwargs: Operation arguments
            
        Returns:
            Operation result
            
        Raises:
            ValueError: If category or operation not supported
            MCPError: If tool execution fails
        """
        try:
            agent = self.get_agent_for_category(category)
            if not agent:
                raise ValueError(f"No agent found for category: {category}")
            
            # Use default service if not specified
            if not service:
                service = self.get_default_service_for_category(category)
                if not service:
                    raise ValueError(f"No default service configured for category: {category}")
            
            # Get the operation method from the agent
            if not hasattr(agent, operation):
                available_ops = [method for method in dir(agent) if not method.startswith('_') and callable(getattr(agent, method))]
                raise ValueError(
                    f"Operation '{operation}' not available for category '{category}'. "
                    f"Available operations: {available_ops}"
                )
            
            operation_method = getattr(agent, operation)
            
            logger.info(
                f"Executing {category}.{operation} via service {service}",
                extra={
                    "category": category,
                    "operation": operation,
                    "service": service,
                    "kwargs": kwargs
                }
            )
            
            # Execute the operation with service parameter
            result = await operation_method(service=service, **kwargs)
            
            logger.info(
                f"Successfully executed {category}.{operation}",
                extra={
                    "category": category,
                    "operation": operation,
                    "service": service,
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to execute {category}.{operation}: {e}",
                extra={
                    "category": category,
                    "operation": operation,
                    "service": service,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise
    
    async def execute_tool_by_service(
        self,
        service: str,
        operation: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a tool operation using service-based routing (backward compatibility).
        
        Args:
            service: Service name (e.g., 'salesforce', 'gmail')
            operation: Operation name (e.g., 'get_accounts', 'send_message')
            **kwargs: Operation arguments
            
        Returns:
            Operation result
            
        Raises:
            ValueError: If service not supported
            MCPError: If tool execution fails
        """
        category = self.get_category_for_service(service)
        if not category:
            raise ValueError(f"No category mapping found for service: {service}")
        
        return await self.execute_tool_by_category(
            category=category,
            operation=operation,
            service=service,
            **kwargs
        )
    
    def get_routing_info(self) -> Dict[str, Any]:
        """
        Get comprehensive routing information.
        
        Returns:
            Dictionary containing routing configuration
        """
        return {
            'categories': list(self.category_agents.keys()),
            'service_mappings': self.service_category_mapping,
            'default_services': self.category_default_services,
            'agents': {
                category: {
                    'class': type(agent).__name__,
                    'supported_services': agent.get_supported_services()
                }
                for category, agent in self.category_agents.items()
            }
        }
    
    async def check_all_services_health(self) -> Dict[str, Dict[str, Any]]:
        """
        Check health status of all services across all categories.
        
        Returns:
            Dictionary mapping categories to service health information
        """
        health_results = {}
        
        for category, agent in self.category_agents.items():
            try:
                health_results[category] = await agent.check_all_services_health()
            except Exception as e:
                logger.error(f"Failed to check health for category {category}: {e}")
                health_results[category] = {'error': str(e)}
        
        return health_results


# Global router instance
_category_router: Optional[CategoryBasedRouter] = None


def get_category_router() -> CategoryBasedRouter:
    """
    Get or create global category-based router instance.
    
    Returns:
        CategoryBasedRouter instance
    """
    global _category_router
    
    if _category_router is None:
        _category_router = CategoryBasedRouter()
    
    return _category_router


# Backward compatibility functions for existing agent nodes
async def route_crm_operation(operation: str, service: str = 'salesforce', **kwargs) -> Dict[str, Any]:
    """Route CRM operations using category-based routing."""
    router = get_category_router()
    return await router.execute_tool_by_category('crm', operation, service, **kwargs)


async def route_email_operation(operation: str, service: str = 'gmail', **kwargs) -> Dict[str, Any]:
    """Route email operations using category-based routing."""
    router = get_category_router()
    return await router.execute_tool_by_category('email', operation, service, **kwargs)


async def route_ap_operation(operation: str, service: str = 'zoho', **kwargs) -> Dict[str, Any]:
    """Route accounts payable operations using category-based routing."""
    router = get_category_router()
    return await router.execute_tool_by_category('accounts_payable', operation, service, **kwargs)


# Enhanced error handling for standardized MCP errors
class CategoryBasedMCPError(MCPError):
    """Enhanced MCP error with category and routing information."""
    
    def __init__(self, message: str, category: str, service: str, operation: str, error_code: str = None):
        super().__init__(message, service, error_code)
        self.category = category
        self.operation = operation
    
    def __str__(self):
        return f"CategoryBasedMCPError[{self.category}.{self.operation}@{self.service}]: {self.args[0]}"


def handle_routing_error(e: Exception, category: str, operation: str, service: str) -> CategoryBasedMCPError:
    """
    Convert generic exceptions to standardized category-based MCP errors.
    
    Args:
        e: Original exception
        category: Category name
        operation: Operation name
        service: Service name
        
    Returns:
        CategoryBasedMCPError instance
    """
    if isinstance(e, MCPError):
        return CategoryBasedMCPError(
            str(e), 
            category, 
            service, 
            operation, 
            e.error_code
        )
    else:
        return CategoryBasedMCPError(
            str(e), 
            category, 
            service, 
            operation, 
            "ROUTING_ERROR"
        )