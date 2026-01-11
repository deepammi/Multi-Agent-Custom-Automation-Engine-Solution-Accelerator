#!/usr/bin/env python3
"""Test script for AI Planner component."""
import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.llm_service import LLMService
from app.services.ai_planner_service import AIPlanner
from app.models.ai_planner import TaskAnalysis, AgentSequence

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_ai_planner():
    """Test the AI Planner component."""
    logger.info("🧪 Testing AI Planner Component")
    
    # Test cases
    test_tasks = [
        "Find emails about the Johnson PO and check if the invoice was processed correctly",
        "Analyze customer complaints about late deliveries in Q4",
        "Review all vendor invoices for accuracy and payment status",
        "Investigate discrepancies in the monthly financial closing",
        "Simple task: get customer info for ABC Corp"
    ]
    
    try:
        # Initialize AI Planner
        llm_service = LLMService()
        ai_planner = AIPlanner(llm_service)
        
        logger.info(f"✅ AI Planner initialized with {len(ai_planner.available_agents)} available agents")
        logger.info(f"Available agents: {', '.join(ai_planner.available_agents)}")
        
        # Test each task
        for i, task in enumerate(test_tasks, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"🎯 Test Case {i}: {task}")
            logger.info(f"{'='*60}")
            
            try:
                # Test complete workflow planning
                summary = await ai_planner.plan_workflow(task)
                
                if summary.success:
                    logger.info(f"✅ Planning successful!")
                    logger.info(f"📊 Analysis Duration: {summary.analysis_duration:.2f}s")
                    logger.info(f"🔄 Sequence Duration: {summary.sequence_generation_duration:.2f}s")
                    logger.info(f"⏱️  Total Duration: {summary.total_duration:.2f}s")
                    
                    # Display task analysis
                    analysis = summary.task_analysis
                    logger.info(f"\n📋 Task Analysis:")
                    logger.info(f"   Complexity: {analysis.complexity}")
                    logger.info(f"   Required Systems: {analysis.required_systems}")
                    logger.info(f"   Business Context: {analysis.business_context}")
                    logger.info(f"   Confidence: {analysis.confidence_score:.2f}")
                    logger.info(f"   Reasoning: {analysis.reasoning}")
                    
                    # Display agent sequence
                    sequence = summary.agent_sequence
                    logger.info(f"\n🎯 Agent Sequence:")
                    logger.info(f"   Agents: {' → '.join(sequence.agents)}")
                    logger.info(f"   Estimated Duration: {sequence.estimated_duration}s")
                    logger.info(f"   Complexity Score: {sequence.complexity_score:.2f}")
                    logger.info(f"   Valid Sequence: {sequence.is_valid_sequence()}")
                    
                    # Display reasoning for each agent
                    logger.info(f"\n💭 Agent Reasoning:")
                    for agent, reason in sequence.reasoning.items():
                        logger.info(f"   {agent}: {reason}")
                
                else:
                    logger.error(f"❌ Planning failed: {summary.error_message}")
                    
                    # Test fallback sequence
                    logger.info("🔄 Testing fallback sequence...")
                    fallback_sequence = ai_planner.get_fallback_sequence(task)
                    logger.info(f"   Fallback: {' → '.join(fallback_sequence.agents)}")
                    logger.info(f"   Valid: {fallback_sequence.is_valid_sequence()}")
                
            except Exception as e:
                logger.error(f"❌ Test case {i} failed: {str(e)}")
                
                # Test fallback sequence
                logger.info("🔄 Testing fallback sequence...")
                try:
                    fallback_sequence = ai_planner.get_fallback_sequence(task)
                    logger.info(f"   Fallback: {' → '.join(fallback_sequence.agents)}")
                    logger.info(f"   Valid: {fallback_sequence.is_valid_sequence()}")
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback also failed: {str(fallback_error)}")
        
        logger.info(f"\n{'='*60}")
        logger.info("🎉 AI Planner testing completed!")
        logger.info(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"❌ AI Planner initialization failed: {str(e)}")
        return False
    
    return True


async def test_individual_components():
    """Test individual AI Planner components."""
    logger.info("\n🔧 Testing Individual Components")
    
    try:
        # Initialize AI Planner
        llm_service = LLMService()
        ai_planner = AIPlanner(llm_service)
        
        # Test task analysis only
        test_task = "Find emails about the Johnson PO and check invoice processing"
        
        logger.info(f"🧠 Testing task analysis for: {test_task}")
        analysis = await ai_planner.analyze_task(test_task)
        
        logger.info(f"✅ Analysis completed:")
        logger.info(f"   Complexity: {analysis.complexity}")
        logger.info(f"   Systems: {analysis.required_systems}")
        logger.info(f"   Confidence: {analysis.confidence_score}")
        
        # Test sequence generation
        logger.info(f"\n🎯 Testing sequence generation...")
        sequence = await ai_planner.generate_sequence(analysis, test_task)
        
        logger.info(f"✅ Sequence generated:")
        logger.info(f"   Agents: {' → '.join(sequence.agents)}")
        logger.info(f"   Duration: {sequence.estimated_duration}s")
        logger.info(f"   Valid: {sequence.is_valid_sequence()}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Individual component testing failed: {str(e)}")
        return False


def check_environment():
    """Check if environment is properly configured."""
    logger.info("🔍 Checking environment configuration...")
    
    # Check LLM provider configuration
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    logger.info(f"LLM Provider: {provider}")
    
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            logger.info("✅ OpenAI API key found")
        else:
            logger.warning("⚠️  OpenAI API key not found - will use mock mode")
    
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            logger.info("✅ Anthropic API key found")
        else:
            logger.warning("⚠️  Anthropic API key not found - will use mock mode")
    
    # Check mock mode
    use_mock = os.getenv("USE_MOCK_LLM", "false").lower()
    if use_mock in ("true", "1", "yes"):
        logger.info("🎭 Mock mode enabled - using dummy responses")
    
    return True


async def main():
    """Main test function."""
    logger.info("🚀 Starting AI Planner Component Tests")
    
    # Check environment
    check_environment()
    
    # Run tests
    try:
        # Test complete workflow
        success1 = await test_ai_planner()
        
        # Test individual components
        success2 = await test_individual_components()
        
        if success1 and success2:
            logger.info("\n🎉 All tests passed successfully!")
            return True
        else:
            logger.error("\n❌ Some tests failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test execution failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Run the test
    success = asyncio.run(main())
    sys.exit(0 if success else 1)