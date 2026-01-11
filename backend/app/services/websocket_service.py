"""
WebSocket service for real-time communication with frontend.

Handles WebSocket connections, message routing, and real-time updates
for HITL approval workflows and agent progress tracking.

Enhanced with improved progress tracking, connection management, and error handling.
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set, List, Union
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types for better type safety."""
    # Connection management
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_ERROR = "connection_error"
    PING = "ping"
    PONG = "pong"
    
    # Agent execution
    AGENT_STREAM_START = "agent_stream_start"
    AGENT_MESSAGE_STREAMING = "agent_message_streaming"
    AGENT_STREAM_END = "agent_stream_end"
    AGENT_MESSAGE = "agent_message"
    AGENT_ERROR = "agent_error"
    
    # Progress tracking
    PROGRESS_UPDATE = "progress_update"
    STEP_PROGRESS = "step_progress"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    
    # HITL interactions
    PLAN_APPROVAL_REQUEST = "plan_approval_request"
    PLAN_APPROVAL_RESPONSE = "plan_approval_response"
    USER_CLARIFICATION_REQUEST = "user_clarification_request"
    USER_CLARIFICATION_RESPONSE = "user_clarification_response"
    
    # Results and completion
    FINAL_RESULT_MESSAGE = "final_result_message"
    SYSTEM_MESSAGE = "system_message"
    ERROR_NOTIFICATION = "error_notification"


