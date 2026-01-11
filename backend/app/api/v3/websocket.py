"""WebSocket endpoint for real-time updates with enhanced features."""
import asyncio
import json
import logging
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, Query

from app.services.websocket_service import get_websocket_manager, MessageType

websocket_manager = get_websocket_manager()

logger = logging.getLogger(__name__)


async def websocket_endpoint(websocket: WebSocket, plan_id: str, user_id: str = Query("default_user")):
    """
    Enhanced WebSocket endpoint for real-time agent updates.
    
    Path: /api/v3/socket/{plan_id}?user_id={user_id}
    
    Features:
    - Enhanced connection management with state tracking
    - Message queuing for disconnected clients
    - Improved error handling and recovery
    - Heartbeat/ping-pong for connection health
    - Progress tracking with time estimates
    - Concurrent connection handling
    """
    try:
        await websocket.accept()
        
        # Connect with enhanced metadata and validation
        await websocket_manager.connect(
            websocket, 
            plan_id, 
            user_id,
            metadata={
                "client_info": websocket.headers.get("user-agent", "unknown"),
                "connection_time": datetime.utcnow().isoformat() + "Z",
                "client_ip": websocket.client.host if websocket.client else "unknown"
            }
        )
        
        # Keep connection alive and listen for messages
        while True:
            try:
                # Receive messages from client with timeout
                data = await asyncio.wait_for(websocket.receive_json(), timeout=60.0)
                
                # Handle different message types
                message_type = data.get("type")
                
                if message_type == MessageType.PING.value:
                    # Respond to ping with pong
                    await websocket.send_json({
                        "type": MessageType.PONG.value,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "server_time": datetime.utcnow().isoformat() + "Z"
                    })
                
                elif message_type == MessageType.PLAN_APPROVAL_RESPONSE.value:
                    # Handle plan approval via WebSocket
                    logger.info(f"Received plan approval response for plan {plan_id}")
                    
                    try:
                        approval_data = data.get("data", {})
                        approved = approval_data.get("approved", False)
                        feedback = approval_data.get("feedback", "")
                        
                        # Use new HITL interface for approval handling
                        from app.services.hitl_interface import HITLInterface
                        from app.services.langgraph_service import LangGraphService
                        
                        if approved:
                            # Plan approved - resume execution
                            updates = {
                                "plan_approved": True,
                                "hitl_feedback": feedback or "Plan approved via WebSocket"
                            }
                            
                            # Resume execution
                            result = await LangGraphService.resume_execution(plan_id, updates)
                            
                            # Send confirmation
                            await websocket.send_json({
                                "type": "approval_processed",
                                "data": {
                                    "status": "approved",
                                    "message": "Plan approved, execution resumed",
                                    "timestamp": datetime.utcnow().isoformat() + "Z"
                                }
                            })
                        else:
                            # Plan rejected
                            from app.db.repositories import PlanRepository
                            await PlanRepository.update_status(plan_id, "rejected")
                            
                            await websocket.send_json({
                                "type": "approval_processed",
                                "data": {
                                    "status": "rejected",
                                    "message": f"Plan rejected. {feedback}",
                                    "timestamp": datetime.utcnow().isoformat() + "Z"
                                }
                            })
                            
                    except Exception as e:
                        logger.error(f"Plan approval processing failed: {e}")
                        await websocket_manager.send_error_notification(
                            plan_id,
                            "approval_processing_error",
                            f"Approval processing failed: {str(e)}",
                            recoverable=True
                        )
                
                elif message_type == MessageType.USER_CLARIFICATION_RESPONSE.value:
                    # Handle user clarification via WebSocket
                    logger.info(f"Received user clarification response for plan {plan_id}")
                    
                    try:
                        clarification_data = data.get("data", {})
                        answer = clarification_data.get("answer", "")
                        request_id = clarification_data.get("request_id", "")
                        
                        # Determine if this is approval or revision
                        is_approval = answer.strip().upper() in ["OK", "YES", "APPROVE", "APPROVED"]
                        
                        from app.services.langgraph_service import LangGraphService
                        
                        if is_approval:
                            # User approved - complete task
                            updates = {
                                "result_approved": True,
                                "hitl_feedback": answer,
                                "awaiting_user_input": False
                            }
                        else:
                            # User provided revision
                            updates = {
                                "result_approved": False,
                                "hitl_feedback": answer,
                                "awaiting_user_input": False,
                                "task_description": answer  # Use revision as new task
                            }
                        
                        # Resume execution with updates
                        result = await LangGraphService.resume_execution(plan_id, updates)
                        
                        # Send confirmation
                        await websocket.send_json({
                            "type": "clarification_processed",
                            "data": {
                                "status": "approved" if is_approval else "revision",
                                "message": "Clarification processed, execution resumed",
                                "timestamp": datetime.utcnow().isoformat() + "Z"
                            }
                        })
                        
                    except Exception as e:
                        logger.error(f"Clarification processing failed: {e}")
                        await websocket_manager.send_error_notification(
                            plan_id,
                            "clarification_processing_error",
                            f"Clarification processing failed: {str(e)}",
                            recoverable=True
                        )
                
                elif message_type == "connection_check":
                    # Handle connection health check
                    stats = websocket_manager.get_connection_stats()
                    await websocket.send_json({
                        "type": "connection_status",
                        "data": {
                            "plan_id": plan_id,
                            "user_id": user_id,
                            "connected": True,
                            "connection_count": websocket_manager.get_connection_count(plan_id),
                            "queued_messages": websocket_manager.get_queued_message_count(plan_id),
                            "server_stats": stats,
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                    })
                
                else:
                    logger.warning(f"Unknown WebSocket message type: {message_type}")
                    await websocket.send_json({
                        "type": MessageType.ERROR_NOTIFICATION.value,
                        "data": {
                            "error_type": "unknown_message_type",
                            "error_message": f"Unknown message type: {message_type}",
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                    })
            
            except asyncio.TimeoutError:
                # Send heartbeat on timeout
                await websocket.send_json({
                    "type": MessageType.PING.value,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                })
            
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received from WebSocket: {e}")
                await websocket.send_json({
                    "type": MessageType.ERROR_NOTIFICATION.value,
                    "data": {
                        "error_type": "invalid_json",
                        "error_message": "Invalid JSON format in message",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                })
    
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected for plan {plan_id} (user: {user_id})")
    
    except ConnectionError as e:
        logger.error(f"WebSocket connection error for plan {plan_id}: {e}")
        await websocket_manager.handle_connection_error(websocket, e, plan_id)
        # Send error response if websocket is still open
        try:
            await websocket.send_json({
                "type": MessageType.CONNECTION_ERROR.value,
                "data": {
                    "error_type": "connection_limit",
                    "error_message": str(e),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            })
            await websocket.close(code=1008, reason=str(e))
        except:
            pass  # Connection already closed
    
    except Exception as e:
        logger.error(f"Unexpected WebSocket error for plan {plan_id}: {e}")
        await websocket_manager.handle_connection_error(websocket, e, plan_id)
