"""
Email Agent Factory for Multi-Provider Support.

This module provides factory functions and utilities for creating email agents
with different providers while maintaining a consistent interface.

**Feature: multi-agent-invoice-workflow, Multi-Provider Support**
**Validates: Requirements FR2.1, NFR3.4**
"""

import logging
from typing import Dict, Any, Optional, List
from .email_agent import EmailAgent, get_email_agent
from .gmail_agent_node import EmailAgentNode, GmailAgentNode

logger = logging.getLogger(__name__)


class EmailAgentFactory:
    """
    Factory class for creating email agents with different providers.
    
    This factory provides a centralized way to create email agents for different
    services while ensuring consistent configuration and error handling.
    """
    
    @staticmethod
    def create_email_agent(service: str = 'gmail', **kwargs) -> EmailAgentNode:
        """
        Create an EmailAgentNode for the specified service.
        
        Args:
            service: Email service to use ('gmail', 'outlook', 'exchange')
            **kwargs: Additional configuration parameters
            
        Returns:
            EmailAgentNode instance configured for the service
            
        Raises:
            ValueError: If service is not supported
        """
        try:
            # Validate service is supported
            email_agent = get_email_agent()
            if not email_agent.is_service_available(service):
                supported = email_agent.get_supported_services()
                raise ValueError(
                    f"Service '{service}' is not available. "
                    f"Supported services: {supported}"
                )
            
            # Create agent node
            agent_node = EmailAgentNode(service=service)
            
            logger.info(
                f"Created EmailAgentNode for {service}",
                extra={
                    "service": service,
                    "factory": "EmailAgentFactory",
                    "kwargs": kwargs
                }
            )
            
            return agent_node
            
        except Exception as e:
            logger.error(
                f"Failed to create EmailAgentNode for {service}: {e}",
                extra={
                    "service": service,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise
    
    @staticmethod
    def create_gmail_agent() -> GmailAgentNode:
        """
        Create a GmailAgentNode for backward compatibility.
        
        Returns:
            GmailAgentNode instance
        """
        return GmailAgentNode()
    
    @staticmethod
    def create_outlook_agent() -> EmailAgentNode:
        """
        Create an EmailAgentNode configured for Outlook.
        
        Returns:
            EmailAgentNode instance configured for Outlook
            
        Raises:
            ValueError: If Outlook service is not available
        """
        return EmailAgentFactory.create_email_agent('outlook')
    
    @staticmethod
    def create_exchange_agent() -> EmailAgentNode:
        """
        Create an EmailAgentNode configured for Exchange.
        
        Returns:
            EmailAgentNode instance configured for Exchange
            
        Raises:
            ValueError: If Exchange service is not available
        """
        return EmailAgentFactory.create_email_agent('exchange')
    
    @staticmethod
    def get_supported_services() -> List[str]:
        """
        Get list of supported email services.
        
        Returns:
            List of supported service names
        """
        email_agent = get_email_agent()
        return email_agent.get_supported_services()
    
    @staticmethod
    def get_service_info(service: str) -> Dict[str, Any]:
        """
        Get information about a specific email service.
        
        Args:
            service: Service name
            
        Returns:
            Dictionary containing service information
        """
        email_agent = get_email_agent()
        return email_agent.get_service_info(service)
    
    @staticmethod
    def get_all_services_info() -> Dict[str, Dict[str, Any]]:
        """
        Get information about all supported email services.
        
        Returns:
            Dictionary mapping service names to their information
        """
        email_agent = get_email_agent()
        return email_agent.get_all_services_info()
    
    @staticmethod
    async def check_service_health(service: str) -> Dict[str, Any]:
        """
        Check health status of a specific email service.
        
        Args:
            service: Service name
            
        Returns:
            Dictionary containing health status
        """
        email_agent = get_email_agent()
        return await email_agent.check_service_health(service)
    
    @staticmethod
    async def check_all_services_health() -> Dict[str, Dict[str, Any]]:
        """
        Check health status of all email services.
        
        Returns:
            Dictionary mapping service names to their health status
        """
        email_agent = get_email_agent()
        return await email_agent.check_all_services_health()


def get_email_agent_for_service(service: str) -> EmailAgentNode:
    """
    Convenience function to get an email agent for a specific service.
    
    Args:
        service: Email service name
        
    Returns:
        EmailAgentNode instance
    """
    return EmailAgentFactory.create_email_agent(service)


def get_gmail_agent_node() -> GmailAgentNode:
    """
    Convenience function to get a Gmail agent node for backward compatibility.
    
    Returns:
        GmailAgentNode instance
    """
    return EmailAgentFactory.create_gmail_agent()


# Service-specific convenience functions
def get_outlook_agent_node() -> EmailAgentNode:
    """Get Outlook email agent node."""
    return EmailAgentFactory.create_outlook_agent()


def get_exchange_agent_node() -> EmailAgentNode:
    """Get Exchange email agent node."""
    return EmailAgentFactory.create_exchange_agent()


# Configuration helpers
def get_email_service_config(service: str) -> Dict[str, Any]:
    """
    Get configuration information for an email service.
    
    Args:
        service: Service name
        
    Returns:
        Service configuration dictionary
    """
    return EmailAgentFactory.get_service_info(service)


def list_available_email_services() -> List[str]:
    """
    List all available email services.
    
    Returns:
        List of service names
    """
    return EmailAgentFactory.get_supported_services()


async def validate_email_service_availability(service: str) -> bool:
    """
    Validate that an email service is available and healthy.
    
    Args:
        service: Service name
        
    Returns:
        True if service is available and healthy, False otherwise
    """
    try:
        health_status = await EmailAgentFactory.check_service_health(service)
        return health_status.get('is_healthy', False)
    except Exception as e:
        logger.error(f"Failed to validate service {service}: {e}")
        return False