class ConnectionState(Enum):
    """WebSocket connection states."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class ProgressInfo:
    """Enhanced progress information."""
    current_step: int
    total_steps: int
    current_agent: str
    progress_percentage: float
    timestamp: str = None
    estimated_completion: Optional[datetime] = None
    step_duration: Optional[float] = None
    average_step_duration: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        if self.estimated_completion:
            result['estimated_completion'] = self.estimated_completion.isoformat() + "Z"
        return result


@dataclass
class ConnectionMetadata:
    """Enhanced connection metadata."""
    plan_id: str
    user_id: Optional[str]
    connected_at: datetime
    last_activity: datetime
    state: ConnectionState
    message_count: int = 0
    error_count: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class WebSocketMessage:
    """Enhanced WebSocket message structure."""
    type: str
    data: Dict[str, Any]
    timestamp: str = None
    message_id: str = None
    correlation_id: Optional[str] = None
    priority: int = 0  # Higher numbers = higher priority
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class EnhancedWebSocketManager:
    """
    Enhanced WebSocket manager with improved progress tracking, connection management,
    and error handling capabilities.
    
    Features:
    - Granular progress tracking with time estimates
    - Connection state management and recovery
    - Message queuing for disconnected clients
    - Concurrent connection handling
    - Enhanced error handling and logging
    """
    
    def __init__(self):
        self.connections: Dict[str, Set[Any]] = {}  # plan_id -> set of websocket connections
        self.connection_metadata: Dict[Any, ConnectionMetadata] = {}  # connection -> metadata
        self.message_history: Dict[str, List[WebSocketMessage]] = {}  # plan_id -> messages
        self.message_queue: Dict[str, List[WebSocketMessage]] = {}  # plan_id -> queued messages
        self.progress_tracking: Dict[str, ProgressInfo] = {}  # plan_id -> progress info
        self.step_timings: Dict[str, List[float]] = {}  # plan_id -> step durations
        
        # Pending task management for WebSocket coordination
        self.pending_tasks: Dict[str, Dict[str, Any]] = {}  # plan_id -> task info
        
        # Configuration
        self.max_history_per_plan = 100
        self.max_queue_size = 50
        self.connection_timeout = timedelta(minutes=30)
        self.heartbeat_interval = 30  # seconds
        self.max_reconnect_attempts = 3
        
        # Enhanced managers
        self.recovery_manager = ConnectionRecoveryManager(self)
        self.concurrent_manager = ConcurrentConnectionManager(self)
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background maintenance tasks."""
        try:
            # Only start tasks if there's a running event loop
            loop = asyncio.get_running_loop()
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            if self._heartbeat_task is None or self._heartbeat_task.done():
                self._heartbeat_task = asyncio.create_task(self._periodic_heartbeat())
        except RuntimeError:
            # No event loop running, tasks will be started when needed
            pass
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of inactive connections and old data."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self.cleanup_inactive_connections()
                self._cleanup_old_data()
                self.recovery_manager.cleanup_expired_recovery_sessions()
                self.concurrent_manager.cleanup_connection_locks()
            except Exception as e:
                logger.error(f"❌ Error in periodic cleanup: {e}")
    
    async def _periodic_heartbeat(self):
        """Send periodic heartbeat to maintain connections."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                await self._send_heartbeat()
            except Exception as e:
                logger.error(f"❌ Error in periodic heartbeat: {e}")
    
    async def _send_heartbeat(self):
        """Send heartbeat ping to all connections."""
        for plan_id in list(self.connections.keys()):
            try:
                await self.send_message(
                    plan_id,
                    {"type": MessageType.PING.value, "timestamp": datetime.utcnow().isoformat() + "Z"},
                    MessageType.PING.value
                )
            except Exception as e:
                logger.debug(f"Heartbeat failed for plan {plan_id}: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old message history and progress data."""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Clean up message history
        for plan_id in list(self.message_history.keys()):
            if plan_id not in self.connections:
                # Remove history for plans with no active connections
                old_messages = self.message_history[plan_id]
                if old_messages and len(old_messages) > 0:
                    # Keep only recent messages
                    recent_messages = [
                        msg for msg in old_messages
                        if datetime.fromisoformat(msg.timestamp.replace('Z', '+00:00')) > cutoff_time
                    ]
                    if recent_messages:
                        self.message_history[plan_id] = recent_messages[-self.max_history_per_plan:]
                    else:
                        del self.message_history[plan_id]
        
        # Clean up progress tracking for inactive plans
        for plan_id in list(self.progress_tracking.keys()):
            if plan_id not in self.connections:
                del self.progress_tracking[plan_id]
                if plan_id in self.step_timings:
                    del self.step_timings[plan_id]
        
        # Clean up old pending tasks (older than 1 hour)
        for plan_id in list(self.pending_tasks.keys()):
            task_info = self.pending_tasks[plan_id]
            try:
                registered_time = datetime.fromisoformat(task_info["registered_at"].replace('Z', '+00:00'))
                if datetime.utcnow() - registered_time.replace(tzinfo=None) > timedelta(hours=1):
                    logger.warning(f"🧹 Removing stale pending task for plan {plan_id}")
                    del self.pending_tasks[plan_id]
            except (ValueError, KeyError):
                # Invalid timestamp, remove the task
                del self.pending_tasks[plan_id]
        
    async def connect(
        self,
        websocket: Any,
        plan_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a new WebSocket connection with enhanced tracking and validation.
        
        Args:
            websocket: WebSocket connection object
            plan_id: Plan identifier to associate with connection
            user_id: Optional user identifier
            metadata: Optional connection metadata
        """
        # Acquire connection lock to prevent race conditions
        async with await self.concurrent_manager.acquire_connection_lock(plan_id):
            # Validate new connection
            if not await self.concurrent_manager.validate_new_connection(plan_id, user_id):
                raise ConnectionError(f"Connection limit exceeded for plan {plan_id} or user {user_id}")
            
            # Check if this is a reconnection
            is_reconnection = plan_id in self.recovery_manager.recovery_attempts
            
            if is_reconnection:
                if not self.recovery_manager.should_allow_reconnection(plan_id):
                    raise ConnectionError(f"Reconnection not allowed for plan {plan_id}")
            
            # Handle duplicate connections
            await self.concurrent_manager.handle_duplicate_connection(plan_id, user_id, websocket)
            
            if plan_id not in self.connections:
                self.connections[plan_id] = set()
            
            self.connections[plan_id].add(websocket)
            
            # Store enhanced connection metadata
            now = datetime.utcnow()
            self.connection_metadata[websocket] = ConnectionMetadata(
                plan_id=plan_id,
                user_id=user_id,
                connected_at=now,
                last_activity=now,
                state=ConnectionState.CONNECTED,
                metadata=metadata or {}
            )
            
            logger.info(f"🔌 WebSocket connected for plan {plan_id} (user: {user_id}) - Reconnection: {is_reconnection}")
            
            # Handle successful reconnection
            if is_reconnection:
                await self.recovery_manager.handle_successful_reconnection(plan_id, user_id)
            
            # Send connection confirmation with enhanced info
            await self._send_to_connection(websocket, WebSocketMessage(
                type=MessageType.CONNECTION_ESTABLISHED.value,
                data={
                    "plan_id": plan_id,
                    "user_id": user_id,
                    "status": "reconnected" if is_reconnection else "connected",
                    "server_time": now.isoformat() + "Z",
                    "connection_count": len(self.connections[plan_id]),
                    "capabilities": {
                        "progress_tracking": True,
                        "message_history": True,
                        "error_recovery": True,
                        "heartbeat": True,
                        "message_queuing": True
                    }
                }
            ))
            
            # Send queued messages if any
            if plan_id in self.message_queue:
                queued_messages = self.message_queue[plan_id]
                logger.info(f"📬 Sending {len(queued_messages)} queued messages for plan {plan_id}")
                
                for message in queued_messages:
                    await self._send_to_connection(websocket, message)
                
                # Clear the queue
                del self.message_queue[plan_id]
            
            # Send recent message history if available
            elif plan_id in self.message_history:
                recent_messages = self.message_history[plan_id][-10:]  # Last 10 messages
                if recent_messages:
                    logger.info(f"📜 Sending {len(recent_messages)} recent messages for plan {plan_id}")
                    for message in recent_messages:
                        await self._send_to_connection(websocket, message)
            
            # Send current progress if available
            if plan_id in self.progress_tracking:
                progress = self.progress_tracking[plan_id]
                await self._send_to_connection(websocket, WebSocketMessage(
                    type=MessageType.PROGRESS_UPDATE.value,
                    data={
                        "plan_id": plan_id,
                        **progress.to_dict()
                    }
                ))
            
            # Execute pending task if available (WebSocket coordination fix)
            if plan_id in self.pending_tasks:
                logger.info(f"🚀 Executing pending task for plan {plan_id} now that WebSocket is connected")
                task_info = self.pending_tasks[plan_id]
                
                # Execute the pending task in background
                asyncio.create_task(self._execute_pending_task(plan_id, task_info))
                
                # Remove from pending tasks
                del self.pending_tasks[plan_id]
    
    async def disconnect(self, websocket: Any) -> None:
        """
        Unregister a WebSocket connection with enhanced cleanup.
        
        Args:
            websocket: WebSocket connection to remove
        """
        if websocket not in self.connection_metadata:
            return
        
        metadata = self.connection_metadata[websocket]
        plan_id = metadata.plan_id
        user_id = metadata.user_id
        
        # Update connection state
        metadata.state = ConnectionState.DISCONNECTING
        
        # Remove from connections
        if plan_id in self.connections:
            self.connections[plan_id].discard(websocket)
            if not self.connections[plan_id]:
                del self.connections[plan_id]
        
        # Remove metadata
        del self.connection_metadata[websocket]
        
        logger.info(f"🔌 WebSocket disconnected for plan {plan_id} (user: {user_id})")
        
        # Log connection statistics
        connection_duration = datetime.utcnow() - metadata.connected_at
        logger.debug(f"📊 Connection stats - Duration: {connection_duration}, Messages: {metadata.message_count}, Errors: {metadata.error_count}")
    
    async def send_message(
        self,
        plan_id: str,
        message_data: Dict[str, Any],
        message_type: Optional[str] = None,
        priority: int = 0,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Send message to all connections for a plan with enhanced features.
        
        Args:
            plan_id: Plan identifier
            message_data: Message data to send
            message_type: Optional message type (extracted from data if not provided)
            priority: Message priority (higher = more important)
            correlation_id: Optional correlation ID for tracking
        """
        # Create enhanced message
        msg_type = message_type or message_data.get("type", "unknown")
        message = WebSocketMessage(
            type=msg_type,
            data=message_data,
            priority=priority,
            correlation_id=correlation_id
        )
        
        # Store in history
        if plan_id not in self.message_history:
            self.message_history[plan_id] = []
        
        self.message_history[plan_id].append(message)
        
        # Trim history if too long
        if len(self.message_history[plan_id]) > self.max_history_per_plan:
            self.message_history[plan_id] = self.message_history[plan_id][-self.max_history_per_plan:]
        
        # Save agent messages to database for persistence
        await self._save_message_to_database(plan_id, msg_type, message_data)
        
        # Update progress tracking if this is a progress message
        if msg_type in [MessageType.PROGRESS_UPDATE.value, MessageType.STEP_PROGRESS.value]:
            self._update_progress_tracking(plan_id, message_data)
        
        # Send to active connections or queue for later
        if plan_id in self.connections and self.connections[plan_id]:
            connections = list(self.connections[plan_id])  # Copy to avoid modification during iteration
            successful_sends = 0
            
            for websocket in connections:
                try:
                    await self._send_to_connection(websocket, message)
                    successful_sends += 1
                    
                    # Update connection metadata
                    if websocket in self.connection_metadata:
                        self.connection_metadata[websocket].message_count += 1
                        self.connection_metadata[websocket].last_activity = datetime.utcnow()
                        
                except Exception as e:
                    logger.error(f"❌ Failed to send message to WebSocket: {e}")
                    # Update error count
                    if websocket in self.connection_metadata:
                        self.connection_metadata[websocket].error_count += 1
                    # Remove failed connection
                    await self.disconnect(websocket)
            
            logger.debug(f"📤 Sent {msg_type} message to {successful_sends}/{len(connections)} connections for plan {plan_id}")
        else:
            # Queue message for when client reconnects
            if plan_id not in self.message_queue:
                self.message_queue[plan_id] = []
            
            self.message_queue[plan_id].append(message)
            
            # Trim queue if too long
            if len(self.message_queue[plan_id]) > self.max_queue_size:
                self.message_queue[plan_id] = self.message_queue[plan_id][-self.max_queue_size:]
            
            logger.debug(f"📬 Queued {msg_type} message for plan {plan_id} (no active connections)")
    
    def _update_progress_tracking(self, plan_id: str, message_data: Dict[str, Any]) -> None:
        """Update internal progress tracking."""
        data = message_data.get("data", {})
        
        if "current_step" in data and "total_steps" in data:
            current_step = data["current_step"]
            total_steps = data["total_steps"]
            current_agent = data.get("current_agent", "unknown")
            
            # Calculate timing information
            now = datetime.utcnow()
            step_duration = None
            average_duration = None
            estimated_completion = None
            
            if plan_id in self.progress_tracking:
                prev_progress = self.progress_tracking[plan_id]
                if prev_progress.current_step < current_step:
                    # Step completed, calculate duration
                    try:
                        prev_time = datetime.fromisoformat(prev_progress.timestamp.replace('Z', '+00:00'))
                        step_duration = (now - prev_time.replace(tzinfo=None)).total_seconds()
                    except (ValueError, AttributeError):
                        # Fallback if timestamp parsing fails
                        step_duration = None
                    
                    # Track step timings
                    if plan_id not in self.step_timings:
                        self.step_timings[plan_id] = []
                    self.step_timings[plan_id].append(step_duration)
                    
                    # Calculate average duration
                    if self.step_timings[plan_id]:
                        average_duration = sum(self.step_timings[plan_id]) / len(self.step_timings[plan_id])
                        
                        # Estimate completion time
                        remaining_steps = total_steps - current_step
                        if remaining_steps > 0 and average_duration:
                            estimated_completion = now + timedelta(seconds=remaining_steps * average_duration)
            
            # Update progress tracking
            progress_percentage = (current_step / total_steps) * 100 if total_steps > 0 else 0
            
            self.progress_tracking[plan_id] = ProgressInfo(
                current_step=current_step,
                total_steps=total_steps,
                current_agent=current_agent,
                progress_percentage=round(progress_percentage, 1),
                estimated_completion=estimated_completion,
                step_duration=step_duration,
                average_step_duration=average_duration
            )
            
            # Update message data with enhanced progress info
            if "data" in message_data:
                message_data["data"].update({
                    "estimated_completion": estimated_completion.isoformat() + "Z" if estimated_completion else None,
                    "step_duration": step_duration,
                    "average_step_duration": average_duration
                })
    
    async def _save_message_to_database(self, plan_id: str, msg_type: str, message_data: Dict[str, Any]) -> None:
        """
        Save agent messages to database for persistence.
        
        Args:
            plan_id: Plan identifier
            msg_type: Message type
            message_data: Message data
        """
        # Skip certain message types that are too noisy
        if msg_type in [
            MessageType.PING.value,
            MessageType.PONG.value,
            MessageType.CONNECTION_ESTABLISHED.value,
            MessageType.PROGRESS_UPDATE.value,
            MessageType.STEP_PROGRESS.value,
            "ping", "pong", "connection_established", "progress_update", "step_progress"
        ]:
            return
        
        # For streaming messages, only save the final complete message
        if msg_type in [MessageType.AGENT_MESSAGE_STREAMING.value, "agent_message_streaming"]:
            # Don't save individual streaming chunks, wait for stream end
            return
        
        try:
            # Import here to avoid circular imports
            from app.models.message import AgentMessage
            from app.db.repositories import MessageRepository
            
            # Extract message content and agent info
            data = message_data.get("data", {})
            
            # Try multiple ways to extract content
            content = ""
            if "content" in data:
                content = data["content"]
            elif "message" in data:
                content = data["message"]
            elif "response" in data:
                content = data["response"]
            elif msg_type == MessageType.AGENT_STREAM_END.value and "agent" in message_data:
                # For stream end messages, try to get the complete response from WebSocket history
                agent = message_data.get("agent", "Unknown")
                
                # Look for accumulated streaming content in message history
                if plan_id in self.message_history:
                    streaming_content = []
                    for msg in self.message_history[plan_id]:
                        if (msg.type in [MessageType.AGENT_MESSAGE_STREAMING.value, "agent_message_streaming"] and
                            msg.data.get("agent") == agent):
                            chunk = msg.data.get("content", "")
                            if chunk:
                                streaming_content.append(chunk)
                    
                    if streaming_content:
                        content = "".join(streaming_content)
                    else:
                        content = f"Agent {agent} completed analysis"
                else:
                    content = f"Agent {agent} completed analysis"
            else:
                # Fallback to string representation, but clean it up
                content_str = str(message_data)
                if len(content_str) > 200:
                    content = content_str[:200] + "..."
                else:
                    content = content_str
            
            # Skip saving if content is empty or too short
            if not content or len(content.strip()) < 10:
                return
            
            # Extract agent information
            agent_name = (
                data.get("agent") or 
                data.get("agent_name") or 
                message_data.get("agent") or 
                "System"
            )
            agent_type = data.get("agent_type", "system")
            
            # Create and save message
            message = AgentMessage(
                plan_id=plan_id,
                agent_name=agent_name,
                agent_type=agent_type,
                content=content,
                timestamp=datetime.utcnow(),
                metadata=data
            )
            
            await MessageRepository.create(message)
            logger.debug(f"💾 Saved {msg_type} message to database for plan {plan_id}: {agent_name} ({len(content)} chars)")
            
        except Exception as e:
            logger.error(f"❌ Failed to save message to database: {e}")
            # Don't raise - message sending should continue even if database save fails
    
    async def send_to_user(
        self,
        user_id: str,
        message_data: Dict[str, Any],
        message_type: Optional[str] = None,
        priority: int = 0
    ) -> None:
        """
        Send message to all connections for a specific user with enhanced features.
        
        Args:
            user_id: User identifier
            message_data: Message data to send
            message_type: Optional message type
            priority: Message priority
        """
        msg_type = message_type or message_data.get("type", "unknown")
        message = WebSocketMessage(
            type=msg_type,
            data=message_data,
            priority=priority
        )
        
        sent_count = 0
        failed_connections = []
        
        for websocket, metadata in self.connection_metadata.items():
            if metadata.user_id == user_id:
                try:
                    await self._send_to_connection(websocket, message)
                    sent_count += 1
                    metadata.message_count += 1
                    metadata.last_activity = datetime.utcnow()
                except Exception as e:
                    logger.error(f"❌ Failed to send message to user {user_id}: {e}")
                    metadata.error_count += 1
                    failed_connections.append(websocket)
        
        # Clean up failed connections
        for websocket in failed_connections:
            await self.disconnect(websocket)
        
        logger.debug(f"📤 Sent {msg_type} message to {sent_count} connections for user {user_id}")
    
    async def broadcast_system_message(
        self,
        message_data: Dict[str, Any],
        message_type: str = "system_message",
        priority: int = 1
    ) -> None:
        """
        Broadcast system message to all connections with enhanced features.
        
        Args:
            message_data: Message data to broadcast
            message_type: Message type
            priority: Message priority
        """
        message = WebSocketMessage(
            type=message_type,
            data=message_data,
            priority=priority
        )
        
        sent_count = 0
        failed_connections = []
        
        for websocket, metadata in list(self.connection_metadata.items()):
            try:
                await self._send_to_connection(websocket, message)
                sent_count += 1
                metadata.message_count += 1
                metadata.last_activity = datetime.utcnow()
            except Exception as e:
                logger.error(f"❌ Failed to broadcast system message: {e}")
                metadata.error_count += 1
                failed_connections.append(websocket)
        
        # Clean up failed connections
        for websocket in failed_connections:
            await self.disconnect(websocket)
        
        logger.info(f"📢 Broadcasted {message_type} to {sent_count} connections")
    
    async def send_enhanced_progress_update(
        self,
        plan_id: str,
        current_step: int,
        total_steps: int,
        current_agent: str,
        step_description: Optional[str] = None,
        agent_status: str = "running",
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send enhanced progress update with detailed information.
        
        Args:
            plan_id: Plan identifier
            current_step: Current step number (1-indexed)
            total_steps: Total number of steps
            current_agent: Currently executing agent
            step_description: Optional description of current step
            agent_status: Status of current agent
            additional_data: Additional data to include
        """
        progress_data = {
            "plan_id": plan_id,
            "current_step": current_step,
            "total_steps": total_steps,
            "current_agent": current_agent,
            "agent_status": agent_status,
            "step_description": step_description,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if additional_data:
            progress_data.update(additional_data)
        
        await self.send_message(
            plan_id,
            {
                "type": MessageType.PROGRESS_UPDATE.value,
                "data": progress_data
            },
            MessageType.PROGRESS_UPDATE.value,
            priority=1
        )
    
    async def send_agent_streaming_start(
        self,
        plan_id: str,
        agent_name: str,
        step_number: Optional[int] = None,
        estimated_duration: Optional[float] = None
    ) -> None:
        """Send agent streaming start notification."""
        data = {
            "plan_id": plan_id,
            "agent_name": agent_name,
            "status": "streaming_started",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        if step_number is not None:
            data["step_number"] = step_number
        if estimated_duration is not None:
            data["estimated_duration"] = estimated_duration
        
        await self.send_message(
            plan_id,
            {
                "type": MessageType.AGENT_STREAM_START.value,
                "data": data
            },
            MessageType.AGENT_STREAM_START.value,
            priority=1
        )
    
    async def send_agent_streaming_content(
        self,
        plan_id: str,
        agent_name: str,
        content: str,
        is_complete: bool = False
    ) -> None:
        """Send streaming content from agent."""
        message_type = MessageType.AGENT_STREAM_END.value if is_complete else MessageType.AGENT_MESSAGE_STREAMING.value
        
        await self.send_message(
            plan_id,
            {
                "type": message_type,
                "data": {
                    "plan_id": plan_id,
                    "agent_name": agent_name,
                    "content": content,
                    "is_complete": is_complete,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            },
            message_type,
            priority=2  # High priority for streaming content
        )
    
    async def send_error_notification(
        self,
        plan_id: str,
        error_type: str,
        error_message: str,
        agent_name: Optional[str] = None,
        recoverable: bool = True,
        retry_count: int = 0
    ) -> None:
        """Send enhanced error notification."""
        await self.send_message(
            plan_id,
            {
                "type": MessageType.ERROR_NOTIFICATION.value,
                "data": {
                    "plan_id": plan_id,
                    "error_type": error_type,
                    "error_message": error_message,
                    "agent_name": agent_name,
                    "recoverable": recoverable,
                    "retry_count": retry_count,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            },
            MessageType.ERROR_NOTIFICATION.value,
            priority=3  # Highest priority for errors
        )
    
    def get_connection_count(self, plan_id: Optional[str] = None) -> int:
        """
        Get number of active connections.
        
        Args:
            plan_id: Optional plan ID to filter by
            
        Returns:
            Number of active connections
        """
        if plan_id:
            return len(self.connections.get(plan_id, set()))
        return len(self.connection_metadata)
    
    def get_connected_plans(self) -> List[str]:
        """
        Get list of plan IDs with active connections.
        
        Returns:
            List of plan IDs
        """
        return list(self.connections.keys())
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get enhanced connection statistics for monitoring.
        
        Returns:
            Dictionary with connection statistics
        """
        total_connections = len(self.connection_metadata)
        active_plans = len(self.connections)
        
        # Count connections per plan
        connections_per_plan = {
            plan_id: len(connections)
            for plan_id, connections in self.connections.items()
        }
        
        # Count messages per plan
        messages_per_plan = {
            plan_id: len(messages)
            for plan_id, messages in self.message_history.items()
        }
        
        # Count queued messages per plan
        queued_messages_per_plan = {
            plan_id: len(messages)
            for plan_id, messages in self.message_queue.items()
        }
        
        # Connection state distribution
        state_distribution = {}
        for metadata in self.connection_metadata.values():
            state = metadata.state.value
            state_distribution[state] = state_distribution.get(state, 0) + 1
        
        # Calculate average connection duration
        now = datetime.utcnow()
        connection_durations = [
            (now - metadata.connected_at).total_seconds()
            for metadata in self.connection_metadata.values()
        ]
        avg_connection_duration = sum(connection_durations) / len(connection_durations) if connection_durations else 0
        
        # Error statistics
        total_errors = sum(metadata.error_count for metadata in self.connection_metadata.values())
        total_messages_sent = sum(metadata.message_count for metadata in self.connection_metadata.values())
        
        return {
            "total_connections": total_connections,
            "active_plans": active_plans,
            "connections_per_plan": connections_per_plan,
            "messages_per_plan": messages_per_plan,
            "queued_messages_per_plan": queued_messages_per_plan,
            "total_messages": sum(messages_per_plan.values()),
            "total_queued_messages": sum(queued_messages_per_plan.values()),
            "state_distribution": state_distribution,
            "average_connection_duration_seconds": round(avg_connection_duration, 2),
            "total_errors": total_errors,
            "total_messages_sent": total_messages_sent,
            "error_rate": round(total_errors / max(total_messages_sent, 1) * 100, 2)
        }
    
    def get_progress_info(self, plan_id: str) -> Optional[ProgressInfo]:
        """
        Get current progress information for a plan.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            ProgressInfo object or None if not found
        """
        return self.progress_tracking.get(plan_id)
    
    def get_queued_message_count(self, plan_id: str) -> int:
        """
        Get number of queued messages for a plan.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Number of queued messages
        """
        return len(self.message_queue.get(plan_id, []))
    
    def register_pending_task(
        self,
        plan_id: str,
        task_func: Any,
        task_args: tuple,
        task_kwargs: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a pending task to be executed when WebSocket connects.
        
        This solves the issue where task execution starts before WebSocket connection,
        causing agents to lose streaming context and fall back to non-streaming behavior.
        
        Args:
            plan_id: Plan identifier
            task_func: Function to execute
            task_args: Arguments for the function
            task_kwargs: Optional keyword arguments for the function
        """
        logger.info(f"📋 Registering pending task for plan {plan_id} - will execute when WebSocket connects")
        
        self.pending_tasks[plan_id] = {
            "task_func": task_func,
            "task_args": task_args,
            "task_kwargs": task_kwargs or {},
            "registered_at": datetime.utcnow().isoformat() + "Z"
        }
        
        # If WebSocket is already connected, execute immediately
        if plan_id in self.connections and self.connections[plan_id]:
            logger.info(f"🚀 WebSocket already connected for plan {plan_id}, executing task immediately")
            asyncio.create_task(self._execute_pending_task(plan_id, self.pending_tasks[plan_id]))
            del self.pending_tasks[plan_id]
    
    async def _execute_pending_task(self, plan_id: str, task_info: Dict[str, Any]) -> None:
        """
        Execute a pending task.
        
        Args:
            plan_id: Plan identifier
            task_info: Task information dictionary
        """
        try:
            task_func = task_info["task_func"]
            task_args = task_info["task_args"]
            task_kwargs = task_info["task_kwargs"]
            
            logger.info(f"🎯 Executing pending task for plan {plan_id}")
            
            # Execute the task
            if asyncio.iscoroutinefunction(task_func):
                await task_func(*task_args, **task_kwargs)
            else:
                task_func(*task_args, **task_kwargs)
                
            logger.info(f"✅ Pending task executed successfully for plan {plan_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to execute pending task for plan {plan_id}: {e}")
            
            # Send error notification
            await self.send_error_notification(
                plan_id,
                "task_execution_error",
                f"Failed to execute pending task: {str(e)}",
                recoverable=False
            )
    
    async def cleanup_inactive_connections(self) -> None:
        """Clean up inactive or stale connections with enhanced logic."""
        inactive_connections = []
        now = datetime.utcnow()
        
        for websocket, metadata in self.connection_metadata.items():
            # Check for timeout
            if now - metadata.last_activity > self.connection_timeout:
                logger.info(f"🧹 Cleaning up inactive connection for plan {metadata.plan_id} (timeout)")
                inactive_connections.append(websocket)
                continue
            
            # Check for too many errors
            if metadata.error_count > 10:
                logger.info(f"🧹 Cleaning up error-prone connection for plan {metadata.plan_id} (errors: {metadata.error_count})")
                inactive_connections.append(websocket)
                continue
            
            # Try to ping the connection to check if it's still alive
            try:
                if hasattr(websocket, 'ping'):
                    await websocket.ping()
                elif hasattr(websocket, 'send_text'):
                    # Send a ping message
                    await websocket.send_text(json.dumps({
                        "type": MessageType.PING.value,
                        "timestamp": now.isoformat() + "Z"
                    }))
            except Exception as e:
                logger.debug(f"Connection ping failed for plan {metadata.plan_id}: {e}")
                inactive_connections.append(websocket)
        
        # Clean up inactive connections
        for websocket in inactive_connections:
            await self.disconnect(websocket)
        
        if inactive_connections:
            logger.info(f"🧹 Cleaned up {len(inactive_connections)} inactive connections")
    
    async def handle_connection_error(
        self,
        websocket: Any,
        error: Exception,
        plan_id: Optional[str] = None
    ) -> None:
        """
        Handle connection errors with enhanced recovery logic.
        
        Args:
            websocket: WebSocket connection that errored
            error: The error that occurred
            plan_id: Optional plan ID for context
        """
        if websocket in self.connection_metadata:
            metadata = self.connection_metadata[websocket]
            metadata.error_count += 1
            metadata.state = ConnectionState.ERROR
            
            plan_id = plan_id or metadata.plan_id
            user_id = metadata.user_id
            
            logger.error(f"❌ WebSocket error for plan {plan_id}: {error}")
            
            # Handle connection drop for recovery
            await self.recovery_manager.handle_connection_drop(plan_id, user_id, error)
            
            # Send error notification to other connections for the same plan
            if plan_id in self.connections and len(self.connections[plan_id]) > 1:
                await self.send_error_notification(
                    plan_id,
                    "connection_error",
                    f"Connection error occurred: {str(error)}",
                    recoverable=True
                )
        
        # Disconnect the problematic connection
        await self.disconnect(websocket)
    
    async def _send_to_connection(self, websocket: Any, message: WebSocketMessage) -> None:
        """
        Send message to a specific WebSocket connection with enhanced error handling.
        
        Args:
            websocket: WebSocket connection
            message: Message to send
        """
        try:
            # Convert message to JSON
            message_json = json.dumps(message.to_dict())
            
            # Send message (implementation depends on WebSocket library)
            if hasattr(websocket, 'send_text'):
                await websocket.send_text(message_json)
            elif hasattr(websocket, 'send'):
                await websocket.send(message_json)
            else:
                # Mock implementation for testing
                if hasattr(websocket, 'messages'):
                    websocket.messages.append(message.to_dict())
                
        except Exception as e:
            logger.error(f"❌ Failed to send WebSocket message: {e}")
            # Handle the connection error
            await self.handle_connection_error(websocket, e)
            raise
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the WebSocket manager."""
        logger.info("🔄 Shutting down WebSocket manager...")
        
        # Cancel background tasks
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
        
        # Disconnect all connections
        connections_to_disconnect = list(self.connection_metadata.keys())
        for websocket in connections_to_disconnect:
            try:
                await self.disconnect(websocket)
            except Exception as e:
                logger.error(f"Error disconnecting WebSocket during shutdown: {e}")
        
        # Clear all data
        self.connections.clear()
        self.connection_metadata.clear()
        self.message_history.clear()
        self.message_queue.clear()
        self.progress_tracking.clear()
        self.step_timings.clear()
        self.pending_tasks.clear()
        
        logger.info("✅ WebSocket manager shutdown complete")


# Maintain backward compatibility
class WebSocketManager(EnhancedWebSocketManager):
    """Backward compatibility alias for the enhanced WebSocket manager."""
    pass


# Global WebSocket manager instance
_websocket_manager: Optional[EnhancedWebSocketManager] = None


def get_websocket_manager() -> EnhancedWebSocketManager:
    """
    Get or create the global WebSocket manager instance.
    
    Returns:
        EnhancedWebSocketManager instance
    """
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = EnhancedWebSocketManager()
    return _websocket_manager


def reset_websocket_manager() -> None:
    """Reset the global WebSocket manager (useful for testing)."""
    global _websocket_manager
    if _websocket_manager is not None:
        # Try to shutdown gracefully
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(_websocket_manager.shutdown())
            else:
                loop.run_until_complete(_websocket_manager.shutdown())
        except Exception as e:
            logger.warning(f"Error during WebSocket manager shutdown: {e}")
    _websocket_manager = None


class MockWebSocketConnection:
    """Enhanced mock WebSocket connection for testing."""
    
    def __init__(self, plan_id: str, user_id: Optional[str] = None):
        self.plan_id = plan_id
        self.user_id = user_id
        self.messages: List[Dict[str, Any]] = []
        self.connected = True
        self.error_count = 0
        self.last_ping = None
    
    async def send_text(self, message: str) -> None:
        """Mock send_text method."""
        if not self.connected:
            raise ConnectionError("WebSocket is disconnected")
        
        try:
            self.messages.append(json.loads(message))
        except json.JSONDecodeError as e:
            self.error_count += 1
            raise ValueError(f"Invalid JSON message: {e}")
    
    async def send(self, message: str) -> None:
        """Mock send method."""
        await self.send_text(message)
    
    async def ping(self) -> None:
        """Mock ping method."""
        if not self.connected:
            raise ConnectionError("WebSocket is disconnected")
        self.last_ping = datetime.utcnow()
    
    def disconnect(self) -> None:
        """Mock disconnect."""
        self.connected = False
    
    def get_messages_by_type(self, message_type: str) -> List[Dict[str, Any]]:
        """Get messages filtered by type."""
        return [msg for msg in self.messages if msg.get("type") == message_type]
    
    def get_latest_message(self) -> Optional[Dict[str, Any]]:
        """Get the most recent message."""
        return self.messages[-1] if self.messages else None
    
    def clear_messages(self) -> None:
        """Clear all messages."""
        self.messages.clear()


class ConnectionRecoveryManager:
    """
    Manages connection recovery and reconnection logic for WebSocket clients.
    """
    
    def __init__(self, websocket_manager: EnhancedWebSocketManager):
        self.websocket_manager = websocket_manager
        self.recovery_attempts: Dict[str, int] = {}  # plan_id -> attempt count
        self.recovery_timeouts: Dict[str, datetime] = {}  # plan_id -> timeout
        self.max_recovery_attempts = 5
        self.recovery_timeout_minutes = 10
    
    async def handle_connection_drop(
        self,
        plan_id: str,
        user_id: Optional[str] = None,
        error: Optional[Exception] = None
    ) -> None:
        """
        Handle connection drop and prepare for recovery.
        
        Args:
            plan_id: Plan identifier
            user_id: Optional user identifier
            error: Optional error that caused the drop
        """
        logger.warning(f"🔄 Connection dropped for plan {plan_id} (user: {user_id})")
        
        # Track recovery attempts
        if plan_id not in self.recovery_attempts:
            self.recovery_attempts[plan_id] = 0
        
        self.recovery_attempts[plan_id] += 1
        
        # Set recovery timeout
        self.recovery_timeouts[plan_id] = datetime.utcnow() + timedelta(minutes=self.recovery_timeout_minutes)
        
        # Send notification to other connections for the same plan
        if plan_id in self.websocket_manager.connections:
            await self.websocket_manager.send_message(
                plan_id,
                {
                    "type": MessageType.CONNECTION_ERROR.value,
                    "data": {
                        "plan_id": plan_id,
                        "user_id": user_id,
                        "error_type": "connection_dropped",
                        "error_message": f"Connection dropped: {str(error) if error else 'Unknown reason'}",
                        "recovery_attempt": self.recovery_attempts[plan_id],
                        "max_attempts": self.max_recovery_attempts,
                        "recovery_timeout": self.recovery_timeouts[plan_id].isoformat() + "Z",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                },
                MessageType.CONNECTION_ERROR.value,
                priority=2
            )
        
        # Log recovery status
        logger.info(f"🔄 Recovery attempt {self.recovery_attempts[plan_id]}/{self.max_recovery_attempts} for plan {plan_id}")
    
    async def handle_successful_reconnection(
        self,
        plan_id: str,
        user_id: Optional[str] = None
    ) -> None:
        """
        Handle successful reconnection.
        
        Args:
            plan_id: Plan identifier
            user_id: Optional user identifier
        """
        logger.info(f"✅ Successful reconnection for plan {plan_id} (user: {user_id})")
        
        # Reset recovery tracking
        if plan_id in self.recovery_attempts:
            del self.recovery_attempts[plan_id]
        if plan_id in self.recovery_timeouts:
            del self.recovery_timeouts[plan_id]
        
        # Send reconnection notification
        await self.websocket_manager.send_message(
            plan_id,
            {
                "type": MessageType.CONNECTION_ESTABLISHED.value,
                "data": {
                    "plan_id": plan_id,
                    "user_id": user_id,
                    "status": "reconnected",
                    "message": "Connection successfully restored",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            },
            MessageType.CONNECTION_ESTABLISHED.value,
            priority=1
        )
    
    def should_allow_reconnection(self, plan_id: str) -> bool:
        """
        Check if reconnection should be allowed for a plan.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            True if reconnection is allowed, False otherwise
        """
        # Check attempt limit
        if self.recovery_attempts.get(plan_id, 0) >= self.max_recovery_attempts:
            logger.warning(f"❌ Max recovery attempts exceeded for plan {plan_id}")
            return False
        
        # Check timeout
        if plan_id in self.recovery_timeouts:
            if datetime.utcnow() > self.recovery_timeouts[plan_id]:
                logger.warning(f"❌ Recovery timeout exceeded for plan {plan_id}")
                return False
        
        return True
    
    def cleanup_expired_recovery_sessions(self) -> None:
        """Clean up expired recovery sessions."""
        now = datetime.utcnow()
        expired_plans = []
        
        for plan_id, timeout in self.recovery_timeouts.items():
            if now > timeout:
                expired_plans.append(plan_id)
        
        for plan_id in expired_plans:
            logger.info(f"🧹 Cleaning up expired recovery session for plan {plan_id}")
            if plan_id in self.recovery_attempts:
                del self.recovery_attempts[plan_id]
            del self.recovery_timeouts[plan_id]


class ConcurrentConnectionManager:
    """
    Manages concurrent WebSocket connections and prevents conflicts.
    """
    
    def __init__(self, websocket_manager: EnhancedWebSocketManager):
        self.websocket_manager = websocket_manager
        self.connection_locks: Dict[str, asyncio.Lock] = {}  # plan_id -> lock
        self.max_connections_per_plan = 5
        self.max_connections_per_user = 10
    
    async def acquire_connection_lock(self, plan_id: str) -> asyncio.Lock:
        """
        Acquire connection lock for a plan.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Asyncio lock for the plan
        """
        if plan_id not in self.connection_locks:
            self.connection_locks[plan_id] = asyncio.Lock()
        return self.connection_locks[plan_id]
    
    async def validate_new_connection(
        self,
        plan_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Validate if a new connection should be allowed.
        
        Args:
            plan_id: Plan identifier
            user_id: Optional user identifier
            
        Returns:
            True if connection is allowed, False otherwise
        """
        # Check plan connection limit
        current_plan_connections = self.websocket_manager.get_connection_count(plan_id)
        if current_plan_connections >= self.max_connections_per_plan:
            logger.warning(f"❌ Connection limit exceeded for plan {plan_id}: {current_plan_connections}/{self.max_connections_per_plan}")
            return False
        
        # Check user connection limit
        if user_id:
            user_connections = sum(
                1 for metadata in self.websocket_manager.connection_metadata.values()
                if metadata.user_id == user_id
            )
            if user_connections >= self.max_connections_per_user:
                logger.warning(f"❌ Connection limit exceeded for user {user_id}: {user_connections}/{self.max_connections_per_user}")
                return False
        
        return True
    
    async def handle_duplicate_connection(
        self,
        plan_id: str,
        user_id: Optional[str] = None,
        new_websocket: Any = None
    ) -> None:
        """
        Handle duplicate connection attempts.
        
        Args:
            plan_id: Plan identifier
            user_id: Optional user identifier
            new_websocket: New WebSocket connection
        """
        logger.info(f"🔄 Handling duplicate connection for plan {plan_id} (user: {user_id})")
        
        # Find existing connections for the same user and plan
        existing_connections = []
        for websocket, metadata in self.websocket_manager.connection_metadata.items():
            if metadata.plan_id == plan_id and metadata.user_id == user_id:
                existing_connections.append(websocket)
        
        if existing_connections:
            # Notify existing connections about the new connection
            for websocket in existing_connections:
                try:
                    await self.websocket_manager._send_to_connection(
                        websocket,
                        WebSocketMessage(
                            type=MessageType.SYSTEM_MESSAGE.value,
                            data={
                                "message": "New connection established for this session",
                                "plan_id": plan_id,
                                "user_id": user_id,
                                "connection_count": len(existing_connections) + 1,
                                "timestamp": datetime.utcnow().isoformat() + "Z"
                            }
                        )
                    )
                except Exception as e:
                    logger.error(f"Failed to notify existing connection: {e}")
    
    def cleanup_connection_locks(self) -> None:
        """Clean up unused connection locks."""
        active_plans = set(self.websocket_manager.get_connected_plans())
        locks_to_remove = []
        
        for plan_id in self.connection_locks:
            if plan_id not in active_plans:
                locks_to_remove.append(plan_id)
        
        for plan_id in locks_to_remove:
            del self.connection_locks[plan_id]


# Convenience functions for common WebSocket operations
async def send_workflow_started(plan_id: str, workflow_description: str) -> None:
    """Send workflow started notification."""
    manager = get_websocket_manager()
    await manager.send_message(
        plan_id,
        {
            "type": MessageType.WORKFLOW_STARTED.value,
            "data": {
                "plan_id": plan_id,
                "description": workflow_description,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        },
        MessageType.WORKFLOW_STARTED.value,
        priority=1
    )


async def send_workflow_completed(plan_id: str, success: bool, results: Optional[Dict[str, Any]] = None) -> None:
    """Send workflow completed notification."""
    manager = get_websocket_manager()
    await manager.send_message(
        plan_id,
        {
            "type": MessageType.WORKFLOW_COMPLETED.value,
            "data": {
                "plan_id": plan_id,
                "success": success,
                "results": results or {},
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        },
        MessageType.WORKFLOW_COMPLETED.value,
        priority=1
    )


async def send_agent_message(
    plan_id: str,
    agent_name: str,
    content: str,
    message_type: str = "agent_message",
    additional_data: Optional[Dict[str, Any]] = None
) -> None:
    """Send agent message with enhanced data."""
    manager = get_websocket_manager()
    
    data = {
        "plan_id": plan_id,
        "agent_name": agent_name,
        "content": content,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if additional_data:
        data.update(additional_data)
    
    await manager.send_message(
        plan_id,
        {
            "type": message_type,
            "data": data
        },
        message_type,
        priority=1
    )


async def send_comprehensive_results_ready(plan_id: str, comprehensive_results: Dict[str, Any]) -> None:
    """Send comprehensive results ready notification."""
    manager = get_websocket_manager()
    await manager.send_message(
        plan_id,
        {
            "type": "comprehensive_results_ready",
            "data": {
                "plan_id": plan_id,
                "comprehensive_results": comprehensive_results,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        },
        "comprehensive_results_ready",
        priority=1
    )