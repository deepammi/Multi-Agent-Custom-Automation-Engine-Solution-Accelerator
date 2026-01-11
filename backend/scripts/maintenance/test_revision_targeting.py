#!/usr/bin/env python3
"""
Test script for revision targeting service functionality.
Task 8: Verify intelligent revision parsing and agent-specific routing.
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.revision_targeting_service import get_revision_targeting_service, RevisionType, RevisionScope


async def test_revision_parsing():
    """Test revision feedback parsing with various scenarios."""
    print("🧪 Testing Revision Targeting Service")
    print("=" * 50)
    
    service = get_revision_targeting_service()
    
    # Test scenarios
    test_cases = [
        {
            "name": "Simple Approval",
            "feedback": "OK looks good",
            "expected_type": RevisionType.APPROVAL
        },
        {
            "name": "Simple Rejection", 
            "feedback": "No this is wrong, start over",
            "expected_type": RevisionType.REJECTION
        },
        {
            "name": "Invoice-Specific Issue",
            "feedback": "The invoice amount is wrong, please fix the billing calculation",
            "expected_type": RevisionType.DATA_CORRECTION
        },
        {
            "name": "Email-Specific Issue",
            "feedback": "Wrong email found, search for messages from last week instead",
            "expected_type": RevisionType.PARAMETER_ADJUSTMENT
        },
        {
            "name": "Analysis Issue",
            "feedback": "The analysis is incomplete, missing correlation between systems",
            "expected_type": RevisionType.SPECIFIC_AGENTS
        },
        {
            "name": "Multiple Agent Issue",
            "feedback": "Both the CRM data and invoice amounts are incorrect",
            "expected_type": RevisionType.SPECIFIC_AGENTS
        }
    ]
    
    # Mock data
    current_results = {
        "gmail": {"emails": ["email1", "email2"]},
        "invoice": {"amount": 1000, "vendor": "ACME Corp"},
        "salesforce": {"account": "University of Chicago"},
        "analysis": {"summary": "Test analysis"}
    }
    agent_sequence = ["gmail", "invoice", "salesforce", "analysis"]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   Feedback: '{test_case['feedback']}'")
        
        try:
            instruction = await service.parse_revision_feedback(
                plan_id=f"test-{i}",
                feedback=test_case['feedback'],
                current_results=current_results,
                agent_sequence=agent_sequence
            )
            
            print(f"   ✅ Parsed Type: {instruction.revision_type.value}")
            print(f"   📊 Confidence: {instruction.confidence_score:.2f}")
            print(f"   🎯 Scope: {instruction.revision_scope.value}")
            print(f"   🔧 Targets: {len(instruction.targets)}")
            
            if instruction.targets:
                for target in instruction.targets:
                    print(f"      - {target.agent_name}: {target.revision_reason}")
            
            print(f"   💾 Preserve: {instruction.preserve_results}")
            print(f"   🔄 Re-run: {instruction.rerun_agents}")
            
            # Check if expected type matches
            if instruction.revision_type == test_case['expected_type']:
                print(f"   ✅ Expected type matched!")
            else:
                print(f"   ⚠️  Expected {test_case['expected_type'].value}, got {instruction.revision_type.value}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test revision statistics
    print(f"\n📈 Revision Statistics:")
    stats = service.get_revision_stats()
    print(f"   Total revisions: {stats['total_revisions']}")
    print(f"   Plans with revisions: {stats['plans_with_revisions']}")
    print(f"   Average iterations: {stats['average_iterations']:.1f}")
    print(f"   Revision types: {stats['revision_types']}")
    print(f"   Average confidence: {stats['average_confidence']:.2f}")
    
    print(f"\n✅ Revision targeting service test completed!")


if __name__ == "__main__":
    asyncio.run(test_revision_parsing())