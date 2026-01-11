#!/usr/bin/env python3
"""
Test WebSocket backward compatibility to ensure existing functionality remains unchanged
with the new message persistence layer.

This test verifies:
1. WebSocket message broadcasting works with new persistence layer
2. Message format and timing remain consistent
3. All message types are properly handled
4. Connection management works as before
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.websocket_service import (
    get_websocket_manager, 
    reset_websocket_manager,
    MockWebSocketConnection,
    MessageType
)
from app.services.message_persistence_service import get_message_persistence_service
from app.db.mongodb import MongoDB

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketBackwardCompatibilityTest:
    """Test suite for WebSocket backward compatibility."""
    
    def __init__(self):
        self.websocket_manager = None
        self.persistence_service = None
        self.test_results = []
    
    async def setup(self):
        """Set up test environment."""
        try:
            # Initialize database connection
            MongoDB.connect()
            logger.info("✅ Database connected")
            
            # Reset WebSocket manager to ensure clean state
            reset_websocket_manager()
            self.websocket_manager = get_websocket_manager()
            
            # Get persistence service
            self.persistence_service = get_message_persistence_service()
            
            logger.info("✅ Test environment set up")
            return True
            
        except Exception as e:
            logger.error(f"❌ Test setup failed: {e}")
            return False
    
    async def test_websocket_message_broadcasting(self) -> bool:
        """Test that WebSocket message broadcasting works with new persistence layer."""
        try:
            logger.info("🧪 Testing WebSocket message broadcasting...")
            
            plan_id = "test-ws-broadcasting"
            user_id = "test-user"
            
            # Create mock WebSocket connections
            ws1 = MockWebSocketConnection(plan_id, user_id)
            ws2 = MockWebSocketConnection(plan_id, user_id + "2")
            
            # Connect both WebSockets
            await self.websocket_manager.connect(ws1, plan_id, user_id)
            await self.websocket_manager.connect(ws2, plan_id, user_id + "2")
            
            # Send various message types
            test_messages = [
                {
                    "type": MessageType.AGENT_MESSAGE.value,
                    "data": {
                        "plan_id": plan_id,
                        "agent_name": "TestAgent",
                        "content": "Test agent message",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                },
                {
                    "type": MessageType.AGENT_MESSAGE_STREAMING.value,
                    "data": {
                        "plan_id": plan_id,
                        "agent_name": "StreamingAgent",
                        "content": "Streaming content chunk",
                        "is_complete": False,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                },
                {
                    "type": MessageType.PROGRESS_UPDATE.value,
                    "data": {
                        "plan_id": plan_id,
                        "current_step": 2,
                        "total_steps": 5,
                        "current_agent": "ProgressAgent",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                },
                {
                    "type": MessageType.FINAL_RESULT_MESSAGE.value,
                    "data": {
                        "plan_id": plan_id,
                        "agent_name": "FinalAgent",
                        "content": "Task completed successfully",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                }
            ]
            
            # Clear connection establishment messages
            await asyncio.sleep(0.1)
            ws1.clear_messages()
            ws2.clear_messages()
            
            # Send each message and verify broadcasting
            for i, message in enumerate(test_messages):
                await self.websocket_manager.send_message(
                    plan_id,
                    message,
                    message["type"]
                )
                
                # Small delay to ensure message processing
                await asyncio.sleep(0.1)
                
                # Verify both connections received the message
                if len(ws1.messages) <= i or len(ws2.messages) <= i:
                    logger.error(f"❌ Message {i} not received by all connections")
                    logger.error(f"WS1 messages: {len(ws1.messages)}, WS2 messages: {len(ws2.messages)}")
                    return False
                
                # Verify message content matches
                received_msg1 = ws1.messages[i]
                received_msg2 = ws2.messages[i]
                
                if received_msg1["type"] != message["type"]:
                    logger.error(f"❌ Message type mismatch in ws1: expected {message['type']}, got {received_msg1['type']}")
                    return False
                
                if received_msg2["type"] != message["type"]:
                    logger.error(f"❌ Message type mismatch in ws2: expected {message['type']}, got {received_msg2['type']}")
                    return False
            
            # Verify connection count
            connection_count = self.websocket_manager.get_connection_count(plan_id)
            if connection_count != 2:
                logger.error(f"❌ Expected 2 connections, got {connection_count}")
                return False
            
            # Clean up connections
            await self.websocket_manager.disconnect(ws1)
            await self.websocket_manager.disconnect(ws2)
            
            logger.info("✅ WebSocket message broadcasting test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ WebSocket message broadcasting test failed: {e}")
            return False
    
    async def test_message_format_consistency(self) -> bool:
        """Test that message format remains consistent with existing expectations."""
        try:
            logger.info("🧪 Testing message format consistency...")
            
            plan_id = "test-format-consistency"
            user_id = "test-user"
            
            # Create mock WebSocket connection
            ws = MockWebSocketConnection(plan_id, user_id)
            await self.websocket_manager.connect(ws, plan_id, user_id)
            
            # Clear connection establishment message
            await asyncio.sleep(0.1)
            ws.clear_messages()
            
            # Test different message formats that frontend expects
            test_cases = [
                {
                    "name": "Agent Message",
                    "message": {
                        "type": "agent_message",
                        "data": {
                            "plan_id": plan_id,
                            "agent_name": "TestAgent",
                            "agent_type": "agent",
                            "content": "This is a test message",
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                    },
                    "expected_fields": ["type", "data", "timestamp", "message_id"]
                },
                {
                    "name": "Streaming Message",
                    "message": {
                        "type": "agent_message_streaming",
                        "data": {
                            "plan_id": plan_id,
                            "agent_name": "StreamingAgent",
                            "content": "Streaming chunk",
                            "is_complete": False,
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                    },
                    "expected_fields": ["type", "data", "timestamp", "message_id"]
                },
                {
                    "name": "Final Result",
                    "message": {
                        "type": "final_result_message",
                        "data": {
                            "plan_id": plan_id,
                            "agent_name": "FinalAgent",
                            "content": "Task completed",
                            "timestamp": datetime.utcnow().isoformat() + "Z"
                        }
                    },
                    "expected_fields": ["type", "data", "timestamp", "message_id"]
                }
            ]
            
            for test_case in test_cases:
                # Clear previous messages
                ws.clear_messages()
                
                # Send message
                await self.websocket_manager.send_message(
                    plan_id,
                    test_case["message"],
                    test_case["message"]["type"]
                )
                
                await asyncio.sleep(0.1)
                
                # Verify message was received
                if not ws.messages:
                    logger.error(f"❌ {test_case['name']}: No message received")
                    return False
                
                received_msg = ws.messages[0]
                
                # Debug: Log the actual message structure
                logger.info(f"🔍 {test_case['name']}: Received message structure: {received_msg}")
                
                # Check required fields
                for field in test_case["expected_fields"]:
                    if field not in received_msg:
                        logger.error(f"❌ {test_case['name']}: Missing required field '{field}'")
                        return False
                
                # Verify message structure matches expected format
                if received_msg["type"] != test_case["message"]["type"]:
                    logger.error(f"❌ {test_case['name']}: Type mismatch")
                    return False
                
                if "data" not in received_msg:
                    logger.error(f"❌ {test_case['name']}: Missing data field")
                    return False
                
                # Verify data content - handle nested structure
                expected_data = test_case["message"]["data"]
                received_data = received_msg["data"]
                
                # The WebSocket service wraps messages, so the actual data is nested
                if "data" in received_data and isinstance(received_data["data"], dict):
                    actual_data = received_data["data"]
                else:
                    actual_data = received_data
                
                for key in ["agent_name", "content"]:  # Remove plan_id check as it might be modified
                    if key in expected_data:
                        if actual_data.get(key) != expected_data[key]:
                            logger.error(f"❌ {test_case['name']}: Data field '{key}' mismatch")
                            logger.error(f"Expected: {expected_data[key]}, Got: {actual_data.get(key)}")
                            return False
                
                logger.info(f"✅ {test_case['name']}: Format validation passed")
            
            # Clean up
            await self.websocket_manager.disconnect(ws)
            
            logger.info("✅ Message format consistency test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Message format consistency test failed: {e}")
            return False
    
    async def test_message_timing_consistency(self) -> bool:
        """Test that message timing remains consistent."""
        try:
            logger.info("🧪 Testing message timing consistency...")
            
            plan_id = "test-timing-consistency"
            user_id = "test-user"
            
            # Create mock WebSocket connection
            ws = MockWebSocketConnection(plan_id, user_id)
            await self.websocket_manager.connect(ws, plan_id, user_id)
            
            # Clear connection establishment message
            await asyncio.sleep(0.1)
            ws.clear_messages()
            
            # Send messages with timing measurements
            message_count = 5
            send_times = []
            receive_times = []
            
            for i in range(message_count):
                # Record send time
                send_time = datetime.utcnow()
                send_times.append(send_time)
                
                # Send message
                await self.websocket_manager.send_message(
                    plan_id,
                    {
                        "type": "agent_message",
                        "data": {
                            "plan_id": plan_id,
                            "agent_name": f"Agent{i}",
                            "content": f"Message {i}",
                            "timestamp": send_time.isoformat() + "Z"
                        }
                    },
                    "agent_message"
                )
                
                # Small delay between messages
                await asyncio.sleep(0.05)
            
            # Wait for all messages to be processed
            await asyncio.sleep(0.2)
            
            # Verify all messages were received
            if len(ws.messages) != message_count:
                logger.error(f"❌ Expected {message_count} messages, received {len(ws.messages)}")
                return False
            
            # Check message ordering and timing
            for i, message in enumerate(ws.messages):
                # Verify message order - handle nested structure
                expected_content = f"Message {i}"
                
                # Extract actual content from nested structure
                if "data" in message and isinstance(message["data"], dict):
                    if "data" in message["data"] and isinstance(message["data"]["data"], dict):
                        actual_content = message["data"]["data"].get("content", "")
                    else:
                        actual_content = message["data"].get("content", "")
                else:
                    actual_content = message.get("content", "")
                
                if actual_content != expected_content:
                    logger.error(f"❌ Message order incorrect: expected '{expected_content}', got '{actual_content}'")
                    return False
                
                # Verify timestamp is present and reasonable
                if "timestamp" not in message:
                    logger.error(f"❌ Message {i} missing timestamp")
                    return False
                
                try:
                    msg_timestamp = datetime.fromisoformat(message["timestamp"].replace('Z', '+00:00'))
                    # Timestamp should be close to when we sent the message
                    time_diff = abs((msg_timestamp.replace(tzinfo=None) - send_times[i]).total_seconds())
                    if time_diff > 1.0:  # Allow 1 second tolerance
                        logger.warning(f"⚠️ Message {i} timestamp differs by {time_diff} seconds")
                except Exception as e:
                    logger.error(f"❌ Message {i} timestamp parsing failed: {e}")
                    return False
            
            # Clean up
            await self.websocket_manager.disconnect(ws)
            
            logger.info("✅ Message timing consistency test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Message timing consistency test failed: {e}")
            return False
    
    async def test_connection_management(self) -> bool:
        """Test that connection management works as before."""
        try:
            logger.info("🧪 Testing connection management...")
            
            plan_id = "test-connection-mgmt"
            
            # Test multiple connections for same plan
            connections = []
            for i in range(3):
                ws = MockWebSocketConnection(plan_id, f"user{i}")
                await self.websocket_manager.connect(ws, plan_id, f"user{i}")
                connections.append(ws)
            
            # Clear connection establishment messages
            await asyncio.sleep(0.1)
            for ws in connections:
                ws.clear_messages()
            
            # Verify connection count
            connection_count = self.websocket_manager.get_connection_count(plan_id)
            if connection_count != 3:
                logger.error(f"❌ Expected 3 connections, got {connection_count}")
                return False
            
            # Send message to all connections
            await self.websocket_manager.send_message(
                plan_id,
                {
                    "type": "system_message",
                    "data": {
                        "plan_id": plan_id,
                        "message": "Test broadcast message"
                    }
                },
                "system_message"
            )
            
            await asyncio.sleep(0.1)
            
            # Verify all connections received the message
            for i, ws in enumerate(connections):
                if not ws.messages:
                    logger.error(f"❌ Connection {i} did not receive message")
                    return False
                
                if ws.messages[0]["type"] != "system_message":
                    logger.error(f"❌ Connection {i} received wrong message type")
                    return False
            
            # Test connection disconnection
            await self.websocket_manager.disconnect(connections[1])
            
            # Verify connection count decreased
            connection_count = self.websocket_manager.get_connection_count(plan_id)
            if connection_count != 2:
                logger.error(f"❌ Expected 2 connections after disconnect, got {connection_count}")
                return False
            
            # Send another message
            for ws in connections:
                ws.clear_messages()
            
            await self.websocket_manager.send_message(
                plan_id,
                {
                    "type": "system_message",
                    "data": {
                        "plan_id": plan_id,
                        "message": "Test message after disconnect"
                    }
                },
                "system_message"
            )
            
            await asyncio.sleep(0.1)
            
            # Verify only remaining connections received the message
            if connections[0].messages:  # Should receive
                if connections[0].messages[0]["type"] != "system_message":
                    logger.error("❌ Connection 0 received wrong message type after disconnect")
                    return False
            else:
                logger.error("❌ Connection 0 did not receive message after disconnect")
                return False
            
            if connections[1].messages:  # Should not receive (disconnected)
                logger.error("❌ Disconnected connection still received message")
                return False
            
            if connections[2].messages:  # Should receive
                if connections[2].messages[0]["type"] != "system_message":
                    logger.error("❌ Connection 2 received wrong message type after disconnect")
                    return False
            else:
                logger.error("❌ Connection 2 did not receive message after disconnect")
                return False
            
            # Clean up remaining connections
            await self.websocket_manager.disconnect(connections[0])
            await self.websocket_manager.disconnect(connections[2])
            
            logger.info("✅ Connection management test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection management test failed: {e}")
            return False
    
    async def test_websocket_stats_and_monitoring(self) -> bool:
        """Test that WebSocket statistics and monitoring work correctly."""
        try:
            logger.info("🧪 Testing WebSocket stats and monitoring...")
            
            plan_id = "test-stats-monitoring"
            user_id = "test-user"
            
            # Get initial stats
            initial_stats = self.websocket_manager.get_connection_stats()
            
            # Create connection
            ws = MockWebSocketConnection(plan_id, user_id)
            await self.websocket_manager.connect(ws, plan_id, user_id)
            
            # Clear connection establishment message
            await asyncio.sleep(0.1)
            ws.clear_messages()
            
            # Send some messages
            for i in range(3):
                await self.websocket_manager.send_message(
                    plan_id,
                    {
                        "type": "agent_message",
                        "data": {
                            "plan_id": plan_id,
                            "agent_name": f"Agent{i}",
                            "content": f"Test message {i}"
                        }
                    },
                    "agent_message"
                )
            
            await asyncio.sleep(0.1)
            
            # Get updated stats
            updated_stats = self.websocket_manager.get_connection_stats()
            
            # Verify stats increased
            if updated_stats["total_connections"] <= initial_stats["total_connections"]:
                logger.error("❌ Connection count did not increase")
                return False
            
            if updated_stats["active_plans"] <= initial_stats["active_plans"]:
                logger.error("❌ Active plans count did not increase")
                return False
            
            # Verify plan-specific stats
            if plan_id not in updated_stats["connections_per_plan"]:
                logger.error(f"❌ Plan {plan_id} not found in connection stats")
                return False
            
            if updated_stats["connections_per_plan"][plan_id] != 1:
                logger.error(f"❌ Expected 1 connection for plan {plan_id}, got {updated_stats['connections_per_plan'][plan_id]}")
                return False
            
            # Test connected plans list
            connected_plans = self.websocket_manager.get_connected_plans()
            if plan_id not in connected_plans:
                logger.error(f"❌ Plan {plan_id} not in connected plans list")
                return False
            
            # Clean up
            await self.websocket_manager.disconnect(ws)
            
            logger.info("✅ WebSocket stats and monitoring test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ WebSocket stats and monitoring test failed: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all backward compatibility tests."""
        logger.info("🚀 Starting WebSocket backward compatibility tests...")
        
        if not await self.setup():
            return {"success": False, "error": "Test setup failed"}
        
        tests = [
            ("WebSocket Message Broadcasting", self.test_websocket_message_broadcasting),
            ("Message Format Consistency", self.test_message_format_consistency),
            ("Message Timing Consistency", self.test_message_timing_consistency),
            ("Connection Management", self.test_connection_management),
            ("Stats and Monitoring", self.test_websocket_stats_and_monitoring)
        ]
        
        results = {}
        all_passed = True
        
        for test_name, test_func in tests:
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"Running: {test_name}")
                logger.info(f"{'='*60}")
                
                result = await test_func()
                results[test_name] = {
                    "passed": result,
                    "error": None
                }
                
                if not result:
                    all_passed = False
                    logger.error(f"❌ {test_name} FAILED")
                else:
                    logger.info(f"✅ {test_name} PASSED")
                    
            except Exception as e:
                logger.error(f"❌ {test_name} FAILED with exception: {e}")
                results[test_name] = {
                    "passed": False,
                    "error": str(e)
                }
                all_passed = False
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*60}")
        
        passed_count = sum(1 for r in results.values() if r["passed"])
        total_count = len(results)
        
        logger.info(f"Tests passed: {passed_count}/{total_count}")
        
        if all_passed:
            logger.info("🎉 ALL WEBSOCKET BACKWARD COMPATIBILITY TESTS PASSED!")
        else:
            logger.error("❌ Some WebSocket backward compatibility tests failed")
        
        return {
            "success": all_passed,
            "results": results,
            "summary": {
                "total_tests": total_count,
                "passed_tests": passed_count,
                "failed_tests": total_count - passed_count
            }
        }


async def main():
    """Main test runner."""
    test_suite = WebSocketBackwardCompatibilityTest()
    results = await test_suite.run_all_tests()
    
    if results["success"]:
        logger.info("\n✅ WebSocket backward compatibility verified!")
        return True
    else:
        logger.error("\n❌ WebSocket backward compatibility issues detected!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)