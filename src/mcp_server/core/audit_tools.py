"""
Generic audit MCP tools that work with any audit provider.
Provides provider-agnostic audit functionality for agents.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from services.audit_service import AuditService, AuditProviderError
from interfaces.audit_provider import AuditEventType, ExceptionSeverity

logger = logging.getLogger(__name__)

# Global audit service instance
audit_service: Optional[AuditService] = None


def initialize_audit_service(service: AuditService):
    """Initialize the global audit service instance."""
    global audit_service
    audit_service = service
    logger.info("Audit service initialized for MCP tools")


async def get_audit_trail(
    entity_id: str,
    entity_type: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    event_types: Optional[str] = None,
    limit: Optional[int] = None,
    provider: Optional[str] = None
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
    if not audit_service:
        return json.dumps({"error": "Audit service not initialized"})
    
    try:
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Parse event types
        event_type_list = None
        if event_types:
            try:
                event_type_list = [
                    AuditEventType(event_type.strip().lower()) 
                    for event_type in event_types.split(',')
                ]
            except ValueError as e:
                return json.dumps({"error": f"Invalid event type: {e}"})
        
        # Get audit trail
        events = await audit_service.get_audit_trail(
            entity_id=entity_id,
            entity_type=entity_type,
            start_date=start_dt,
            end_date=end_dt,
            event_types=event_type_list,
            limit=limit,
            provider_name=provider
        )
        
        # Convert to JSON-serializable format
        events_data = []
        for event in events:
            events_data.append({
                "event_id": event.event_id,
                "entity_id": event.entity_id,
                "entity_type": event.entity_type,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "user_id": event.user_id,
                "user_name": event.user_name,
                "description": event.description,
                "old_values": event.old_values,
                "new_values": event.new_values,
                "metadata": event.metadata
            })
        
        result = {
            "success": True,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "events_count": len(events),
            "events": events_data
        }
        
        logger.info(f"Retrieved {len(events)} audit events for {entity_type} {entity_id}")
        return json.dumps(result, indent=2)
        
    except AuditProviderError as e:
        logger.error(f"Audit provider error: {e}")
        return json.dumps({"error": f"Audit provider error: {e}"})
    except Exception as e:
        logger.error(f"Error retrieving audit trail: {e}")
        return json.dumps({"error": f"Failed to retrieve audit trail: {e}"})


async def get_modification_history(
    entity_id: str,
    entity_type: str,
    field_names: Optional[str] = None,
    provider: Optional[str] = None
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
    if not audit_service:
        return json.dumps({"error": "Audit service not initialized"})
    
    try:
        # Parse field names
        field_list = None
        if field_names:
            field_list = [field.strip() for field in field_names.split(',')]
        
        # Get modification history
        events = await audit_service.get_modification_history(
            entity_id=entity_id,
            entity_type=entity_type,
            field_names=field_list,
            provider_name=provider
        )
        
        # Convert to JSON-serializable format
        modifications = []
        for event in events:
            modifications.append({
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
                "user_id": event.user_id,
                "user_name": event.user_name,
                "description": event.description,
                "old_values": event.old_values,
                "new_values": event.new_values,
                "metadata": event.metadata
            })
        
        result = {
            "success": True,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "modifications_count": len(modifications),
            "modifications": modifications
        }
        
        logger.info(f"Retrieved {len(modifications)} modifications for {entity_type} {entity_id}")
        return json.dumps(result, indent=2)
        
    except AuditProviderError as e:
        logger.error(f"Audit provider error: {e}")
        return json.dumps({"error": f"Audit provider error: {e}"})
    except Exception as e:
        logger.error(f"Error retrieving modification history: {e}")
        return json.dumps({"error": f"Failed to retrieve modification history: {e}"})


async def detect_audit_exceptions(
    entity_type: str,
    criteria: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    severity_filter: Optional[str] = None,
    provider: Optional[str] = None
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
    if not audit_service:
        return json.dumps({"error": "Audit service not initialized"})
    
    try:
        # Parse criteria
        criteria_dict = {}
        if criteria:
            try:
                criteria_dict = json.loads(criteria)
            except json.JSONDecodeError:
                return json.dumps({"error": "Invalid criteria JSON format"})
        else:
            # Default criteria for basic exception detection
            criteria_dict = {"check_all": True}
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Detect exceptions
        exceptions = await audit_service.detect_exceptions(
            entity_type=entity_type,
            criteria=criteria_dict,
            start_date=start_dt,
            end_date=end_dt,
            provider_name=provider
        )
        
        # Filter by severity if specified
        if severity_filter:
            try:
                severity = ExceptionSeverity(severity_filter.lower())
                exceptions = [exc for exc in exceptions if exc.severity == severity]
            except ValueError:
                return json.dumps({"error": f"Invalid severity filter: {severity_filter}"})
        
        # Convert to JSON-serializable format
        exceptions_data = []
        for exception in exceptions:
            exceptions_data.append({
                "exception_id": exception.exception_id,
                "entity_id": exception.entity_id,
                "entity_type": exception.entity_type,
                "severity": exception.severity.value,
                "rule_name": exception.rule_name,
                "description": exception.description,
                "detected_at": exception.detected_at.isoformat(),
                "details": exception.details,
                "suggested_action": exception.suggested_action
            })
        
        # Group by severity for summary
        severity_counts = {}
        for exc in exceptions:
            severity_counts[exc.severity.value] = severity_counts.get(exc.severity.value, 0) + 1
        
        result = {
            "success": True,
            "entity_type": entity_type,
            "exceptions_count": len(exceptions),
            "severity_breakdown": severity_counts,
            "exceptions": exceptions_data
        }
        
        logger.info(f"Detected {len(exceptions)} audit exceptions for {entity_type}")
        return json.dumps(result, indent=2)
        
    except AuditProviderError as e:
        logger.error(f"Audit provider error: {e}")
        return json.dumps({"error": f"Audit provider error: {e}"})
    except Exception as e:
        logger.error(f"Error detecting exceptions: {e}")
        return json.dumps({"error": f"Failed to detect exceptions: {e}"})


async def generate_audit_report(
    entity_ids: str,
    entity_type: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_exceptions: bool = True,
    format_type: str = "json",
    provider: Optional[str] = None
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
    if not audit_service:
        return json.dumps({"error": "Audit service not initialized"})
    
    try:
        # Parse entity IDs
        entity_id_list = [entity_id.strip() for entity_id in entity_ids.split(',')]
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Generate report
        report = await audit_service.generate_audit_report(
            entity_ids=entity_id_list,
            entity_type=entity_type,
            start_date=start_dt,
            end_date=end_dt,
            include_exceptions=include_exceptions,
            format_type=format_type,
            provider_name=provider
        )
        
        # Convert to JSON-serializable format
        if format_type == "summary":
            # Return summary only
            result = {
                "success": True,
                "report_id": report.report_id,
                "title": report.title,
                "generated_at": report.generated_at.isoformat(),
                "date_range": {
                    "start": report.date_range["start"].isoformat(),
                    "end": report.date_range["end"].isoformat()
                },
                "entities_reviewed": report.entities_reviewed,
                "events_found": report.events_found,
                "exceptions_found": report.exceptions_found,
                "summary": report.summary,
                "metadata": report.metadata
            }
        else:
            # Return full report
            events_data = []
            for event in report.events:
                events_data.append({
                    "event_id": event.event_id,
                    "entity_id": event.entity_id,
                    "entity_type": event.entity_type,
                    "event_type": event.event_type.value,
                    "timestamp": event.timestamp.isoformat(),
                    "user_id": event.user_id,
                    "user_name": event.user_name,
                    "description": event.description,
                    "old_values": event.old_values,
                    "new_values": event.new_values,
                    "metadata": event.metadata
                })
            
            exceptions_data = []
            for exception in report.exceptions:
                exceptions_data.append({
                    "exception_id": exception.exception_id,
                    "entity_id": exception.entity_id,
                    "entity_type": exception.entity_type,
                    "severity": exception.severity.value,
                    "rule_name": exception.rule_name,
                    "description": exception.description,
                    "detected_at": exception.detected_at.isoformat(),
                    "details": exception.details,
                    "suggested_action": exception.suggested_action
                })
            
            result = {
                "success": True,
                "report_id": report.report_id,
                "title": report.title,
                "generated_at": report.generated_at.isoformat(),
                "date_range": {
                    "start": report.date_range["start"].isoformat(),
                    "end": report.date_range["end"].isoformat()
                },
                "entities_reviewed": report.entities_reviewed,
                "events_found": report.events_found,
                "exceptions_found": report.exceptions_found,
                "summary": report.summary,
                "events": events_data,
                "exceptions": exceptions_data,
                "metadata": report.metadata
            }
        
        logger.info(f"Generated audit report {report.report_id} for {len(entity_id_list)} {entity_type}(s)")
        return json.dumps(result, indent=2)
        
    except AuditProviderError as e:
        logger.error(f"Audit provider error: {e}")
        return json.dumps({"error": f"Audit provider error: {e}"})
    except Exception as e:
        logger.error(f"Error generating audit report: {e}")
        return json.dumps({"error": f"Failed to generate audit report: {e}"})


async def get_audit_providers() -> str:
    """
    Get information about available audit providers.
    
    Returns:
        JSON string containing provider information and capabilities
    """
    if not audit_service:
        return json.dumps({"error": "Audit service not initialized"})
    
    try:
        providers = audit_service.get_available_providers()
        
        providers_data = {}
        for name, metadata in providers.items():
            providers_data[name] = {
                "name": metadata.name,
                "version": metadata.version,
                "description": metadata.description,
                "capabilities": {
                    "supports_audit_trail": metadata.capabilities.supports_audit_trail,
                    "supports_modification_history": metadata.capabilities.supports_modification_history,
                    "supports_exception_detection": metadata.capabilities.supports_exception_detection,
                    "supports_user_tracking": metadata.capabilities.supports_user_tracking,
                    "supports_approval_workflow": metadata.capabilities.supports_approval_workflow,
                    "supports_real_time_events": metadata.capabilities.supports_real_time_events,
                    "max_history_days": metadata.capabilities.max_history_days,
                    "supported_entity_types": metadata.capabilities.supported_entity_types
                }
            }
        
        result = {
            "success": True,
            "providers_count": len(providers),
            "providers": providers_data
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting audit providers: {e}")
        return json.dumps({"error": f"Failed to get audit providers: {e}"})


async def audit_health_check(provider: Optional[str] = None) -> str:
    """
    Check health of audit providers.
    
    Args:
        provider: Specific provider to check (optional, checks all if not specified)
    
    Returns:
        JSON string containing health status
    """
    if not audit_service:
        return json.dumps({"error": "Audit service not initialized"})
    
    try:
        if provider:
            # Check specific provider
            provider_instance = audit_service.get_provider(provider)
            health_result = await provider_instance.health_check()
            result = {
                "success": True,
                "provider": provider,
                "health": health_result
            }
        else:
            # Check all providers
            health_results = await audit_service.health_check_all()
            result = {
                "success": True,
                "providers_checked": len(health_results),
                "health_results": health_results
            }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error checking audit health: {e}")
        return json.dumps({"error": f"Failed to check audit health: {e}"})