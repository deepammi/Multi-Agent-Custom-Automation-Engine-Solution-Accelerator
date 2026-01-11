"""
Bill.com audit adapter implementing the generic audit provider interface.
Maps Bill.com specific audit data to standardized audit models.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid

from interfaces.audit_provider import (
    AuditProvider, AuditEvent, AuditException, AuditReport,
    AuditEventType, ExceptionSeverity, ProviderMetadata, ProviderCapabilities
)
from services.bill_com_service import BillComAPIService

logger = logging.getLogger(__name__)


class BillComAuditAdapter(AuditProvider):
    """Bill.com implementation of the audit provider interface."""
    
    def __init__(self, bill_com_service: BillComAPIService):
        self.service = bill_com_service
        self._metadata = ProviderMetadata(
            name="Bill.com",
            version="1.0.0",
            description="Bill.com audit trail and compliance monitoring",
            capabilities=ProviderCapabilities(
                supports_audit_trail=True,
                supports_modification_history=True,
                supports_exception_detection=True,
                supports_user_tracking=True,
                supports_approval_workflow=True,
                supports_real_time_events=False,
                max_history_days=365,
                supported_entity_types=["invoice", "vendor", "payment", "bill"]
            )
        )
    
    @property
    def metadata(self) -> ProviderMetadata:
        """Return Bill.com provider metadata."""
        return self._metadata
    
    async def get_audit_trail(
        self,
        entity_id: str,
        entity_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        limit: Optional[int] = None
    ) -> List[AuditEvent]:
        """Retrieve audit trail from Bill.com."""
        try:
            # Map entity types to Bill.com object types
            billcom_object_type = self._map_entity_type(entity_type)
            
            # Get audit data from Bill.com
            audit_data = await self._get_billcom_audit_data(
                entity_id, billcom_object_type, start_date, end_date
            )
            
            # Convert to standard audit events
            events = []
            for item in audit_data:
                event = self._convert_to_audit_event(item, entity_id, entity_type)
                if event and (not event_types or event.event_type in event_types):
                    events.append(event)
            
            # Apply limit if specified
            if limit:
                events = events[:limit]
            
            logger.info(f"Retrieved {len(events)} audit events for {entity_type} {entity_id}")
            return events
            
        except Exception as e:
            logger.error(f"Error retrieving audit trail: {e}")
            raise
    
    async def get_modification_history(
        self,
        entity_id: str,
        entity_type: str,
        field_names: Optional[List[str]] = None
    ) -> List[AuditEvent]:
        """Get detailed modification history from Bill.com."""
        try:
            # Get full audit trail
            events = await self.get_audit_trail(entity_id, entity_type)
            
            # Filter for modification events only
            modification_events = [
                event for event in events 
                if event.event_type == AuditEventType.MODIFIED and event.old_values
            ]
            
            # Filter by field names if specified
            if field_names:
                filtered_events = []
                for event in modification_events:
                    if event.old_values and any(field in event.old_values for field in field_names):
                        filtered_events.append(event)
                modification_events = filtered_events
            
            logger.info(f"Retrieved {len(modification_events)} modification events for {entity_type} {entity_id}")
            return modification_events
            
        except Exception as e:
            logger.error(f"Error retrieving modification history: {e}")
            raise
    
    async def detect_exceptions(
        self,
        entity_type: str,
        criteria: Dict[str, Any],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditException]:
        """Detect audit exceptions using Bill.com data."""
        try:
            exceptions = []
            
            # Get entities to check based on criteria
            entities = await self._get_entities_for_exception_check(
                entity_type, criteria, start_date, end_date
            )
            
            for entity in entities:
                entity_exceptions = await self._check_entity_exceptions(entity, criteria)
                exceptions.extend(entity_exceptions)
            
            logger.info(f"Detected {len(exceptions)} audit exceptions for {entity_type}")
            return exceptions
            
        except Exception as e:
            logger.error(f"Error detecting exceptions: {e}")
            raise
    
    async def generate_audit_report(
        self,
        entity_ids: List[str],
        entity_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_exceptions: bool = True,
        format_type: str = "json"
    ) -> AuditReport:
        """Generate comprehensive audit report."""
        try:
            report_id = str(uuid.uuid4())
            generated_at = datetime.utcnow()
            
            # Collect all audit events
            all_events = []
            for entity_id in entity_ids:
                events = await self.get_audit_trail(entity_id, entity_type, start_date, end_date)
                all_events.extend(events)
            
            # Detect exceptions if requested
            exceptions = []
            if include_exceptions:
                exception_criteria = {"check_all": True}  # Basic criteria
                exceptions = await self.detect_exceptions(entity_type, exception_criteria, start_date, end_date)
                # Filter exceptions to only those for our entities
                exceptions = [exc for exc in exceptions if exc.entity_id in entity_ids]
            
            # Generate summary
            summary = self._generate_report_summary(all_events, exceptions, entity_type)
            
            report = AuditReport(
                report_id=report_id,
                title=f"Audit Report - {entity_type.title()}s",
                generated_at=generated_at,
                date_range={
                    "start": start_date or (generated_at - timedelta(days=30)),
                    "end": end_date or generated_at
                },
                entities_reviewed=len(entity_ids),
                events_found=len(all_events),
                exceptions_found=len(exceptions),
                summary=summary,
                events=all_events,
                exceptions=exceptions,
                metadata={
                    "provider": "Bill.com",
                    "format": format_type,
                    "entity_type": entity_type
                }
            )
            
            logger.info(f"Generated audit report {report_id} with {len(all_events)} events and {len(exceptions)} exceptions")
            return report
            
        except Exception as e:
            logger.error(f"Error generating audit report: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Bill.com service health."""
        try:
            # Test basic connectivity
            await self.service.ensure_authenticated()
            
            return {
                "status": "healthy",
                "provider": "Bill.com",
                "authenticated": True,
                "timestamp": datetime.utcnow().isoformat(),
                "capabilities": self.metadata.capabilities.__dict__
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "provider": "Bill.com",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Private helper methods
    
    def _map_entity_type(self, entity_type: str) -> str:
        """Map generic entity type to Bill.com object type."""
        mapping = {
            "invoice": "Bill",
            "vendor": "Vendor", 
            "payment": "VendorPayment",
            "bill": "Bill"
        }
        return mapping.get(entity_type.lower(), entity_type)
    
    async def _get_billcom_audit_data(
        self,
        entity_id: str,
        object_type: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Get audit data from Bill.com API."""
        # This would call Bill.com's audit/history endpoints
        # For now, we'll simulate with invoice data and derive audit events
        
        try:
            if object_type == "Bill":
                # Get invoice details which may include some audit info
                invoice_data = await self.service.get_invoice_by_id(entity_id)
                
                # Simulate audit events from invoice data
                audit_events = []
                
                # Creation event
                if invoice_data.get("createdTime"):
                    audit_events.append({
                        "eventType": "Created",
                        "timestamp": invoice_data["createdTime"],
                        "userId": invoice_data.get("createdBy"),
                        "description": f"Invoice {entity_id} created",
                        "objectId": entity_id
                    })
                
                # Status changes (if we have status history)
                if invoice_data.get("approvalStatus"):
                    audit_events.append({
                        "eventType": "StatusChanged",
                        "timestamp": invoice_data.get("updatedTime", invoice_data.get("createdTime")),
                        "userId": invoice_data.get("updatedBy"),
                        "description": f"Invoice status changed to {invoice_data['approvalStatus']}",
                        "objectId": entity_id,
                        "newValue": invoice_data["approvalStatus"]
                    })
                
                return audit_events
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting Bill.com audit data: {e}")
            return []
    
    def _convert_to_audit_event(
        self,
        billcom_event: Dict[str, Any],
        entity_id: str,
        entity_type: str
    ) -> Optional[AuditEvent]:
        """Convert Bill.com audit data to standard audit event."""
        try:
            # Map Bill.com event types to standard types
            event_type_mapping = {
                "Created": AuditEventType.CREATED,
                "Modified": AuditEventType.MODIFIED,
                "Approved": AuditEventType.APPROVED,
                "Rejected": AuditEventType.REJECTED,
                "Paid": AuditEventType.PAID,
                "StatusChanged": AuditEventType.STATUS_CHANGED,
                "Deleted": AuditEventType.DELETED
            }
            
            billcom_type = billcom_event.get("eventType", "Modified")
            event_type = event_type_mapping.get(billcom_type, AuditEventType.MODIFIED)
            
            # Parse timestamp
            timestamp_str = billcom_event.get("timestamp")
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.utcnow()
            
            return AuditEvent(
                event_id=str(uuid.uuid4()),
                entity_id=entity_id,
                entity_type=entity_type,
                event_type=event_type,
                timestamp=timestamp,
                user_id=billcom_event.get("userId"),
                user_name=billcom_event.get("userName"),
                description=billcom_event.get("description", f"{event_type.value} event"),
                old_values=billcom_event.get("oldValue"),
                new_values=billcom_event.get("newValue"),
                metadata={
                    "provider": "Bill.com",
                    "original_event": billcom_event
                }
            )
            
        except Exception as e:
            logger.error(f"Error converting audit event: {e}")
            return None
    
    async def _get_entities_for_exception_check(
        self,
        entity_type: str,
        criteria: Dict[str, Any],
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Get entities to check for exceptions."""
        try:
            if entity_type == "invoice":
                # Get bills in date range (Bill.com API uses "bills" not "invoices")
                invoices = await self.service.get_bills(
                    start_date=start_date,
                    end_date=end_date,
                    limit=100  # Reasonable limit for exception checking
                )
                return invoices
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting entities for exception check: {e}")
            return []
    
    async def _check_entity_exceptions(
        self,
        entity: Dict[str, Any],
        criteria: Dict[str, Any]
    ) -> List[AuditException]:
        """Check a single entity for audit exceptions."""
        exceptions = []
        
        try:
            entity_id = entity.get("id", "unknown")
            
            # Check for missing approval
            if not entity.get("approvalStatus") or entity.get("approvalStatus") == "Unassigned":
                exceptions.append(AuditException(
                    exception_id=str(uuid.uuid4()),
                    entity_id=entity_id,
                    entity_type="invoice",
                    severity=ExceptionSeverity.MEDIUM,
                    rule_name="Missing Approval",
                    description="Invoice lacks proper approval status",
                    detected_at=datetime.utcnow(),
                    details={
                        "current_status": entity.get("approvalStatus"),
                        "amount": entity.get("amount")
                    },
                    suggested_action="Review and assign appropriate approval status"
                ))
            
            # Check for unusual amounts (example rule)
            amount = float(entity.get("amount", 0))
            if amount > 10000:  # Configurable threshold
                exceptions.append(AuditException(
                    exception_id=str(uuid.uuid4()),
                    entity_id=entity_id,
                    entity_type="invoice",
                    severity=ExceptionSeverity.HIGH,
                    rule_name="High Value Transaction",
                    description=f"Invoice amount ${amount:,.2f} exceeds threshold",
                    detected_at=datetime.utcnow(),
                    details={
                        "amount": amount,
                        "threshold": 10000,
                        "vendor": entity.get("vendorName")
                    },
                    suggested_action="Verify authorization for high-value transaction"
                ))
            
            # Check for old unpaid invoices
            due_date_str = entity.get("dueDate")
            if due_date_str and entity.get("paymentStatus") != "Paid":
                try:
                    due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                    days_overdue = (datetime.utcnow() - due_date).days
                    
                    if days_overdue > 30:
                        exceptions.append(AuditException(
                            exception_id=str(uuid.uuid4()),
                            entity_id=entity_id,
                            entity_type="invoice",
                            severity=ExceptionSeverity.MEDIUM,
                            rule_name="Overdue Payment",
                            description=f"Invoice overdue by {days_overdue} days",
                            detected_at=datetime.utcnow(),
                            details={
                                "due_date": due_date_str,
                                "days_overdue": days_overdue,
                                "amount": amount
                            },
                            suggested_action="Follow up on overdue payment"
                        ))
                except ValueError:
                    pass  # Skip if date parsing fails
            
        except Exception as e:
            logger.error(f"Error checking entity exceptions: {e}")
        
        return exceptions
    
    def _generate_report_summary(
        self,
        events: List[AuditEvent],
        exceptions: List[AuditException],
        entity_type: str
    ) -> str:
        """Generate a summary for the audit report."""
        event_counts = {}
        for event in events:
            event_counts[event.event_type.value] = event_counts.get(event.event_type.value, 0) + 1
        
        exception_counts = {}
        for exception in exceptions:
            exception_counts[exception.severity.value] = exception_counts.get(exception.severity.value, 0) + 1
        
        summary_parts = [
            f"Audit report for {len(set(e.entity_id for e in events))} {entity_type}(s)",
            f"Total events: {len(events)}",
            f"Event breakdown: {', '.join(f'{k}: {v}' for k, v in event_counts.items())}",
            f"Total exceptions: {len(exceptions)}"
        ]
        
        if exception_counts:
            summary_parts.append(f"Exception severity: {', '.join(f'{k}: {v}' for k, v in exception_counts.items())}")
        
        return ". ".join(summary_parts) + "."