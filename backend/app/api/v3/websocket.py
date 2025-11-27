"""WebSocket endpoint for real-time updates."""
import logging
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, Query

from app.services.websocket_service import websocket_manager

logger = logging.getLogger(__name__)


async def websocket_endpoint(websocket: WebSocket, plan_id: str, user_id: str = Query("default_user")):
    """
    WebSocket endpoint for real-time agent updates.
    
    Path: /api/v3/socket/{plan_id}?user_id={user_id}
    """
    await websocket_manager.connect(websocket, plan_id, user_id)
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "agent_message",
            "data": {
                "agent_name": "System",
                "content": f"Connected to plan {plan_id}",
                "status": "connected",
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        # Keep connection alive and listen for messages
        while True:
            # Receive messages from client
            data = await websocket.receive_json()
            
            # Handle different message types
            message_type = data.get("type")
            
            if message_type == "ping":
                # Respond to ping with pong
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif message_type == "plan_approval_response":
                # Handle plan approval (Phase 6)
                logger.info(f"Received plan approval response for plan {plan_id}")
                # Will be implemented in Phase 6
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, plan_id)
        logger.info(f"WebSocket disconnected for plan {plan_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error for plan {plan_id}: {e}")
        websocket_manager.disconnect(websocket, plan_id)
