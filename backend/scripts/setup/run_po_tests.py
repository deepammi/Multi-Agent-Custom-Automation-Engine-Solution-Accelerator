#!/usr/bin/env python3
"""
Simple test runner for PO Workflow End-to-End tests.
Run this script to see the complete workflow execution with detailed logging.
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_po_workflow_e2e import (
    run_mock_po_test,
    run_real_po_test, 
    run_detailed_analysis,
    run_error_scenarios
)


async def main():
    """Main test runner with interactive menu."""
    
    print("🚀 PO Workflow Test Runner")
    print("="*50)
    print("This will demonstrate the new LangGraph orchestrator")
    print("with detailed step-by-step execution logging.")
    print()
    
    while True:
        print("Available Tests:")
        print("1. Mock AI Test - Shows complete flow with predictable responses")
        print("2. Real AI Test - Uses actual LLM service (requires configuration)")
        print("3. Detailed Analysis - Step-by-step workflow breakdown")
        print("4. Error Scenarios - Error handling and recovery testing")
        print("5. Run All Tests")
        print("6. Exit")
        print()
        
        choice = input("Select test to run (1-6): ").strip()
        
        if choice == "1":
            print("\n" + "="*60)
            print("🧪 MOCK AI TEST")
            print("="*60)
            print("This test uses mock AI responses to show the complete")
            print("workflow execution with predictable, detailed results.")
            print()
            
            try:
                result = await run_mock_po_test()
                print(f"\n✅ Mock test completed successfully!")
                print(f"   Final status: {result.get('status', 'unknown')}")
                
            except Exception as e:
                print(f"\n❌ Mock test failed: {e}")
        
        elif choice == "2":
            print("\n" + "="*60)
            print("🌐 REAL AI TEST")
            print("="*60)
            print("This test uses the actual LLM service to generate")
            print("real AI responses. Requires proper API configuration.")
            print()
            
            try:
                result = await run_real_po_test()
                print(f"\n✅ Real AI test completed!")
                print(f"   Final status: {result.get('status', 'unknown')}")
                
            except Exception as e:
                print(f"\n⚠️  Real AI test skipped: {e}")
                print("   This is expected if LLM service is not configured.")
        
        elif choice == "3":
            print("\n" + "="*60)
            print("🔬 DETAILED ANALYSIS")
            print("="*60)
            print("This shows a comprehensive step-by-step breakdown")
            print("of how the workflow executes each phase.")
            print()
            
            try:
                result = await run_detailed_analysis()
                print(f"\n✅ Detailed analysis completed!")
                print(f"   Agents analyzed: {len(result['sequence'].agents)}")
                
            except Exception as e:
                print(f"\n❌ Analysis failed: {e}")
        
        elif choice == "4":
            print("\n" + "="*60)
            print("⚠️  ERROR SCENARIOS")
            print("="*60)
            print("This tests various error conditions and recovery")
            print("mechanisms in the workflow system.")
            print()
            
            try:
                result = await run_error_scenarios()
                print(f"\n✅ Error scenario testing completed!")
                print(f"   Scenarios tested: {len(result)}")
                
            except Exception as e:
                print(f"\n❌ Error scenario testing failed: {e}")
        
        elif choice == "5":
            print("\n" + "="*60)
            print("🎯 RUNNING ALL TESTS")
            print("="*60)
            
            tests = [
                ("Mock AI Test", run_mock_po_test),
                ("Detailed Analysis", run_detailed_analysis),
                ("Error Scenarios", run_error_scenarios),
                ("Real AI Test", run_real_po_test)
            ]
            
            results = {}
            
            for test_name, test_func in tests:
                print(f"\n🔄 Running {test_name}...")
                try:
                    result = await test_func()
                    results[test_name] = {"status": "success", "result": result}
                    print(f"✅ {test_name} completed")
                except Exception as e:
                    results[test_name] = {"status": "failed", "error": str(e)}
                    print(f"⚠️  {test_name} failed: {e}")
            
            print(f"\n📊 FINAL RESULTS:")
            print("="*40)
            for test_name, result in results.items():
                status_icon = "✅" if result["status"] == "success" else "⚠️ "
                print(f"{status_icon} {test_name}: {result['status']}")
            
            success_count = sum(1 for r in results.values() if r["status"] == "success")
            print(f"\nSummary: {success_count}/{len(tests)} tests successful")
        
        elif choice == "6":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("\n❌ Invalid choice. Please select 1-6.")
        
        print("\n" + "-"*50)
        input("Press Enter to continue...")
        print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Test runner interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Test runner error: {e}")
        sys.exit(1)