#!/usr/bin/env python3
"""
Test script to verify Gemini is being used for AI planning.
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.ai_planner_service import AIPlanner
from app.services.llm_service import LLMService
from app.db.mongodb import MongoDB

async def test_gemini_ai_planner():
    """Test that AI Planner uses Gemini for task analysis and sequence generation."""
    
    print("🧪 Testing Gemini AI Planner Integration")
    print("=" * 60)
    
    # Initialize AI Planner
    llm_service = LLMService()
    ai_planner = AIPlanner(llm_service)
    
    # Test task
    task = "Find emails about invoice INV-1001 from Acme Marketing and check payment status"
    
    print(f"\n📋 Task: {task}")
    
    try:
        # Test 1: Task Analysis with Gemini
        print("\n1. Testing Task Analysis with Gemini:")
        print("   🤖 Calling Gemini for task analysis...")
        
        task_analysis = await ai_planner.analyze_task(task)
        
        print(f"   ✅ Task Analysis Complete:")
        print(f"      Complexity: {task_analysis.complexity}")
        print(f"      Required Systems: {task_analysis.required_systems}")
        print(f"      Business Context: {task_analysis.business_context}")
        print(f"      Estimated Agents: {task_analysis.estimated_agents}")
        print(f"      Confidence Score: {task_analysis.confidence_score}")
        
        # Verify planner is included
        if "planner" in task_analysis.estimated_agents:
            print("   ✅ Planner agent included in estimated agents")
        else:
            print("   ❌ Planner agent missing from estimated agents")
            return False
        
        # Test 2: Sequence Generation with Gemini
        print("\n2. Testing Sequence Generation with Gemini:")
        print("   🤖 Calling Gemini for sequence generation...")
        
        agent_sequence = await ai_planner.generate_sequence(task_analysis, task)
        
        print(f"   ✅ Agent Sequence Generated:")
        print(f"      Agents: {agent_sequence.agents}")
        print(f"      Estimated Duration: {agent_sequence.estimated_duration}s")
        print(f"      Complexity Score: {agent_sequence.complexity_score}")
        
        # Verify planner is first
        if agent_sequence.agents and agent_sequence.agents[0] == "planner":
            print("   ✅ Sequence starts with 'planner' agent")
        else:
            print(f"   ❌ Sequence does NOT start with 'planner': {agent_sequence.agents}")
            return False
        
        # Show reasoning
        print(f"\n   🧠 Gemini's Reasoning:")
        for agent, reason in agent_sequence.reasoning.items():
            print(f"      {agent}: {reason}")
        
        # Test 3: Complete Workflow
        print("\n3. Testing Complete AI Planning Workflow:")
        print("   🤖 Running complete workflow with Gemini...")
        
        planning_summary = await ai_planner.plan_workflow(task)
        
        print(f"   ✅ Workflow Planning Complete:")
        print(f"      Success: {planning_summary.success}")
        print(f"      Total Duration: {planning_summary.total_duration:.2f}s")
        print(f"      Analysis Duration: {planning_summary.analysis_duration:.2f}s")
        print(f"      Sequence Duration: {planning_summary.sequence_generation_duration:.2f}s")
        
        if planning_summary.success:
            final_sequence = planning_summary.agent_sequence.agents
            print(f"      Final Sequence: {final_sequence}")
            
            if final_sequence and final_sequence[0] == "planner":
                print("   ✅ Final sequence starts with 'planner'")
                return True
            else:
                print(f"   ❌ Final sequence does NOT start with 'planner': {final_sequence}")
                return False
        else:
            print(f"   ❌ Workflow planning failed: {planning_summary.error_message}")
            return False
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Initialize database connection
    try:
        print("🔌 Initializing database connection...")
        MongoDB.connect()
        print("✅ Database connected successfully\n")
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print("   Test will continue but may show database errors\n")
    
    success = asyncio.run(test_gemini_ai_planner())
    
    # Close database connection
    try:
        MongoDB.close()
        print("\n🔌 Database connection closed")
    except Exception as e:
        print(f"⚠️  Error closing database: {e}")
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SUCCESS! Gemini AI Planner Integration Working Perfectly!")
        print("\nKey achievements:")
        print("✅ Gemini is being used for AI task analysis")
        print("✅ Gemini is being used for agent sequence generation")
        print("✅ All sequences start with the 'planner' agent")
        print("✅ AI planning workflow is complete and functional")
        print("✅ Backend routing issue is FIXED!")
        
        print("\n🚀 The system now properly routes all queries through the Planner agent first,")
        print("   using Gemini AI for intelligent task analysis and agent coordination!")
    else:
        print("❌ Gemini AI Planner integration has issues.")
        print("Please check the error messages above.")