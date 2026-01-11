"""
Generic audit provider interface for multi-provider audit functionality.
Allows switching between different AP providers (Bill.com, QuickBooks, Xero, etc.)
without changing agent code.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum


class AuditEventType(Enum):
    """Standard audit event types across all providers."""
    CREATED = "created"
    MODIFIED = "modified"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CANCELLED = "cancelled"
    DELETED = "deleted"
    STATUS_CHANGED = "status_changed"


class ExceptionSeverity(Enum):
    """Severity levels for audit exceptions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Standard audit event structure."""
    event_id: str
    entity_id: str
    entity_type: str  # invoice, vendor, payment, etc.
    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str]
    user_name: Optional[str]
    description: str
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AuditException:
    """Standard audit exception structure."""
    exception_id: str
    entity_id: str
    entity_type: str
    severity: ExceptionSeverity
    rule_name: str
    description: str
    detected_at: datetime
    details: Dict[str, Any]
    suggested_action: Optional[str] = None


@dataclass
class AuditReport:
    """Standard audit report structure."""
    report_id: str
    title: str
    generated_at: datetime
    date_range: Dict[str, datetime]
    entities_reviewed: int
    events_found: int
    exceptions_found: int
    summary: str
    events: List[AuditEvent]
    exceptions: List[AuditException]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProviderCapabilities:
    """Describes what audit capabilities a provider supports."""
    supports_audit_trail: bool = True
    supports_modification_history: bool = True
    supports_exception_detection: bool = True
    supports_user_tracking: bool = True
    supports_approval_workflow: bool = False
    supports_real_time_events: bool = False
    max_history_days: Optional[int] = None
    supported_entity_types: List[str] = None


@dataclass
class ProviderMetadata:
    """Metadata about the audit provider."""
    name: str
    version: str
    description: str
    capabilities: ProviderCapabilities


class AuditProvider(ABC):
    """Abstract base class for audit providers."""
    
    @property
    @abstractmethod
    def metadata(self) -> ProviderMetadata:
        """Return provider metadata and capabilities."""
        pass
    
    @abstractmethod
    async def get_audit_trail(
        self,
        entity_id: str,
        entity_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        limit: Optional[int] = None
    ) -> List[AuditEvent]:
        """
        Retrieve audit trail for a specific entity.
        
        Args:
            entity_id: ID of the entity to audit
            entity_type: Type of entity (invoice, vendor, payment, etc.)
            start_date: Start of date range (optional)
            end_date: End of date range (optional)
            event_types: Filter by specific event types (optional)
            limit: Maximum number of events to return (optional)
            
        Returns:
            List of audit events
        """
        pass
    
    @abstractmethod
    async def get_modification_history(
        self,
        entity_id: str,
        entity_type: str,
        field_names: Optional[List[str]] = None
    ) -> List[AuditEvent]:
        """
        Get detailed modification history for an entity.
        
        Args:
            entity_id: ID of the entity
            entity_type: Type of entity
            field_names: Specific fields to track (optional)
            
        Returns:
            List of modification events with old/new values
        """
        pass
    
    @abstractmethod
    async def detect_exceptions(
        self,
        entity_type: str,
        criteria: Dict[str, Any],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditException]:
        """
        Detect audit exceptions based on criteria.
        
        Args:
            entity_type: Type of entities to check
            criteria: Exception detection criteria
            start_date: Start of date range (optional)
            end_date: End of date range (optional)
            
        Returns:
            List of detected exceptions
        """
        pass
    
    @abstractmethod
    async def generate_audit_report(
        self,
        entity_ids: List[str],
        entity_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_exceptions: bool = True,
        format_type: str = "json"
    ) -> AuditReport:
        """
        Generate comprehensive audit report.
        
        Args:
            entity_ids: List of entity IDs to include
            entity_type: Type of entities
            start_date: Start of date range (optional)
            end_date: End of date range (optional)
            include_exceptions: Whether to include exception detection
            format_type: Output format (json, csv, pdf)
            
        Returns:
            Formatted audit report
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check provider health and connectivity.
        
        Returns:
            Health status information
        """
        pass