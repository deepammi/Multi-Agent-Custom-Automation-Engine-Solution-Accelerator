#!/usr/bin/env python3
"""
Enhanced Gmail Query Transformation Tracing Script

This enhanced version provides:
1. Real LLM calls (when available) vs mock mode
2. Detailed query analysis at each step
3. Performance metrics
4. Error detection and debugging
5. Multiple test queries
6. Comparison between expected vs actual transformations

Example queries to test:
- "Find all emails from Acme Corp about Invoice INV-1001 from last month"
- "Search for emails containing 'payment due' from last week"
- "Show me recent emails from john@company.com"
"""

import asyncio
import logging
import sys
import os
import json
import time
from typing import Dict, Any, List
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class EnhancedQueryTracer:
    """Enhanced tracer with performance metrics and detailed analysis."""
    
    def __init__(self):
        self.step_counter = 0
        self.transformations = []
        self.start_time = time.time()
        self.step_times = []
        self.errors = []
        self.warnings = []
    
    def log_step(self, stage_name: str, input_data: Any, output_data: Any, description: str = "", 
                 performance_notes: str = "", expected_output: Any = None):
        """Log a transformation step with enhanced analysis."""
        step_start = time.time()
        self.step_counter += 1
        
        # Calculate step timing
        step_duration = time.time() - (self.step_times[-1] if self.step_times else self.start_time)
        self.step_times.append(time.time())
        
        # Analyze transformation quality
        transformation_analysis = self._analyze_transformation(input_data, output_data, expected_output)
        
        step_info = {
            "step": self.step_counter,
            "stage": stage_name,
            "input": input_data,
            "output": output_data,
            "expected_output": expected_output,
            "description": description,
            "performance_notes": performance_notes,
            "timestamp": datetime.now().isoformat(),
            "duration_ms": int(step_duration * 1000),
            "analysis": transformation_analysis
        }
        
        self.transformations.append(step_info)
        
        # Print detailed step information
        print(f"\n{'='*100}")
        print(f"STEP {self.step_counter}: {stage_name} ({int(step_duration * 1000)}ms)")
        print(f"{'='*100}")
        
        if description:
            print(f"📋 Description: {description}")
        
        if performance_notes:
            print(f"⚡ Performance: {performance_notes}")
        
        print(f"\n📥 INPUT ({type(input_data).__name__}):")
        self._print_formatted_data(input_data, "   ")
        
        print(f"\n📤 OUTPUT ({type(output_data).__name__}):")
        self._print_formatted_data(output_data, "   ")
        
        if expected_output is not None:
            print(f"\n🎯 EXPECTED OUTPUT:")
            self._print_formatted_data(expected_output, "   ")
            
            if transformation_analysis["matches_expected"]:
                print(f"✅ Output matches expected result")
            else:
                print(f"⚠️ Output differs from expected result")
                print(f"   Differences: {transformation_analysis['differences']}")
        
        # Show analysis
        if transformation_analysis["issues"]:
            print(f"\n🚨 ISSUES DETECTED:")
            for issue in transformation_analysis["issues"]:
                print(f"   - {issue}")
                self.warnings.append(f"Step {self.step_counter}: {issue}")
        
        if transformation_analysis["insights"]:
            print(f"\n💡 INSIGHTS:")
            for insight in transformation_analysis["insights"]:
                print(f"   - {insight}")
        
        print(f"{'='*100}")
    
    def _print_formatted_data(self, data: Any, indent: str = ""):
        """Print data in a formatted, readable way."""
        if isinstance(data, dict):
            if len(json.dumps(data, default=str)) > 500:
                # For large objects, show summary
                print(f"{indent}{{")
                for key, value in data.items():
                    if isinstance(value, (str, int, float, bool)):
                        print(f"{indent}  {key}: {repr(value)}")
                    elif isinstance(value, (list, dict)):
                        print(f"{indent}  {key}: {type(value).__name__}({len(value)} items)")
                    else:
                        print(f"{indent}  {key}: {type(value).__name__}")
                print(f"{indent}}}")
            else:
                print(f"{indent}{json.dumps(data, indent=2, default=str)}")
        elif isinstance(data, str) and len(data) > 300:
            print(f"{indent}{data[:300]}...")
        else:
            print(f"{indent}{json.dumps(data, indent=2, default=str)}")
    
    def _analyze_transformation(self, input_data: Any, output_data: Any, expected_output: Any = None) -> Dict[str, Any]:
        """Analyze the quality and correctness of a transformation."""
        analysis = {
            "matches_expected": False,
            "differences": [],
            "issues": [],
            "insights": [],
            "data_flow_valid": True
        }
        
        # Check if output matches expected
        if expected_output is not None:
            if output_data == expected_output:
                analysis["matches_expected"] = True
            else:
                analysis["differences"] = self._find_differences(output_data, expected_output)
        
        # Detect common issues
        if output_data is None:
            analysis["issues"].append("Output is None - possible processing failure")
        
        if isinstance(output_data, dict) and "error" in output_data:
            analysis["issues"].append(f"Error in output: {output_data['error']}")
        
        if isinstance(input_data, str) and isinstance(output_data, str) and input_data == output_data:
            analysis["insights"].append("No transformation applied - passthrough detected")
        
        # Analyze data flow
        if isinstance(input_data, dict) and isinstance(output_data, dict):
            input_keys = set(input_data.keys())
            output_keys = set(output_data.keys())
            
            if input_keys.issubset(output_keys):
                analysis["insights"].append("All input data preserved in output")
            elif input_keys.intersection(output_keys):
                analysis["insights"].append("Partial input data preserved in output")
            else:
                analysis["insights"].append("Complete data transformation - no input keys preserved")
        
        return analysis
    
    def _find_differences(self, actual: Any, expected: Any) -> List[str]:
        """Find differences between actual and expected output."""
        differences = []
        
        if type(actual) != type(expected):
            differences.append(f"Type mismatch: got {type(actual).__name__}, expected {type(expected).__name__}")
            return differences
        
        if isinstance(actual, dict) and isinstance(expected, dict):
            actual_keys = set(actual.keys())
            expected_keys = set(expected.keys())
            
            missing_keys = expected_keys - actual_keys
            extra_keys = actual_keys - expected_keys
            
            if missing_keys:
                differences.append(f"Missing keys: {missing_keys}")
            if extra_keys:
                differences.append(f"Extra keys: {extra_keys}")
            
            for key in actual_keys.intersection(expected_keys):
                if actual[key] != expected[key]:
                    differences.append(f"Key '{key}': got {repr(actual[key])}, expected {repr(expected[key])}")
        
        elif actual != expected:
            differences.append(f"Value mismatch: got {repr(actual)}, expected {repr(expected)}")
        
        return differences
    
    def log_error(self, stage_name: str, error: Exception, context: Dict[str, Any] = None):
        """Log an error during processing."""
        error_info = {
            "step": self.step_counter + 1,
            "stage": stage_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.errors.append(error_info)
        
        print(f"\n❌ ERROR in {stage_name}:")
        print(f"   Type: {type(error).__name__}")
        print(f"   Message: {str(error)}")
        if context:
            print(f"   Context: {json.dumps(context, indent=2, default=str)}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of the entire pipeline."""
        total_time = time.time() - self.start_time
        
        return {
            "total_duration_ms": int(total_time * 1000),
            "total_steps": self.step_counter,
            "average_step_time_ms": int((total_time / max(self.step_counter, 1)) * 1000),
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "success_rate": (self.step_counter - len(self.errors)) / max(self.step_counter, 1),
            "step_times_ms": [int((self.step_times[i] - (self.step_times[i-1] if i > 0 else self.start_time)) * 1000) 
                             for i in range(len(self.step_times))]
        }
    
    def print_final_summary(self):
        """Print comprehensive final summary."""
        perf = self.get_performance_summary()
        
        print(f"\n🎯 COMPREHENSIVE PIPELINE ANALYSIS")
        print(f"{'='*100}")
        
        print(f"\n📊 PERFORMANCE METRICS:")
        print(f"   Total Duration: {perf['total_duration_ms']}ms")
        print(f"   Total Steps: {perf['total_steps']}")
        print(f"   Average Step Time: {perf['average_step_time_ms']}ms")
        print(f"   Success Rate: {perf['success_rate']:.1%}")
        
        if perf['step_times_ms']:
            slowest_step = max(enumerate(perf['step_times_ms']), key=lambda x: x[1])
            fastest_step = min(enumerate(perf['step_times_ms']), key=lambda x: x[1])
            print(f"   Slowest Step: #{slowest_step[0]+1} ({slowest_step[1]}ms)")
            print(f"   Fastest Step: #{fastest_step[0]+1} ({fastest_step[1]}ms)")
        
        print(f"\n🚨 ISSUES SUMMARY:")
        print(f"   Errors: {len(self.errors)}")
        print(f"   Warnings: {len(self.warnings)}")
        
        if self.errors:
            print(f"\n   ERROR DETAILS:")
            for error in self.errors:
                print(f"     Step {error['step']}: {error['error_type']} - {error['error_message']}")
        
        if self.warnings:
            print(f"\n   WARNING DETAILS:")
            for warning in self.warnings:
                print(f"     {warning}")
        
        print(f"\n🔄 PIPELINE FLOW:")
        for i, transform in enumerate(self.transformations, 1):
            status = "✅" if not transform['analysis']['issues'] else "⚠️"
            print(f"   {i:2d}. {status} {transform['stage']} ({transform['duration_ms']}ms)")
        
        print(f"\n{'='*100}")


async def test_query_transformation_enhanced(query: str, expected_transformations: Dict[str, Any] = None):
    """Test query transformation with enhanced tracing and analysis."""
    
    tracer = EnhancedQueryTracer()
    
    print(f"\n🚀 ENHANCED GMAIL QUERY TRANSFORMATION ANALYSIS")
    print(f"📝 Test Query: '{query}'")
    print(f"⏰ Started at: {datetime.now().isoformat()}")
    
    try:
        # Import required modules
        from app.agents.gmail_agent_node import GmailAgentNode
        from app.services.llm_service import LLMService
        
        # Step 1: Query Analysis
        query_analysis = {
            "length": len(query),
            "word_count": len(query.split()),
            "contains_keywords": {
                "search_terms": any(word in query.lower() for word in ["find", "search", "look", "show"]),
                "email_terms": any(word in query.lower() for word in ["email", "message", "mail"]),
                "time_terms": any(word in query.lower() for word in ["last", "recent", "today", "yesterday", "week", "month"]),
                "company_terms": any(word in query.lower() for word in ["corp", "company", "inc", "ltd"]),
                "invoice_terms": any(word in query.lower() for word in ["invoice", "inv-", "bill", "payment"])
            },
            "complexity": "high" if len(query.split()) > 10 else "medium" if len(query.split()) > 5 else "low"
        }
        
        expected_query_analysis = expected_transformations.get("query_analysis") if expected_transformations else None
        
        tracer.log_step(
            "Query Analysis",
            {"raw_query": query},
            query_analysis,
            "Analyze query structure and extract key characteristics",
            f"Query complexity: {query_analysis['complexity']}, {query_analysis['word_count']} words",
            expected_query_analysis
        )
        
        # Step 2: Gmail Agent Setup
        gmail_agent = GmailAgentNode()
        
        agent_info = {
            "agent_name": gmail_agent.name,
            "service": gmail_agent.service,
            "email_agent_type": type(gmail_agent.email_agent).__name__,
            "supported_actions": ["search", "list", "get", "send"]
        }
        
        tracer.log_step(
            "Gmail Agent Setup",
            {"query": query},
            agent_info,
            "Initialize Gmail agent with category-based Email Agent",
            "Agent ready for processing"
        )
        
        # Step 3: State Preparation with Enhanced Context
        test_state = {
            "task": "",
            "user_request": query,
            "plan_id": f"enhanced-trace-{int(time.time())}",
            "websocket_manager": None,  # Mock mode
            "session_id": "test-session",
            "user_id": "test-user"
        }
        
        tracer.log_step(
            "State Preparation",
            {"query": query, "context": "test_environment"},
            test_state,
            "Prepare enhanced state with full context",
            "State includes session tracking and user context"
        )
        
        # Step 4: Intent Analysis with Real/Mock LLM
        print(f"\n🤖 PERFORMING INTENT ANALYSIS...")
        
        # Check if we can use real LLM or need mock
        use_mock = LLMService.is_mock_mode() if hasattr(LLMService, 'is_mock_mode') else True
        
        intent_analysis_result = await gmail_agent._analyze_user_intent(query, test_state)
        
        expected_intent = expected_transformations.get("intent_analysis") if expected_transformations else {
            "action": "search",
            "query": "from:acme invoice INV-1001 newer_than:1m",
            "max_results": 15
        }
        
        tracer.log_step(
            "LLM Intent Analysis",
            {"user_query": query, "llm_mode": "mock" if use_mock else "real"},
            intent_analysis_result,
            "LLM analyzes user intent and extracts structured action",
            f"LLM mode: {'Mock' if use_mock else 'Real'}, Action: {intent_analysis_result.get('action', 'unknown')}",
            expected_intent
        )
        
        # Step 5: Query Transformation Analysis
        if intent_analysis_result.get("action") == "search":
            original_query = query
            transformed_query = intent_analysis_result.get("query", "")
            
            transformation_analysis = {
                "original_query": original_query,
                "transformed_query": transformed_query,
                "transformation_type": "natural_language_to_gmail_syntax",
                "gmail_operators_used": [],
                "transformation_quality": "unknown"
            }
            
            # Analyze Gmail operators used
            gmail_operators = ["from:", "to:", "subject:", "newer_than:", "older_than:", "has:", "in:", "is:"]
            for operator in gmail_operators:
                if operator in transformed_query:
                    transformation_analysis["gmail_operators_used"].append(operator)
            
            # Assess transformation quality
            if transformation_analysis["gmail_operators_used"]:
                transformation_analysis["transformation_quality"] = "good"
            elif transformed_query and transformed_query != original_query:
                transformation_analysis["transformation_quality"] = "basic"
            else:
                transformation_analysis["transformation_quality"] = "poor"
            
            tracer.log_step(
                "Query Transformation Analysis",
                {"original": original_query},
                transformation_analysis,
                "Analyze how natural language was transformed to Gmail search syntax",
                f"Quality: {transformation_analysis['transformation_quality']}, Operators: {len(transformation_analysis['gmail_operators_used'])}"
            )
        
        # Step 6: Simulate MCP Call with Detailed Analysis
        if intent_analysis_result.get("action") == "search":
            search_query = intent_analysis_result.get("query", "")
            
            # Simulate what the MCP call would look like
            mcp_call_simulation = {
                "service": "gmail",
                "tool": "gmail_search_messages",
                "arguments": {
                    "query": search_query,
                    "max_results": intent_analysis_result.get("max_results", 15)
                },
                "expected_server": "http://localhost:9002/mcp",
                "transport": "HTTP"
            }
            
            tracer.log_step(
                "MCP Call Simulation",
                {"search_parameters": intent_analysis_result},
                mcp_call_simulation,
                "Simulate the actual MCP tool call that would be made",
                f"Tool: {mcp_call_simulation['tool']}, Query: '{search_query}'"
            )
            
            # Simulate response analysis
            mock_response = {
                "messages": [
                    {
                        "id": f"msg_{i:03d}",
                        "snippet": f"Mock email {i} matching query: {search_query}",
                        "relevance_score": 0.9 - (i * 0.1)
                    }
                    for i in range(1, 4)
                ],
                "total_estimated": 3,
                "query_performance": {
                    "execution_time_ms": 150,
                    "index_hits": 1250,
                    "results_filtered": 3
                }
            }
            
            response_analysis = {
                "messages_found": len(mock_response["messages"]),
                "average_relevance": sum(msg["relevance_score"] for msg in mock_response["messages"]) / len(mock_response["messages"]),
                "performance_acceptable": mock_response["query_performance"]["execution_time_ms"] < 1000,
                "results_quality": "good" if len(mock_response["messages"]) > 0 else "poor"
            }
            
            tracer.log_step(
                "Search Results Analysis",
                {"mcp_call": mcp_call_simulation},
                {**mock_response, "analysis": response_analysis},
                "Analyze search results quality and performance",
                f"Found {response_analysis['messages_found']} messages, avg relevance: {response_analysis['average_relevance']:.2f}"
            )
        
        # Final Summary
        tracer.print_final_summary()
        
        return {
            "success": True,
            "transformations": tracer.transformations,
            "performance": tracer.get_performance_summary(),
            "errors": tracer.errors,
            "warnings": tracer.warnings
        }
        
    except Exception as e:
        tracer.log_error("Pipeline Execution", e, {"query": query})
        tracer.print_final_summary()
        return {
            "success": False,
            "error": str(e),
            "transformations": tracer.transformations,
            "performance": tracer.get_performance_summary()
        }


async def run_multiple_test_queries():
    """Run multiple test queries to compare transformations."""
    
    test_queries = [
        {
            "query": "Find all emails from Acme Corp about Invoice INV-1001 from last month",
            "expected": {
                "intent_analysis": {
                    "action": "search",
                    "query": "from:acme invoice INV-1001 newer_than:1m",
                    "max_results": 15
                },
                "query_analysis": {
                    "complexity": "high",
                    "contains_keywords": {
                        "search_terms": True,
                        "email_terms": True,
                        "company_terms": True,
                        "invoice_terms": True,
                        "time_terms": True
                    }
                }
            }
        },
        {
            "query": "Show me recent emails from john@company.com",
            "expected": {
                "intent_analysis": {
                    "action": "search",
                    "query": "from:john@company.com newer_than:7d",
                    "max_results": 10
                }
            }
        },
        {
            "query": "List my last 5 emails",
            "expected": {
                "intent_analysis": {
                    "action": "list",
                    "max_results": 5
                }
            }
        }
    ]
    
    print(f"\n🧪 RUNNING MULTIPLE QUERY TRANSFORMATION TESTS")
    print(f"{'='*100}")
    
    results = []
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n📋 TEST CASE {i}/{len(test_queries)}")
        print(f"{'='*50}")
        
        result = await test_query_transformation_enhanced(
            test_case["query"], 
            test_case.get("expected")
        )
        
        results.append({
            "test_case": i,
            "query": test_case["query"],
            "result": result
        })
        
        print(f"\n✅ Test Case {i} {'PASSED' if result['success'] else 'FAILED'}")
    
    # Print overall summary
    print(f"\n🎯 OVERALL TEST SUMMARY")
    print(f"{'='*100}")
    
    passed = sum(1 for r in results if r["result"]["success"])
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total} ({passed/total:.1%})")
    
    for result in results:
        status = "✅ PASS" if result["result"]["success"] else "❌ FAIL"
        perf = result["result"]["performance"]
        print(f"  {status} - Query {result['test_case']}: {perf['total_duration_ms']}ms, {perf['total_steps']} steps")
    
    return results


async def main():
    """Main function for enhanced query transformation testing."""
    
    print("🔍 Enhanced Gmail Query Transformation Tracing Tool")
    print("=" * 100)
    print("This enhanced tool provides detailed analysis of query transformations")
    print("with performance metrics, error detection, and quality assessment.")
    print("=" * 100)
    
    # Run multiple test cases
    results = await run_multiple_test_queries()
    
    # Final summary
    success_count = sum(1 for r in results if r["result"]["success"])
    print(f"\n🏁 FINAL RESULTS: {success_count}/{len(results)} tests passed")
    
    if success_count == len(results):
        print("🎉 All query transformation tests completed successfully!")
    else:
        print("⚠️ Some tests failed - check the detailed logs above for issues")


if __name__ == "__main__":
    print("Starting Enhanced Gmail Query Transformation Analysis...")
    asyncio.run(main())