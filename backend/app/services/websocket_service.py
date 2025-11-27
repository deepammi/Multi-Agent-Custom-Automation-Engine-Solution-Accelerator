"""WebSocket connection management service."""
import logging
from typing import Dict, Set, List
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        # Store active connections: {plan_id: {websocket1, websocket2, ...}}
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Buffer messages for plans without active connections
        self.message_buffer: Dict[str, List[dict]] = {}
    
    async def connect(self, websocket: WebSocket, plan_id: str, user_id: str):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        
        if plan_id not in self.active_connections:
            self.active_connections[plan_id] = set()
        
        self.active_connections[plan_id].add(websocket)
        logger.info(f"WebSocket connected for plan {plan_id}, user {user_id}")
        logger.info(f"Active connections for plan {plan_id}: {len(self.active_connections[plan_id])}")
        
        # Send any buffered messages
        if plan_id in self.message_buffer:
            logger.info(f"Sending {len(self.message_buffer[plan_id])} buffered messages for plan {plan_id}")
            for message in self.message_buffer[plan_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending buffered message: {e}")
            # Clear buffer after sending
            del self.message_buffer[plan_id]
    
    def disconnect(self, websocket: WebSocket, plan_id: str):
        """Remove a WebSocket connection."""
        if plan_id in self.active_connections:
            self.active_connections[plan_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[plan_id]:
                del self.active_connections[plan_id]
            
            logger.info(f"WebSocket disconnected for plan {plan_id}")
    
    async def send_message(self, plan_id: str, message: dict):
        """Send a message to all connections for a specific plan."""
        msg_type = message.get("type", "unknown")
        logger.info(f"📨 send_message called: plan_id={plan_id}, type={msg_type}")
        
        if plan_id not in self.active_connections or not self.active_connections[plan_id]:
            # No active connections - buffer the message
            logger.warning(f"⚠️ No active connections for plan {plan_id}, buffering {msg_type} message")
            logger.warning(f"⚠️ Active connections: {list(self.active_connections.keys())}")
            if plan_id not in self.message_buffer:
                self.message_buffer[plan_id] = []
            self.message_buffer[plan_id].append(message)
            logger.warning(f"⚠️ Buffered {len(self.message_buffer[plan_id])} messages for plan {plan_id}")
            return
        
        logger.info(f"✅ Sending {msg_type} to {len(self.active_connections[plan_id])} connection(s)")
        disconnected = set()
        
        for connection in self.active_connections[plan_id]:
            try:
                await connection.send_json(message)
                logger.info(f"✅ Sent {msg_type} successfully")
            except Exception as e:
                logger.error(f"❌ Error sending message: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection, plan_id)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all active connections."""
        for plan_id in list(self.active_connections.keys()):
            await self.send_message(plan_id, message)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
