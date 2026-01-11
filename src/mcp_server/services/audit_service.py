"""
Audit service manager that provides unified interface for multiple audit providers.
Handles provider registration, selection, and error translation.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Type
import asyncio

from interfaces.audit_provider import (
    AuditProvider, AuditEvent, AuditException, AuditReport,
    AuditEventType, ProviderMetadata
)

logger = logging.getLogger(__name__)


class AuditProviderError(Exception):
    """Base exception for audit provider errors."""
    pass


class ProviderNotFoundError(AuditProviderError):
    """Raised when requested provider is not available."""
    pass


class NoProvidersAvailableError(AuditProviderError):
    """Raised when no audit providers are available."""
    pass


class AuditService:
    """
    Unified audit service that manages multiple audit providers.
    Provides provider-agnostic interface for agents.
    """
    
    def __init__(self):
        self._providers: Dict[str, AuditProvider] = {}
        self._default_provider: Optional[str] = None
        self._fallback_providers: List[str] = []
    
    def register_provider(self, name: str, provider: AuditProvider, is_default: bool = False):
        """
        Register an audit provider.
        
        Args:
            name: Provider name (e.g., 'billcom', 'quickbooks')
            provider: Provider instance
            is_default: Whether this should be the default provider
        """
        self._providers[name] = provider
        
        if is_default or not self._default_provider:
            self._default_provider = name
        
        logger.info(f"Registered audit provider: {name} (default: {is_default})")
    
    def unregister_provider(self, name: str):
        """Unregister an audit provider."""
        if name in self._providers:
            del self._providers[name]
            
            if self._default_provider == name:
                self._default_provider = next(iter(self._providers.keys()), None)
            
            if name in self._fallback_providers:
                self._fallback_providers.remove(name)
            
            logger.info(f"Unregistered audit provider: {name}")
    
    def set_fallback_order(self, provider_names: List[str]):
        """
        Set the fallback order for providers.
        
        Args:
            provider_names: List of provider names in fallback order
        """
        # Validate all providers exist
        for name in provider_names:
            if name not in self._providers:
                raise ProviderNotFoundError(f"Provider '{name}' not registered")
        
        self._fallback_providers = provider_names.copy()
        logger.info(f"Set fallback order: {provider_names}")
    
    def get_available_providers(self) -> Dict[str, ProviderMetadata]:
        """Get metadata for all available providers."""
        return {
            name: provider.metadata 
            for name, provider in self._providers.items()
        }
    
    def get_provider(self, name: Optional[str] = None) -> AuditProvider:
        """
        Get a specific provider or the default provider.
        
        Args:
            name: Provider name (optional, uses default if not specified)
            
        Returns:
            AuditProvider instance
            
        Raises:
            ProviderNotFoundError: If provider doesn't exist
            NoProvidersAvailableError: If no providers are available
        """
        if not self._providers:
            raise NoProvidersAvailableError("No audit providers registered")
        
        if name:
            if name not in self._providers:
                raise ProviderNotFoundError(f"Provider '{name}' not found")
            return self._providers[name]
        
        if self._default_provider:
            return self._providers[self._default_provider]
        
        # Return first available provider if no default set
        return next(iter(self._providers.values()))
    
    async def get_audit_trail(
        self,
        entity_id: str,
        entity_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        limit: Optional[int] = None,
        provider_name: Optional[str] = None
    ) -> List[AuditEvent]:
        """
        Get audit trail using specified or default provider with fallback.
        
        Args:
            entity_id: ID of the entity to audit
            entity_type: Type of entity
            start_date: Start of date range (optional)
            end_date: End of date range (optional)
            event_types: Filter by specific event types (optional)
            limit: Maximum number of events to return (optional)
            provider_name: Specific provider to use (optional)
            
        Returns:
            List of audit events
        """
        providers_to_try = self._get_providers_to_try(provider_name)
        
        for provider_name in providers_to_try:
            try:
                provider = self._providers[provider_name]
                logger.info(f"Attempting audit trail retrieval with provider: {provider_name}")
                
                events = await provider.get_audit_trail(
                    entity_id, entity_type, start_date, end_date, event_types, limit
                )
                
                logger.info(f"Successfully retrieved {len(events)} events from {provider_name}")
                return events
                
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed for audit trail: {e}")
                if provider_name == providers_to_try[-1]:  # Last provider
                    raise AuditProviderError(f"All providers failed. Last error: {e}")
                continue
        
        raise NoProvidersAvailableError("No providers available for audit trail retrieval")
    
    async def get_modification_history(
        self,
        entity_id: str,
        entity_type: str,
        field_names: Optional[List[str]] = None,
        provider_name: Optional[str] = None
    ) -> List[AuditEvent]:
        """Get modification history with provider fallback."""
        providers_to_try = self._get_providers_to_try(provider_name)
        
        for provider_name in providers_to_try:
            try:
                provider = self._providers[provider_name]
                logger.info(f"Attempting modification history with provider: {provider_name}")
                
                events = await provider.get_modification_history(entity_id, entity_type, field_names)
                
                logger.info(f"Successfully retrieved {len(events)} modification events from {provider_name}")
                return events
                
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed for modification history: {e}")
                if provider_name == providers_to_try[-1]:
                    raise AuditProviderError(f"All providers failed. Last error: {e}")
                continue
        
        raise NoProvidersAvailableError("No providers available for modification history")
    
    async def detect_exceptions(
        self,
        entity_type: str,
        criteria: Dict[str, Any],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        provider_name: Optional[str] = None
    ) -> List[AuditException]:
        """Detect exceptions with provider fallback."""
        providers_to_try = self._get_providers_to_try(provider_name)
        
        for provider_name in providers_to_try:
            try:
                provider = self._providers[provider_name]
                logger.info(f"Attempting exception detection with provider: {provider_name}")
                
                exceptions = await provider.detect_exceptions(entity_type, criteria, start_date, end_date)
                
                logger.info(f"Successfully detected {len(exceptions)} exceptions from {provider_name}")
                return exceptions
                
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed for exception detection: {e}")
                if provider_name == providers_to_try[-1]:
                    raise AuditProviderError(f"All providers failed. Last error: {e}")
                continue
        
        raise NoProvidersAvailableError("No providers available for exception detection")
    
    async def generate_audit_report(
        self,
        entity_ids: List[str],
        entity_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_exceptions: bool = True,
        format_type: str = "json",
        provider_name: Optional[str] = None
    ) -> AuditReport:
        """Generate audit report with provider fallback."""
        providers_to_try = self._get_providers_to_try(provider_name)
        
        for provider_name in providers_to_try:
            try:
                provider = self._providers[provider_name]
                logger.info(f"Attempting report generation with provider: {provider_name}")
                
                report = await provider.generate_audit_report(
                    entity_ids, entity_type, start_date, end_date, include_exceptions, format_type
                )
                
                logger.info(f"Successfully generated report from {provider_name}")
                return report
                
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed for report generation: {e}")
                if provider_name == providers_to_try[-1]:
                    raise AuditProviderError(f"All providers failed. Last error: {e}")
                continue
        
        raise NoProvidersAvailableError("No providers available for report generation")
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all registered providers."""
        results = {}
        
        # Run health checks concurrently
        tasks = []
        for name, provider in self._providers.items():
            tasks.append(self._health_check_provider(name, provider))
        
        if tasks:
            health_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, (name, _) in enumerate(self._providers.items()):
                result = health_results[i]
                if isinstance(result, Exception):
                    results[name] = {
                        "status": "error",
                        "error": str(result),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    results[name] = result
        
        return results
    
    async def _health_check_provider(self, name: str, provider: AuditProvider) -> Dict[str, Any]:
        """Check health of a single provider."""
        try:
            result = await provider.health_check()
            result["provider_name"] = name
            return result
        except Exception as e:
            return {
                "provider_name": name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _get_providers_to_try(self, preferred_provider: Optional[str] = None) -> List[str]:
        """Get ordered list of providers to try."""
        if preferred_provider:
            if preferred_provider not in self._providers:
                raise ProviderNotFoundError(f"Provider '{preferred_provider}' not found")
            return [preferred_provider]
        
        providers_to_try = []
        
        # Start with default provider
        if self._default_provider:
            providers_to_try.append(self._default_provider)
        
        # Add fallback providers
        for provider in self._fallback_providers:
            if provider not in providers_to_try and provider in self._providers:
                providers_to_try.append(provider)
        
        # Add any remaining providers
        for provider in self._providers.keys():
            if provider not in providers_to_try:
                providers_to_try.append(provider)
        
        if not providers_to_try:
            raise NoProvidersAvailableError("No audit providers available")
        
        return providers_to_try