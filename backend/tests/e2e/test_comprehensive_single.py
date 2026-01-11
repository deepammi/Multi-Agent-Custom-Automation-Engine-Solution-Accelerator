#!/usr/bin/env python3
"""
Single Comprehensive Test - Run only the first test for debugging.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_comprehensive_workflow_integration import ComprehensiveWorkflowTester


async def main():
    """Run single comprehensive test."""
    print("🚀 Running Single Comprehensive Test (First Test Only)")
    print("=" * 80)
    
    tester = ComprehensiveWorkflowTester()
    
    try:
        # Setup test environment
        setup_success = await tester.setup_test_environment()
        if not setup_success:
            print("❌ Failed to setup test environment")
            return False
        
        # Run only the first test scenario
        first_scenario = tester.test_scenarios[0]
        print(f"\n🔥 Running Test: {first_scenario.name}")
        
        result = await tester.run_comprehensive_workflow_test(first_scenario)
        
        # Show results
        print(f"\n{'🎉' * 20} TEST RESULTS {'🎉' * 20}")
        print(f"Status: {result['status']}")
        print(f"Duration: {result.get('total_duration', 0):.2f}s")
        
        if result.get('errors'):
            print(f"Errors: {result['errors']}")
        
        success = result['status'] in ['success', 'partial_success']
        print(f"Result: {'✅ PASSED' if success else '❌ FAILED'}")
        
        return success
        
    except Exception as e:
        print(f"💥 Test crashed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        await tester.cleanup()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)