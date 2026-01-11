"""
Message Persistence Service for direct database message saving.

This service provides direct database persistence for agent messages,
ensuring messages are saved regardless of WebSocket connection status.
"""
import logging
import re
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from app.db.mongodb import MongoDB
from app.db.repositories import MessageRepository
from app.models.message import AgentMessage

logger = logging.getLogger(__name__)


class MessageValidationError(Exception):
    """Exception raised when message validation fails."""
    pass


class MessageFormat(Enum):
    """Supported message formats for consistency validation."""
    AGENT_RESPONSE = "agent_response"
    SYSTEM_MESSAGE = "system_message"
    ERROR_MESSAGE = "error_message"
    STREAMING_CHUNK = "streaming_chunk"
    FINAL_RESULT = "final_result"


@dataclass
class ValidationResult:
    """Result of message validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    normalized_message: Optional[AgentMessage] = None


class MessageFormatValidator:
    """
    Validator for ensuring consistent message structure across persistence methods.
    """
    
    # Required fields for different message types
    REQUIRED_FIELDS = {
        MessageFormat.AGENT_RESPONSE: {"plan_id", "agent_name", "content", "agent_type"},
        MessageFormat.SYSTEM_MESSAGE: {"plan_id", "agent_name", "content"},
        MessageFormat.ERROR_MESSAGE: {"plan_id", "agent_name", "content"},
        MessageFormat.STREAMING_CHUNK: {"plan_id", "agent_name", "content"},
        MessageFormat.FINAL_RESULT: {"plan_id", "agent_name", "content", "agent_type"}
    }
    
    # Valid agent types
    VALID_AGENT_TYPES = {
        "agent", "system", "error", "planner", "email", "invoice", 
        "closing", "audit", "contract", "procurement", "supervisor", "test"
    }
    
    # Content validation patterns
    CONTENT_PATTERNS = {
        "min_length": 1,
        "max_length": 50000,
        "forbidden_patterns": [
            r"<script[^>]*>.*?</script>",  # No script tags
            r"javascript:",  # No javascript URLs
            r"data:text/html",  # No HTML data URLs
        ]
    }
    
    def __init__(self):
        """Initialize the validator."""
        self.validation_stats = {
            "total_validated": 0,
            "validation_errors": 0,
            "validation_warnings": 0,
            "format_corrections": 0
        }
    
    def validate_message(
        self,
        message: AgentMessage,
        expected_format: Optional[MessageFormat] = None,
        strict_mode: bool = False
    ) -> ValidationResult:
        """
        Validate message format and consistency.
        
        Args:
            message: AgentMessage to validate
            expected_format: Expected message format (optional)
            strict_mode: Whether to apply strict validation rules
            
        Returns:
            ValidationResult with validation details
        """
        errors = []
        warnings = []
        
        try:
            self.validation_stats["total_validated"] += 1
            
            # Basic field validation
            field_errors = self._validate_required_fields(message, expected_format)
            errors.extend(field_errors)
            
            # Content validation
            content_errors, content_warnings = self._validate_content(message.content, strict_mode)
            errors.extend(content_errors)
            warnings.extend(content_warnings)
            
            # Agent type validation
            agent_type_errors = self._validate_agent_type(message.agent_type)
            errors.extend(agent_type_errors)
            
            # Plan ID format validation
            plan_id_errors = self._validate_plan_id(message.plan_id)
            errors.extend(plan_id_errors)
            
            # Agent name validation
            agent_name_errors = self._validate_agent_name(message.agent_name)
            errors.extend(agent_name_errors)
            
            # Timestamp validation
            timestamp_errors = self._validate_timestamp(message.timestamp)
            errors.extend(timestamp_errors)
            
            # Metadata validation
            metadata_warnings = self._validate_metadata(message.metadata)
            warnings.extend(metadata_warnings)
            
            # Create normalized message if validation passes
            normalized_message = None
            if not errors:
                normalized_message = self._normalize_message(message)
                if normalized_message != message:
                    self.validation_stats["format_corrections"] += 1
            
            # Update stats
            if errors:
                self.validation_stats["validation_errors"] += 1
            if warnings:
                self.validation_stats["validation_warnings"] += 1
            
            is_valid = len(errors) == 0
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                normalized_message=normalized_message
            )
            
        except Exception as e:
            logger.error(f"❌ Message validation failed with exception: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation exception: {str(e)}"],
                warnings=[]
            )
    
    def _validate_required_fields(
        self,
        message: AgentMessage,
        expected_format: Optional[MessageFormat]
    ) -> List[str]:
        """Validate required fields based on message format."""
        errors = []
        
        # Get required fields for format
        if expected_format and expected_format in self.REQUIRED_FIELDS:
            required_fields = self.REQUIRED_FIELDS[expected_format]
        else:
            # Default required fields
            required_fields = {"plan_id", "agent_name", "content"}
        
        # Check each required field
        for field in required_fields:
            value = getattr(message, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                errors.append(f"Required field '{field}' is missing or empty")
        
        return errors
    
    def _validate_content(self, content: str, strict_mode: bool) -> tuple[List[str], List[str]]:
        """Validate message content."""
        errors = []
        warnings = []
        
        if not content:
            errors.append("Content cannot be empty")
            return errors, warnings
        
        # Length validation
        if len(content) < self.CONTENT_PATTERNS["min_length"]:
            errors.append(f"Content too short (minimum {self.CONTENT_PATTERNS['min_length']} characters)")
        
        if len(content) > self.CONTENT_PATTERNS["max_length"]:
            if strict_mode:
                errors.append(f"Content too long (maximum {self.CONTENT_PATTERNS['max_length']} characters)")
            else:
                warnings.append(f"Content is very long ({len(content)} characters)")
        
        # Security validation - check for forbidden patterns
        for pattern in self.CONTENT_PATTERNS["forbidden_patterns"]:
            if re.search(pattern, content, re.IGNORECASE):
                errors.append(f"Content contains forbidden pattern: {pattern}")
        
        # Content quality checks
        if strict_mode:
            # Check for reasonable content structure
            if len(content.strip()) < 10:
                warnings.append("Content appears to be very short for an agent message")
            
            # Check for excessive whitespace
            if len(content) - len(content.strip()) > len(content) * 0.3:
                warnings.append("Content contains excessive whitespace")
        
        return errors, warnings
    
    def _validate_agent_type(self, agent_type: str) -> List[str]:
        """Validate agent type."""
        errors = []
        
        if not agent_type:
            errors.append("Agent type cannot be empty")
            return errors
        
        if agent_type.lower() not in self.VALID_AGENT_TYPES:
            errors.append(f"Invalid agent type '{agent_type}'. Valid types: {', '.join(self.VALID_AGENT_TYPES)}")
        
        return errors
    
    def _validate_plan_id(self, plan_id: str) -> List[str]:
        """Validate plan ID format."""
        errors = []
        
        if not plan_id:
            errors.append("Plan ID cannot be empty")
            return errors
        
        # Check format (should be UUID-like or reasonable identifier)
        if len(plan_id) < 8:
            errors.append("Plan ID appears to be too short")
        
        if len(plan_id) > 100:
            errors.append("Plan ID is too long")
        
        # Check for valid characters (alphanumeric, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9_-]+$', plan_id):
            errors.append("Plan ID contains invalid characters (only alphanumeric, hyphens, and underscores allowed)")
        
        return errors
    
    def _validate_agent_name(self, agent_name: str) -> List[str]:
        """Validate agent name."""
        errors = []
        
        if not agent_name:
            errors.append("Agent name cannot be empty")
            return errors
        
        if len(agent_name) > 100:
            errors.append("Agent name is too long")
        
        # Check for reasonable agent name format
        if not re.match(r'^[a-zA-Z0-9_\s-]+$', agent_name):
            errors.append("Agent name contains invalid characters")
        
        return errors
    
    def _validate_timestamp(self, timestamp: datetime) -> List[str]:
        """Validate timestamp."""
        errors = []
        
        if not timestamp:
            errors.append("Timestamp cannot be empty")
            return errors
        
        # Check if timestamp is reasonable (not too far in past or future)
        now = datetime.utcnow()
        if timestamp > now + timedelta(minutes=5):
            errors.append("Timestamp is too far in the future")
        
        if timestamp < now - timedelta(days=30):
            errors.append("Timestamp is too far in the past")
        
        return errors
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """Validate metadata structure."""
        warnings = []
        
        if not isinstance(metadata, dict):
            warnings.append("Metadata should be a dictionary")
            return warnings
        
        # Check metadata size
        try:
            import json
            metadata_size = len(json.dumps(metadata))
            if metadata_size > 10000:  # 10KB limit
                warnings.append(f"Metadata is very large ({metadata_size} bytes)")
        except Exception:
            warnings.append("Metadata contains non-serializable data")
        
        # Check for sensitive data patterns
        sensitive_keys = {"password", "token", "secret", "key", "credential"}
        for key in metadata.keys():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                warnings.append(f"Metadata may contain sensitive data in key: {key}")
        
        return warnings
    
    def _normalize_message(self, message: AgentMessage) -> AgentMessage:
        """Normalize message format for consistency."""
        # Create a copy with normalized values
        normalized = AgentMessage(
            plan_id=message.plan_id.strip(),
            agent_name=message.agent_name.strip(),
            agent_type=message.agent_type.lower().strip(),
            content=message.content.strip(),
            timestamp=message.timestamp,
            metadata=message.metadata or {}
        )
        
        # Ensure timestamp is UTC
        if normalized.timestamp.tzinfo is not None:
            normalized.timestamp = normalized.timestamp.replace(tzinfo=None)
        
        return normalized
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        return {
            **self.validation_stats,
            "error_rate": (
                self.validation_stats["validation_errors"] / 
                max(self.validation_stats["total_validated"], 1) * 100
            ),
            "warning_rate": (
                self.validation_stats["validation_warnings"] / 
                max(self.validation_stats["total_validated"], 1) * 100
            )
        }
    
    def reset_stats(self) -> None:
        """Reset validation statistics."""
        self.validation_stats = {
            "total_validated": 0,
            "validation_errors": 0,
            "validation_warnings": 0,
            "format_corrections": 0
        }


class MessagePersistenceService:
    """
    Service for persisting agent messages directly to database.
    
    This service ensures that agent messages are saved to the database
    during execution, regardless of WebSocket connection status.
    Includes comprehensive message format validation and consistency checks.
    """
    
    def __init__(self, strict_validation: bool = False):
        """
        Initialize the message persistence service.
        
        Args:
            strict_validation: Whether to apply strict validation rules
        """
        self._ensure_database_connection()
        self.validator = MessageFormatValidator()
        self.strict_validation = strict_validation
        self.persistence_stats = {
            "messages_saved": 0,
            "messages_failed": 0,
            "validation_failures": 0,
            "format_corrections": 0
        }
    
    def _ensure_database_connection(self) -> None:
        """Ensure database connection is available and indexes are initialized."""
        try:
            db = MongoDB.get_database()
            if db is None:
                raise RuntimeError("Database connection not available")
            
            # Initialize indexes for optimal chronological ordering
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're in an async context, schedule the index initialization
                    asyncio.create_task(MongoDB.initialize_indexes())
                else:
                    # If not in async context, run it synchronously
                    loop.run_until_complete(MongoDB.initialize_indexes())
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize database indexes: {e}")
                # Continue without indexes - they're not critical for basic functionality
                
        except Exception as e:
            logger.error(f"❌ Database connection check failed: {e}")
            raise
    
    async def save_agent_message(
        self,
        plan_id: str,
        agent_name: str,
        content: str,
        agent_type: str = "agent",
        metadata: Optional[Dict[str, Any]] = None,
        expected_format: Optional[MessageFormat] = None,
        skip_validation: bool = False
    ) -> bool:
        """
        Save a single agent message to database with validation.
        
        Args:
            plan_id: Plan identifier
            agent_name: Name of the agent generating the message
            content: Message content
            agent_type: Type of agent (default: "agent")
            metadata: Optional metadata dictionary
            expected_format: Expected message format for validation
            skip_validation: Whether to skip validation (not recommended)
            
        Returns:
            True if message was saved successfully, False otherwise
        """
        try:
            # Basic parameter validation
            if not plan_id or not plan_id.strip():
                logger.error("❌ Cannot save message: plan_id is required")
                self.persistence_stats["messages_failed"] += 1
                return False
            
            if not agent_name or not agent_name.strip():
                logger.error("❌ Cannot save message: agent_name is required")
                self.persistence_stats["messages_failed"] += 1
                return False
            
            if not content or not content.strip():
                logger.debug("⚠️ Skipping empty message content")
                return False
            
            # Create message object
            message = AgentMessage(
                plan_id=plan_id.strip(),
                agent_name=agent_name.strip(),
                agent_type=agent_type.strip(),
                content=content.strip(),
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            # Validate message format unless skipped
            if not skip_validation:
                validation_result = self.validator.validate_message(
                    message, 
                    expected_format, 
                    self.strict_validation
                )
                
                if not validation_result.is_valid:
                    logger.error(f"❌ Message validation failed: {', '.join(validation_result.errors)}")
                    self.persistence_stats["validation_failures"] += 1
                    self.persistence_stats["messages_failed"] += 1
                    return False
                
                # Log warnings if any
                if validation_result.warnings:
                    logger.warning(f"⚠️ Message validation warnings: {', '.join(validation_result.warnings)}")
                
                # Use normalized message if available
                if validation_result.normalized_message:
                    message = validation_result.normalized_message
                    self.persistence_stats["format_corrections"] += 1
            
            # Save to database using repository
            message_id = await MessageRepository.create(message)
            
            self.persistence_stats["messages_saved"] += 1
            logger.debug(f"💾 Saved message to database: {agent_name} -> {plan_id} ({len(content)} chars)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save agent message: {e}")
            self.persistence_stats["messages_failed"] += 1
            return False
    
    async def save_messages_batch(
        self,
        messages: List[AgentMessage],
        validate_consistency: bool = True
    ) -> List[bool]:
        """
        Save multiple messages in batch with consistency validation.
        
        Args:
            messages: List of AgentMessage objects to save
            validate_consistency: Whether to validate consistency across messages
            
        Returns:
            List of boolean results indicating success/failure for each message
        """
        if not messages:
            return []
        
        results = []
        
        try:
            # Validate consistency across messages if requested
            if validate_consistency:
                consistency_errors = self._validate_message_consistency(messages)
                if consistency_errors:
                    logger.warning(f"⚠️ Message batch consistency issues: {', '.join(consistency_errors)}")
            
            # Process each message individually to ensure partial success
            for i, message in enumerate(messages):
                try:
                    # Validate message
                    validation_result = self.validator.validate_message(
                        message, 
                        strict_mode=self.strict_validation
                    )
                    
                    if not validation_result.is_valid:
                        logger.error(f"❌ Message {i} validation failed: {', '.join(validation_result.errors)}")
                        self.persistence_stats["validation_failures"] += 1
                        results.append(False)
                        continue
                    
                    # Use normalized message if available
                    save_message = validation_result.normalized_message or message
                    
                    # Save message
                    await MessageRepository.create(save_message)
                    results.append(True)
                    self.persistence_stats["messages_saved"] += 1
                    
                    if validation_result.normalized_message:
                        self.persistence_stats["format_corrections"] += 1
                    
                except Exception as e:
                    logger.error(f"❌ Failed to save message {i} in batch: {e}")
                    self.persistence_stats["messages_failed"] += 1
                    results.append(False)
            
            success_count = sum(results)
            logger.info(f"💾 Batch save completed: {success_count}/{len(messages)} messages saved")
            
        except Exception as e:
            logger.error(f"❌ Batch save failed: {e}")
            results = [False] * len(messages)
            self.persistence_stats["messages_failed"] += len(messages)
        
        return results
    
    def _validate_message_consistency(self, messages: List[AgentMessage]) -> List[str]:
        """
        Validate consistency across multiple messages.
        
        Args:
            messages: List of messages to validate
            
        Returns:
            List of consistency error messages
        """
        errors = []
        
        if not messages:
            return errors
        
        # Check plan_id consistency
        plan_ids = {msg.plan_id for msg in messages}
        if len(plan_ids) > 1:
            errors.append(f"Multiple plan IDs in batch: {', '.join(plan_ids)}")
        
        # Check timestamp ordering
        timestamps = [msg.timestamp for msg in messages if msg.timestamp]
        if len(timestamps) > 1:
            sorted_timestamps = sorted(timestamps)
            if timestamps != sorted_timestamps:
                errors.append("Messages are not in chronological order")
        
        # Check for duplicate content
        content_hashes = {}
        for i, msg in enumerate(messages):
            content_hash = hash(msg.content)
            if content_hash in content_hashes:
                errors.append(f"Duplicate content detected between messages {content_hashes[content_hash]} and {i}")
            else:
                content_hashes[content_hash] = i
        
        # Check agent name consistency patterns
        agent_names = [msg.agent_name for msg in messages]
        if len(set(agent_names)) == 1 and len(messages) > 10:
            errors.append("All messages from same agent - possible streaming issue")
        
        return errors
    
    async def get_messages_for_plan(
        self,
        plan_id: str,
        limit: Optional[int] = None
    ) -> List[AgentMessage]:
        """
        Retrieve all messages for a specific plan.
        
        Args:
            plan_id: Plan identifier
            limit: Optional limit on number of messages to return
            
        Returns:
            List of AgentMessage objects, ordered by timestamp
        """
        try:
            if not plan_id or not plan_id.strip():
                logger.error("❌ Cannot retrieve messages: plan_id is required")
                return []
            
            # Get messages from repository
            messages = await MessageRepository.get_by_plan_id(plan_id.strip())
            
            # Apply limit if specified
            if limit and limit > 0:
                messages = messages[-limit:]  # Get most recent messages
            
            logger.debug(f"📖 Retrieved {len(messages)} messages for plan {plan_id}")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve messages for plan {plan_id}: {e}")
            return []
    
    async def save_streaming_message(
        self,
        plan_id: str,
        agent_name: str,
        content_chunks: List[str],
        agent_type: str = "agent",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save a complete streaming message by combining content chunks.
        
        Args:
            plan_id: Plan identifier
            agent_name: Name of the agent
            content_chunks: List of content chunks to combine
            agent_type: Type of agent
            metadata: Optional metadata
            
        Returns:
            True if message was saved successfully, False otherwise
        """
        try:
            if not content_chunks:
                logger.debug("⚠️ No content chunks to save")
                return False
            
            # Combine all chunks into complete content
            complete_content = "".join(content_chunks)
            
            # Save as single message with streaming format validation
            return await self.save_agent_message(
                plan_id=plan_id,
                agent_name=agent_name,
                content=complete_content,
                agent_type=agent_type,
                metadata=metadata,
                expected_format=MessageFormat.FINAL_RESULT
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to save streaming message: {e}")
            return False
    
    async def save_system_message(
        self,
        plan_id: str,
        message: str,
        message_type: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save a system message.
        
        Args:
            plan_id: Plan identifier
            message: System message content
            message_type: Type of system message
            metadata: Optional metadata
            
        Returns:
            True if message was saved successfully, False otherwise
        """
        return await self.save_agent_message(
            plan_id=plan_id,
            agent_name="System",
            content=message,
            agent_type=message_type,
            metadata=metadata,
            expected_format=MessageFormat.SYSTEM_MESSAGE
        )
    
    async def save_error_message(
        self,
        plan_id: str,
        error_message: str,
        agent_name: Optional[str] = None,
        error_type: str = "error",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save an error message.
        
        Args:
            plan_id: Plan identifier
            error_message: Error message content
            agent_name: Optional agent name that caused the error
            error_type: Type of error
            metadata: Optional metadata including error details
            
        Returns:
            True if message was saved successfully, False otherwise
        """
        agent = agent_name or "System"
        error_metadata = metadata or {}
        error_metadata.update({
            "error_type": error_type,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return await self.save_agent_message(
            plan_id=plan_id,
            agent_name=agent,
            content=f"Error: {error_message}",
            agent_type="error",
            metadata=error_metadata,
            expected_format=MessageFormat.ERROR_MESSAGE
        )
    
    async def validate_message_format_consistency(
        self,
        plan_id: str,
        websocket_messages: List[Dict[str, Any]],
        database_messages: List[AgentMessage]
    ) -> Dict[str, Any]:
        """
        Validate format consistency between WebSocket and database messages.
        
        Args:
            plan_id: Plan identifier
            websocket_messages: Messages from WebSocket history
            database_messages: Messages from database
            
        Returns:
            Dictionary with consistency validation results
        """
        try:
            consistency_report = {
                "plan_id": plan_id,
                "websocket_count": len(websocket_messages),
                "database_count": len(database_messages),
                "format_mismatches": [],
                "content_mismatches": [],
                "timestamp_issues": [],
                "missing_in_database": [],
                "missing_in_websocket": [],
                "overall_consistent": True
            }
            
            # Create lookup maps
            ws_by_content = {self._normalize_content(msg.get("data", {}).get("content", "")): msg 
                           for msg in websocket_messages if msg.get("data", {}).get("content")}
            db_by_content = {self._normalize_content(msg.content): msg for msg in database_messages}
            
            # Check for messages in WebSocket but not in database
            for content, ws_msg in ws_by_content.items():
                if content not in db_by_content:
                    consistency_report["missing_in_database"].append({
                        "content_preview": content[:100],
                        "agent": ws_msg.get("data", {}).get("agent_name", "unknown"),
                        "timestamp": ws_msg.get("timestamp")
                    })
                    consistency_report["overall_consistent"] = False
            
            # Check for messages in database but not in WebSocket
            for content, db_msg in db_by_content.items():
                if content not in ws_by_content:
                    consistency_report["missing_in_websocket"].append({
                        "content_preview": content[:100],
                        "agent": db_msg.agent_name,
                        "timestamp": db_msg.timestamp.isoformat()
                    })
            
            # Check format consistency for matching messages
            for content in set(ws_by_content.keys()) & set(db_by_content.keys()):
                ws_msg = ws_by_content[content]
                db_msg = db_by_content[content]
                
                # Compare agent names
                ws_agent = ws_msg.get("data", {}).get("agent_name", "")
                if ws_agent != db_msg.agent_name:
                    consistency_report["format_mismatches"].append({
                        "issue": "agent_name_mismatch",
                        "websocket_agent": ws_agent,
                        "database_agent": db_msg.agent_name,
                        "content_preview": content[:50]
                    })
                    consistency_report["overall_consistent"] = False
                
                # Compare timestamps (allow some tolerance)
                ws_timestamp_str = ws_msg.get("timestamp", "")
                if ws_timestamp_str:
                    try:
                        ws_timestamp = datetime.fromisoformat(ws_timestamp_str.replace('Z', '+00:00'))
                        time_diff = abs((ws_timestamp.replace(tzinfo=None) - db_msg.timestamp).total_seconds())
                        if time_diff > 60:  # More than 1 minute difference
                            consistency_report["timestamp_issues"].append({
                                "websocket_timestamp": ws_timestamp_str,
                                "database_timestamp": db_msg.timestamp.isoformat(),
                                "difference_seconds": time_diff,
                                "content_preview": content[:50]
                            })
                    except Exception as e:
                        logger.debug(f"Timestamp parsing error: {e}")
            
            logger.info(f"📊 Message consistency check for plan {plan_id}: "
                       f"WS={len(websocket_messages)}, DB={len(database_messages)}, "
                       f"Consistent={consistency_report['overall_consistent']}")
            
            return consistency_report
            
        except Exception as e:
            logger.error(f"❌ Failed to validate message format consistency: {e}")
            return {
                "plan_id": plan_id,
                "error": str(e),
                "overall_consistent": False
            }
    
    def _normalize_content(self, content: str) -> str:
        """Normalize content for comparison."""
        if not content:
            return ""
        return content.strip().lower()
    
    async def get_format_validation_report(self, plan_id: str) -> Dict[str, Any]:
        """
        Get a comprehensive format validation report for a plan's messages.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Dictionary with validation report
        """
        try:
            messages = await self.get_messages_for_plan(plan_id)
            
            report = {
                "plan_id": plan_id,
                "total_messages": len(messages),
                "validation_results": [],
                "format_distribution": {},
                "agent_distribution": {},
                "validation_summary": {
                    "valid_messages": 0,
                    "invalid_messages": 0,
                    "messages_with_warnings": 0,
                    "format_corrections_needed": 0
                }
            }
            
            # Validate each message
            for i, message in enumerate(messages):
                validation_result = self.validator.validate_message(message, strict_mode=True)
                
                result_summary = {
                    "message_index": i,
                    "agent_name": message.agent_name,
                    "agent_type": message.agent_type,
                    "content_length": len(message.content),
                    "is_valid": validation_result.is_valid,
                    "error_count": len(validation_result.errors),
                    "warning_count": len(validation_result.warnings),
                    "needs_normalization": validation_result.normalized_message is not None
                }
                
                if validation_result.errors:
                    result_summary["errors"] = validation_result.errors
                if validation_result.warnings:
                    result_summary["warnings"] = validation_result.warnings
                
                report["validation_results"].append(result_summary)
                
                # Update summary stats
                if validation_result.is_valid:
                    report["validation_summary"]["valid_messages"] += 1
                else:
                    report["validation_summary"]["invalid_messages"] += 1
                
                if validation_result.warnings:
                    report["validation_summary"]["messages_with_warnings"] += 1
                
                if validation_result.normalized_message:
                    report["validation_summary"]["format_corrections_needed"] += 1
                
                # Update distributions
                agent_type = message.agent_type
                report["agent_distribution"][agent_type] = report["agent_distribution"].get(agent_type, 0) + 1
            
            logger.info(f"📊 Generated format validation report for plan {plan_id}: "
                       f"{report['validation_summary']['valid_messages']}/{len(messages)} valid messages")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Failed to generate format validation report: {e}")
            return {
                "plan_id": plan_id,
                "error": str(e),
                "total_messages": 0
            }
    
    def get_persistence_stats(self) -> Dict[str, Any]:
        """Get persistence service statistics."""
        validator_stats = self.validator.get_validation_stats()
        
        return {
            **self.persistence_stats,
            "validation_stats": validator_stats,
            "success_rate": (
                self.persistence_stats["messages_saved"] / 
                max(self.persistence_stats["messages_saved"] + self.persistence_stats["messages_failed"], 1) * 100
            ),
            "validation_failure_rate": (
                self.persistence_stats["validation_failures"] / 
                max(self.persistence_stats["messages_saved"] + self.persistence_stats["messages_failed"], 1) * 100
            )
        }
    
    def reset_stats(self) -> None:
        """Reset all statistics."""
        self.persistence_stats = {
            "messages_saved": 0,
            "messages_failed": 0,
            "validation_failures": 0,
            "format_corrections": 0
        }
        self.validator.reset_stats()
    
    def _validate_message(self, message: AgentMessage) -> bool:
        """
        Validate a message object using the format validator.
        
        Args:
            message: AgentMessage to validate
            
        Returns:
            True if message is valid, False otherwise
        """
        validation_result = self.validator.validate_message(message, strict_mode=self.strict_validation)
        
        if not validation_result.is_valid:
            logger.error(f"❌ Message validation failed: {', '.join(validation_result.errors)}")
            return False
        
        if validation_result.warnings:
            logger.warning(f"⚠️ Message validation warnings: {', '.join(validation_result.warnings)}")
        
        return True
    
    async def get_message_count_for_plan(self, plan_id: str) -> int:
        """
        Get the count of messages for a specific plan.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Number of messages for the plan
        """
        try:
            if not plan_id or not plan_id.strip():
                return 0
            
            db = MongoDB.get_database()
            collection = db["messages"]
            
            count = await collection.count_documents({"plan_id": plan_id.strip()})
            return count
            
        except Exception as e:
            logger.error(f"❌ Failed to get message count for plan {plan_id}: {e}")
            return 0
    
    async def delete_messages_for_plan(self, plan_id: str) -> bool:
        """
        Delete all messages for a specific plan.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            if not plan_id or not plan_id.strip():
                logger.error("❌ Cannot delete messages: plan_id is required")
                return False
            
            db = MongoDB.get_database()
            collection = db["messages"]
            
            result = await collection.delete_many({"plan_id": plan_id.strip()})
            
            logger.info(f"🗑️ Deleted {result.deleted_count} messages for plan {plan_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete messages for plan {plan_id}: {e}")
            return False
    
    async def verify_message_chronological_ordering(self, plan_id: str) -> Dict[str, Any]:
        """
        Verify that messages for a plan are stored in chronological order.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Dictionary with verification results
        """
        try:
            if not plan_id or not plan_id.strip():
                return {
                    "plan_id": plan_id,
                    "is_chronological": False,
                    "error": "Invalid plan_id"
                }
            
            # Get messages from database
            messages = await self.get_messages_for_plan(plan_id.strip())
            
            if len(messages) <= 1:
                return {
                    "plan_id": plan_id,
                    "is_chronological": True,
                    "message_count": len(messages),
                    "note": "Single or no messages - chronological by definition"
                }
            
            # Check if timestamps are in chronological order
            is_chronological = True
            ordering_issues = []
            
            for i in range(1, len(messages)):
                prev_timestamp = messages[i-1].timestamp
                curr_timestamp = messages[i].timestamp
                
                if curr_timestamp < prev_timestamp:
                    is_chronological = False
                    ordering_issues.append({
                        "message_index": i,
                        "previous_timestamp": prev_timestamp.isoformat(),
                        "current_timestamp": curr_timestamp.isoformat(),
                        "time_difference_seconds": (prev_timestamp - curr_timestamp).total_seconds(),
                        "previous_agent": messages[i-1].agent_name,
                        "current_agent": messages[i].agent_name
                    })
            
            # Calculate time spans
            first_message_time = messages[0].timestamp
            last_message_time = messages[-1].timestamp
            total_duration = (last_message_time - first_message_time).total_seconds()
            
            # Check for duplicate timestamps
            timestamps = [msg.timestamp for msg in messages]
            unique_timestamps = set(timestamps)
            has_duplicates = len(timestamps) != len(unique_timestamps)
            
            # Find duplicate timestamp groups
            duplicate_groups = []
            if has_duplicates:
                from collections import defaultdict
                timestamp_groups = defaultdict(list)
                for i, timestamp in enumerate(timestamps):
                    timestamp_groups[timestamp].append(i)
                
                for timestamp, indices in timestamp_groups.items():
                    if len(indices) > 1:
                        duplicate_groups.append({
                            "timestamp": timestamp.isoformat(),
                            "message_indices": indices,
                            "agents": [messages[i].agent_name for i in indices]
                        })
            
            result = {
                "plan_id": plan_id,
                "is_chronological": is_chronological,
                "message_count": len(messages),
                "total_duration_seconds": total_duration,
                "first_message_time": first_message_time.isoformat(),
                "last_message_time": last_message_time.isoformat(),
                "has_duplicate_timestamps": has_duplicates,
                "ordering_issues_count": len(ordering_issues),
                "ordering_issues": ordering_issues[:10],  # Limit to first 10 issues
                "duplicate_timestamp_groups": duplicate_groups
            }
            
            if is_chronological:
                logger.info(f"✅ Messages for plan {plan_id} are in chronological order ({len(messages)} messages)")
            else:
                logger.warning(f"⚠️ Messages for plan {plan_id} have chronological ordering issues ({len(ordering_issues)} issues)")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to verify message chronological ordering for plan {plan_id}: {e}")
            return {
                "plan_id": plan_id,
                "is_chronological": False,
                "error": str(e)
            }
    
    async def test_connection(self) -> bool:
        """
        Test database connection and basic operations.
        
        Returns:
            True if connection test passes, False otherwise
        """
        try:
            # Test database connection
            if not await MongoDB.test_connection():
                return False
            
            # Test basic operations with a test message
            test_plan_id = "test_connection_plan"
            test_message = "Connection test message"
            
            # Save test message
            success = await self.save_agent_message(
                plan_id=test_plan_id,
                agent_name="TestAgent",
                content=test_message,
                agent_type="test"
            )
            
            if not success:
                return False
            
            # Retrieve test message
            messages = await self.get_messages_for_plan(test_plan_id)
            if not messages or messages[-1].content != test_message:
                return False
            
            # Clean up test message
            await self.delete_messages_for_plan(test_plan_id)
            
            logger.info("✅ Message persistence service connection test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Message persistence service connection test failed: {e}")
            return False


# Global service instance
_message_persistence_service: Optional[MessagePersistenceService] = None


def get_message_persistence_service(strict_validation: bool = False) -> MessagePersistenceService:
    """
    Get or create the global MessagePersistenceService instance.
    
    Args:
        strict_validation: Whether to apply strict validation rules
    
    Returns:
        MessagePersistenceService instance
    """
    global _message_persistence_service
    if _message_persistence_service is None:
        _message_persistence_service = MessagePersistenceService(strict_validation=strict_validation)
    return _message_persistence_service


def reset_message_persistence_service() -> None:
    """Reset the global service instance (useful for testing)."""
    global _message_persistence_service
    _message_persistence_service = None