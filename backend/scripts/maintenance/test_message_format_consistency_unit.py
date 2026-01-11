#!/usr/bin/env python3
"""
Unit test for message format consistency between database and WebSocket.

This test verifies that:
1. Messages from MessagePersistenceService have consistent format
2. Message format matches the expected AgentMessage structure
3. All required fields are present and have correct types

Task 4.3: Ensure API response format consistency
Requirements: 3.4
"""
import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.models.message import AgentMessage
from app.services.message_persistence_service import get_message_persistence_service
from app.db.mongodb import MongoDB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageFormatConsistencyTest:
    """Unit test for message format consistency."""
    
    def __init__(self):
        self.test_results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "format_issues": []
        }
        self.test_plan_id = f"test-format-{int(datetime.utcnow().timestamp())}"
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all message format consistency tests."""
        logger.info("🧪 Starting message format consistency unit tests...")
        
        try:
            # Initialize database connection
            MongoDB.connect()
            
            # Test 1: AgentMessage model validation
            await self._test_agent_message_model()
            
            # Test 2: MessagePersistenceService format
            await self._test_message_persistence_service_format()
            
            # Test 3: Message serialization consistency
            await self._test_message_serialization_consistency()
            
            # Test 4: Required fields validation
            await self._test_required_fields_validation()
            
            # Test 5: Timestamp format consistency
            await self._test_timestamp_format_consistency()
            
            # Cleanup test data
            await self._cleanup_test_data()
            
        except Exception as e:
            logger.error(f"❌ Test suite failed with exception: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["format_issues"].append(f"Test suite exception: {str(e)}")
        
        # Generate summary
        self._generate_test_summary()
        return self.test_results
    
    async def _test_agent_message_model(self):
        """Test AgentMessage model structure and validation."""
        logger.info("🔍 Test 1: AgentMessage model validation")
        self.test_results["tests_run"] += 1
        
        try:
            # Create a test message
            message = AgentMessage(
                plan_id=self.test_plan_id,
                agent_name="TestAgent",
                agent_type="test",
                content="Test message content for format validation",
                timestamp=datetime.utcnow(),
                metadata={"test": True}
            )
            
            # Validate required fields exist
            required_fields = ["plan_id", "agent_name", "agent_type", "content", "timestamp", "metadata"]
            for field in required_fields:
                if not hasattr(message, field):
                    raise Exception(f"AgentMessage missing required field: {field}")
            
            # Validate field types
            if not isinstance(message.plan_id, str):
                raise Exception("plan_id must be string")
            if not isinstance(message.agent_name, str):
                raise Exception("agent_name must be string")
            if not isinstance(message.agent_type, str):
                raise Exception("agent_type must be string")
            if not isinstance(message.content, str):
                raise Exception("content must be string")
            if not isinstance(message.timestamp, datetime):
                raise Exception("timestamp must be datetime")
            if not isinstance(message.metadata, dict):
                raise Exception("metadata must be dict")
            
            # Test serialization to dict
            message_dict = message.dict()
            if not isinstance(message_dict, dict):
                raise Exception("AgentMessage.dict() must return dictionary")
            
            # Validate serialized structure
            for field in required_fields:
                if field not in message_dict:
                    raise Exception(f"Serialized message missing field: {field}")
            
            # Validate timestamp serialization
            if not isinstance(message_dict["timestamp"], (str, datetime)):
                raise Exception("Serialized timestamp must be string or datetime")
            
            logger.info("✅ AgentMessage model validation test passed")
            self.test_results["tests_passed"] += 1
            
        except Exception as e:
            logger.error(f"❌ AgentMessage model validation test failed: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["format_issues"].append(f"AgentMessage model: {str(e)}")
    
    async def _test_message_persistence_service_format(self):
        """Test MessagePersistenceService returns consistent format."""
        logger.info("🔍 Test 2: MessagePersistenceService format")
        self.test_results["tests_run"] += 1
        
        try:
            # Get service instance
            service = get_message_persistence_service()
            
            # Save a test message
            success = await service.save_agent_message(
                plan_id=self.test_plan_id,
                agent_name="FormatTestAgent",
                content="Test message for format consistency validation",
                agent_type="test",
                metadata={"format_test": True, "timestamp": datetime.utcnow().isoformat()}
            )
            
            if not success:
                raise Exception("Failed to save test message")
            
            # Retrieve messages
            messages = await service.get_messages_for_plan(self.test_plan_id)
            
            if not messages:
                raise Exception("No messages retrieved from service")
            
            # Validate each message format
            for i, message in enumerate(messages):
                if not isinstance(message, AgentMessage):
                    raise Exception(f"Message {i} is not AgentMessage instance")
                
                # Check required fields
                required_fields = ["plan_id", "agent_name", "agent_type", "content", "timestamp"]
                for field in required_fields:
                    if not hasattr(message, field):
                        raise Exception(f"Message {i} missing field: {field}")
                    
                    value = getattr(message, field)
                    if value is None:
                        raise Exception(f"Message {i} field {field} is None")
                
                # Validate field types
                if not isinstance(message.plan_id, str):
                    raise Exception(f"Message {i} plan_id must be string")
                if not isinstance(message.agent_name, str):
                    raise Exception(f"Message {i} agent_name must be string")
                if not isinstance(message.agent_type, str):
                    raise Exception(f"Message {i} agent_type must be string")
                if not isinstance(message.content, str):
                    raise Exception(f"Message {i} content must be string")
                if not isinstance(message.timestamp, datetime):
                    raise Exception(f"Message {i} timestamp must be datetime")
                
                # Validate plan_id consistency
                if message.plan_id != self.test_plan_id:
                    raise Exception(f"Message {i} has wrong plan_id: {message.plan_id}")
            
            logger.info(f"✅ MessagePersistenceService format test passed ({len(messages)} messages)")
            self.test_results["tests_passed"] += 1
            
        except Exception as e:
            logger.error(f"❌ MessagePersistenceService format test failed: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["format_issues"].append(f"Service format: {str(e)}")
    
    async def _test_message_serialization_consistency(self):
        """Test that message serialization is consistent."""
        logger.info("🔍 Test 3: Message serialization consistency")
        self.test_results["tests_run"] += 1
        
        try:
            # Create test message
            original_message = AgentMessage(
                plan_id=self.test_plan_id,
                agent_name="SerializationTestAgent",
                agent_type="test",
                content="Test message for serialization consistency",
                timestamp=datetime.utcnow(),
                metadata={"serialization_test": True}
            )
            
            # Test dict serialization
            message_dict = original_message.dict()
            
            # Validate dict structure
            expected_keys = {"plan_id", "agent_name", "agent_type", "content", "timestamp", "metadata"}
            actual_keys = set(message_dict.keys())
            
            if expected_keys != actual_keys:
                missing = expected_keys - actual_keys
                extra = actual_keys - expected_keys
                raise Exception(f"Dict serialization mismatch - Missing: {missing}, Extra: {extra}")
            
            # Test JSON serialization compatibility
            import json
            try:
                # Convert datetime to string for JSON compatibility
                json_dict = message_dict.copy()
                if isinstance(json_dict["timestamp"], datetime):
                    json_dict["timestamp"] = json_dict["timestamp"].isoformat()
                
                json_str = json.dumps(json_dict)
                parsed_dict = json.loads(json_str)
                
                # Validate JSON round-trip
                for key in expected_keys:
                    if key not in parsed_dict:
                        raise Exception(f"JSON round-trip lost field: {key}")
                
            except (TypeError, ValueError) as e:
                raise Exception(f"JSON serialization failed: {e}")
            
            # Test that serialized format matches expected API format
            api_format_fields = ["plan_id", "agent_name", "agent_type", "content", "timestamp"]
            for field in api_format_fields:
                if field not in message_dict:
                    raise Exception(f"API format missing field: {field}")
            
            logger.info("✅ Message serialization consistency test passed")
            self.test_results["tests_passed"] += 1
            
        except Exception as e:
            logger.error(f"❌ Message serialization consistency test failed: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["format_issues"].append(f"Serialization: {str(e)}")
    
    async def _test_required_fields_validation(self):
        """Test that all required fields are properly validated."""
        logger.info("🔍 Test 4: Required fields validation")
        self.test_results["tests_run"] += 1
        
        try:
            service = get_message_persistence_service()
            
            # Test with missing required fields
            test_cases = [
                {"plan_id": "", "agent_name": "Test", "content": "Test", "should_fail": True},
                {"plan_id": "test", "agent_name": "", "content": "Test", "should_fail": True},
                {"plan_id": "test", "agent_name": "Test", "content": "", "should_fail": True},
                {"plan_id": self.test_plan_id, "agent_name": "ValidAgent", "content": "Valid content", "should_fail": False},
            ]
            
            for i, test_case in enumerate(test_cases):
                should_fail = test_case.pop("should_fail")
                
                try:
                    success = await service.save_agent_message(**test_case)
                    
                    if should_fail and success:
                        raise Exception(f"Test case {i} should have failed but succeeded")
                    elif not should_fail and not success:
                        raise Exception(f"Test case {i} should have succeeded but failed")
                        
                except Exception as e:
                    if not should_fail:
                        raise Exception(f"Test case {i} failed unexpectedly: {e}")
            
            logger.info("✅ Required fields validation test passed")
            self.test_results["tests_passed"] += 1
            
        except Exception as e:
            logger.error(f"❌ Required fields validation test failed: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["format_issues"].append(f"Required fields: {str(e)}")
    
    async def _test_timestamp_format_consistency(self):
        """Test that timestamp formats are consistent."""
        logger.info("🔍 Test 5: Timestamp format consistency")
        self.test_results["tests_run"] += 1
        
        try:
            service = get_message_persistence_service()
            
            # Save message with current timestamp
            test_timestamp = datetime.utcnow()
            success = await service.save_agent_message(
                plan_id=self.test_plan_id,
                agent_name="TimestampTestAgent",
                content="Test message for timestamp consistency",
                agent_type="test"
            )
            
            if not success:
                raise Exception("Failed to save timestamp test message")
            
            # Retrieve and validate timestamp
            messages = await service.get_messages_for_plan(self.test_plan_id)
            timestamp_messages = [msg for msg in messages if msg.agent_name == "TimestampTestAgent"]
            
            if not timestamp_messages:
                raise Exception("Timestamp test message not found")
            
            message = timestamp_messages[0]
            
            # Validate timestamp type
            if not isinstance(message.timestamp, datetime):
                raise Exception(f"Timestamp must be datetime, got {type(message.timestamp)}")
            
            # Validate timestamp is reasonable (within last minute)
            time_diff = abs((datetime.utcnow() - message.timestamp).total_seconds())
            if time_diff > 60:
                raise Exception(f"Timestamp seems incorrect, {time_diff} seconds difference")
            
            # Test serialization format
            message_dict = message.dict()
            timestamp_value = message_dict["timestamp"]
            
            # Should be datetime or ISO string
            if isinstance(timestamp_value, str):
                try:
                    datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                except ValueError:
                    raise Exception(f"Invalid timestamp format: {timestamp_value}")
            elif not isinstance(timestamp_value, datetime):
                raise Exception(f"Timestamp must be datetime or ISO string, got {type(timestamp_value)}")
            
            logger.info("✅ Timestamp format consistency test passed")
            self.test_results["tests_passed"] += 1
            
        except Exception as e:
            logger.error(f"❌ Timestamp format consistency test failed: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["format_issues"].append(f"Timestamp format: {str(e)}")
    
    async def _cleanup_test_data(self):
        """Clean up test data."""
        try:
            service = get_message_persistence_service()
            await service.delete_messages_for_plan(self.test_plan_id)
            logger.info(f"🧹 Cleaned up test data for plan {self.test_plan_id}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to clean up test data: {e}")
    
    def _generate_test_summary(self):
        """Generate and log test summary."""
        results = self.test_results
        
        logger.info("📊 Message Format Consistency Test Summary")
        logger.info(f"   Tests Run: {results['tests_run']}")
        logger.info(f"   Tests Passed: {results['tests_passed']}")
        logger.info(f"   Tests Failed: {results['tests_failed']}")
        
        if results["tests_failed"] == 0:
            logger.info("✅ All message format consistency tests passed!")
        else:
            logger.error(f"❌ {results['tests_failed']} tests failed")
            
            if results["format_issues"]:
                logger.error("Format Issues:")
                for issue in results["format_issues"]:
                    logger.error(f"   - {issue}")
        
        # Calculate success rate
        if results["tests_run"] > 0:
            success_rate = (results["tests_passed"] / results["tests_run"]) * 100
            logger.info(f"📈 Success Rate: {success_rate:.1f}%")
        
        return results["tests_failed"] == 0


async def main():
    """Run the message format consistency tests."""
    print("🧪 Message Format Consistency Unit Test")
    print("=" * 50)
    
    tester = MessageFormatConsistencyTest()
    results = await tester.run_all_tests()
    
    print("\n" + "=" * 50)
    if results["tests_failed"] == 0:
        print("✅ All tests passed! Message format is consistent.")
        return 0
    else:
        print(f"❌ {results['tests_failed']} tests failed. See logs for details.")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))