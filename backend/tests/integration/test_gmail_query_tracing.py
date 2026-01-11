#!/usr/bin/env python3
"""
Gmail Query Transformation Tracing Script - REAL MODE

This script traces the complete query transformation pipeline for Gmail search operations,
showing each step of the process from user input to final MCP tool call using REAL LLM calls
and REAL MCP responses (no mock data).

Example: "Find all emails from with keywords invoice or INV-1001 anywhere in subject or body of email, from last month"
"""

import asyncio
import logging
import sys
import os
import json
from typing import Dict, Any
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment variables")
except Exception as e:
    print(f"⚠️ Could not load .env file: {e}")

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create a custom logger for our tracing
trace_logger = logging.getLogger("QUERY_TRACE")
trace_logger.setLevel(logging.INFO)

# Create console handler with custom format for tracing
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
trace_formatter = logging.Formatter('🔍 TRACE: %(message)s')
console_handler.setFormatter(trace_formatter)
trace_logger.addHandler(console_handler)


class RealWebSocketManager:
    """Real WebSocket manager for capturing LLM streaming responses."""
    
    def __init__(self):
        self.messages = []
        self.streaming_content = []
    
    async def send_message(self, plan_id: str, message: Dict[str, Any]):
        """Capture WebSocket messages for analysis."""
        self.messages.append({
            "plan_id": plan_id,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Capture streaming content
        if message.get("type") == "agent_message_streaming":
            self.streaming_content.append(message.get("content", ""))
        
        # Log the message for tracing
        msg_type = message.get("type", "unknown")
        if msg_type == "agent_message_streaming":
            print(f"🔄 STREAMING: {message.get('content', '')}", end="", flush=True)
        elif msg_type == "agent_stream_start":
            print(f"\n🚀 LLM STREAM START for {message.get('agent', 'unknown')}")
        elif msg_type == "agent_stream_end":
            print(f"\n✅ LLM STREAM END")
            if message.get("error"):
                print(f"❌ ERROR: {message.get('error_message', 'Unknown error')}")
    
    def get_full_response(self) -> str:
        """Get the complete streamed response."""
        return "".join(self.streaming_content)
    
    def clear_streaming_content(self):
        """Clear streaming content for next call."""
        self.streaming_content = []


class QueryTransformationTracer:
    """Traces the complete query transformation pipeline with real calls."""
    
    def __init__(self):
        self.step_counter = 0
        self.transformations = []
    
    def log_step(self, stage_name: str, input_data: Any, output_data: Any, description: str = ""):
        """Log a transformation step with before/after data."""
        self.step_counter += 1
        
        step_info = {
            "step": self.step_counter,
            "stage": stage_name,
            "input": input_data,
            "output": output_data,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
        
        self.transformations.append(step_info)
        
        print(f"\n{'='*80}")
        print(f"STEP {self.step_counter}: {stage_name}")
        print(f"{'='*80}")
        if description:
            print(f"Description: {description}")
        print(f"\n📥 INPUT:")
        print(f"   {json.dumps(input_data, indent=2, default=str)}")
        print(f"\n📤 OUTPUT:")
        print(f"   {json.dumps(output_data, indent=2, default=str)}")
        print(f"{'='*80}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all transformations."""
        return {
            "total_steps": self.step_counter,
            "transformations": self.transformations,
            "pipeline_summary": [
                f"Step {t['step']}: {t['stage']}" for t in self.transformations
            ]
        }


async def trace_gmail_query_transformation_real(user_query: str):
    """
    Trace the complete Gmail query transformation pipeline using REAL LLM and MCP calls.
    
    Args:
        user_query: The user's natural language query
    """
    tracer = QueryTransformationTracer()
    
    print(f"\n🚀 STARTING REAL GMAIL QUERY TRANSFORMATION TRACE")
    print(f"📝 User Query: '{user_query}'")
    print(f"⏰ Started at: {datetime.now().isoformat()}")
    print(f"🔥 MODE: REAL LLM + REAL MCP CALLS (NO MOCKS)")
    
    try:
        # Import required modules
        from app.agents.gmail_agent_node import GmailAgentNode
        from app.services.llm_service import LLMService
        
        # Step 1: Environment Setup and Configuration
        # Force disable mock mode and set Gemini as provider
        os.environ["USE_MOCK_LLM"] = "false"
        os.environ["LLM_PROVIDER"] = "gemini"
        
        # Check LLM configuration
        llm_provider = os.getenv("LLM_PROVIDER", "gemini")
        api_key_env = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "gemini": "GOOGLE_API_KEY"
        }.get(llm_provider.lower())
        
        api_key = os.getenv(api_key_env) if api_key_env else None
        
        env_config = {
            "llm_provider": llm_provider,
            "api_key_configured": bool(api_key),
            "mock_mode_disabled": True,
            "mcp_server_url": "http://localhost:9002/mcp"
        }
        
        tracer.log_step(
            "Environment Configuration",
            {"user_query": user_query},
            env_config,
            "Configure environment for real LLM and MCP calls"
        )
        
        if not api_key:
            raise ValueError(f"API key not configured for {llm_provider}. Set {api_key_env} environment variable.")
        
        # Step 2: Gmail Agent Initialization
        gmail_agent = GmailAgentNode()
        
        agent_info = {
            "agent_name": gmail_agent.name,
            "service": gmail_agent.service,
            "email_agent_type": type(gmail_agent.email_agent).__name__,
            "mcp_manager_type": type(gmail_agent.email_agent.mcp_manager).__name__
        }
        
        tracer.log_step(
            "Gmail Agent Initialization",
            {"agent_class": "GmailAgentNode"},
            agent_info,
            "Initialize Gmail agent with real MCP HTTP client"
        )
        
        # Step 3: WebSocket Manager Setup for Real LLM Streaming
        websocket_manager = RealWebSocketManager()
        
        test_state = {
            "task": "",
            "user_request": user_query,
            "plan_id": f"real-trace-{int(datetime.now().timestamp())}",
            "websocket_manager": websocket_manager,
            "session_id": "real-test-session",
            "user_id": "real-test-user"
        }
        
        tracer.log_step(
            "State Preparation with Real WebSocket",
            {"user_query": user_query},
            {k: v if k != "websocket_manager" else "RealWebSocketManager()" for k, v in test_state.items()},
            "Prepare state with real WebSocket manager for LLM streaming"
        )
        
        # Step 4: Combined Text Creation
        combined_text = f"{test_state.get('task', '')} {test_state.get('user_request', '')}".strip()
        tracer.log_step(
            "Combined Text Creation",
            {
                "task": test_state.get('task', ''),
                "user_request": test_state.get('user_request', '')
            },
            {"combined_text": combined_text},
            "Combine task and user request for processing"
        )
        
        # Step 5: REAL LLM Intent Analysis
        print(f"\n🤖 CALLING REAL LLM FOR INTENT ANALYSIS...")
        print(f"Provider: {llm_provider}")
        print(f"Mock Mode: {LLMService.is_mock_mode()}")
        
        websocket_manager.clear_streaming_content()
        
        # Call the real LLM intent analysis
        action_analysis = await gmail_agent._analyze_user_intent(combined_text, test_state)
        
        # Get the full LLM response from streaming
        full_llm_response = websocket_manager.get_full_response()
        
        tracer.log_step(
            "REAL LLM Intent Analysis",
            {
                "user_query": combined_text,
                "llm_provider": llm_provider,
                "websocket_messages": len(websocket_manager.messages)
            },
            {
                "action_analysis": action_analysis,
                "full_llm_response": full_llm_response,
                "response_length": len(full_llm_response),
                "is_real_llm": True
            },
            "Real LLM analyzes user intent and returns structured action"
        )
        
        # Step 6: Query Transformation Analysis
        if action_analysis.get("action") == "search":
            original_query = user_query
            transformed_query = action_analysis.get("query", "")
            
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
                {"original": original_query, "llm_output": action_analysis},
                transformation_analysis,
                "Analyze how LLM transformed natural language to Gmail search syntax"
            )
        
        # Step 7: REAL MCP Call Execution
        if action_analysis.get("action") == "search":
            search_query = action_analysis.get("query", "")
            max_results = action_analysis.get("max_results", 15)
            
            print(f"\n📡 EXECUTING REAL MCP CALL...")
            print(f"Service: gmail")
            print(f"Tool: gmail_search_messages")
            print(f"Query: {search_query}")
            
            try:
                # Execute the real MCP call
                email_data = await gmail_agent._search_emails_with_llm_query(search_query)
                
                # Parse the MCP response properly
                messages = []
                has_error = False
                error_message = None
                
                if isinstance(email_data, dict):
                    if "error" in email_data:
                        has_error = True
                        error_message = email_data["error"]
                        messages = email_data.get("messages", [])
                    elif "result" in email_data:
                        # Handle FastMCP CallToolResult format
                        result = email_data["result"]
                        
                        # First try to access structured_content directly if it's an object
                        if hasattr(result, 'structured_content') and result.structured_content:
                            messages = result.structured_content.get("messages", [])
                            print(f"✅ Extracted {len(messages)} messages from result.structured_content")
                        elif hasattr(result, 'data') and result.data:
                            messages = result.data.get("messages", [])
                            print(f"✅ Extracted {len(messages)} messages from result.data")
                        else:
                            # Parse from string representation - this is the most common case
                            result_str = str(result)
                            print(f"🔍 Parsing from string representation: {result_str[:200]}...")
                            
                            # Look for structured_content in the string
                            if 'structured_content=' in result_str:
                                try:
                                    # Find the structured_content section
                                    start_marker = "structured_content="
                                    start_idx = result_str.find(start_marker)
                                    if start_idx != -1:
                                        # Extract the dictionary part after structured_content=
                                        content_start = start_idx + len(start_marker)
                                        
                                        # Find the end of the structured_content dict
                                        brace_count = 0
                                        in_dict = False
                                        content_end = content_start
                                        
                                        for i, char in enumerate(result_str[content_start:]):
                                            if char == '{' and not in_dict:
                                                in_dict = True
                                                brace_count = 1
                                            elif in_dict:
                                                if char == '{':
                                                    brace_count += 1
                                                elif char == '}':
                                                    brace_count -= 1
                                                    if brace_count == 0:
                                                        content_end = content_start + i + 1
                                                        break
                                        
                                        if in_dict and brace_count == 0:
                                            structured_content_str = result_str[content_start:content_end]
                                            print(f"🔍 Extracted structured_content string: {structured_content_str[:200]}...")
                                            
                                            # Use eval to parse the Python dict (safer than JSON for this case)
                                            try:
                                                structured_content = eval(structured_content_str)
                                                messages = structured_content.get("messages", [])
                                                print(f"✅ Successfully parsed {len(messages)} messages from structured_content")
                                            except Exception as eval_error:
                                                print(f"❌ Failed to eval structured_content: {eval_error}")
                                                # Fallback: try to extract messages directly from the string
                                                if '"messages":[' in result_str or "'messages':[" in result_str:
                                                    # Extract the JSON part from the text content
                                                    text_start = result_str.find('text=\'{"messages":[')
                                                    if text_start == -1:
                                                        text_start = result_str.find('text="{\"messages\":[')
                                                    
                                                    if text_start != -1:
                                                        # Find the end of the JSON
                                                        json_start = result_str.find('{"messages":[', text_start)
                                                        if json_start != -1:
                                                            # Find the matching closing brace
                                                            brace_count = 0
                                                            json_end = json_start
                                                            for i, char in enumerate(result_str[json_start:]):
                                                                if char == '{':
                                                                    brace_count += 1
                                                                elif char == '}':
                                                                    brace_count -= 1
                                                                    if brace_count == 0:
                                                                        json_end = json_start + i + 1
                                                                        break
                                                            
                                                            json_str = result_str[json_start:json_end]
                                                            try:
                                                                import json
                                                                parsed_json = json.loads(json_str)
                                                                messages = parsed_json.get("messages", [])
                                                                print(f"✅ Fallback: extracted {len(messages)} messages from JSON text")
                                                            except Exception as json_error:
                                                                print(f"❌ Fallback JSON parsing failed: {json_error}")
                                                                messages = []
                                except Exception as parse_error:
                                    print(f"❌ Failed to parse structured_content: {parse_error}")
                                    messages = []
                    else:
                        messages = email_data.get("messages", [])
                
                mcp_call_result = {
                    "mcp_service": "gmail",
                    "mcp_tool": "gmail_search_messages",
                    "mcp_arguments": {
                        "query": search_query,
                        "max_results": max_results
                    },
                    "mcp_response": email_data,
                    "messages_found": len(messages),
                    "has_error": has_error,
                    "error_message": error_message,
                    "is_real_mcp": True
                }
                
                tracer.log_step(
                    "REAL MCP Tool Call",
                    {
                        "search_query": search_query,
                        "max_results": max_results,
                        "service": "gmail"
                    },
                    mcp_call_result,
                    "Execute real MCP call to Gmail search API"
                )
                
                # Step 8: Email Data Processing and Analysis
                if messages and len(messages) > 0:
                    # Analyze the real email data
                    
                    email_analysis = {
                        "total_messages": len(messages),
                        "sample_subjects": [],
                        "sample_senders": [],
                        "date_range": {"earliest": None, "latest": None},
                        "contains_target_terms": 0,
                        "exact_matches": []
                    }
                    
                    target_terms = ["acme", "invoice", "inv-1001"]
                    
                    for msg in messages[:5]:  # Analyze first 5 messages
                        # Extract headers
                        subject = "No subject"
                        sender = "Unknown sender"
                        date = "Unknown date"
                        
                        if "payload" in msg and "headers" in msg["payload"]:
                            headers = msg["payload"]["headers"]
                            for header in headers:
                                header_name = header.get("name", "").lower()
                                header_value = header.get("value", "")
                                
                                if header_name == "subject":
                                    subject = header_value
                                    email_analysis["sample_subjects"].append(header_value)
                                elif header_name == "from":
                                    sender = header_value
                                    email_analysis["sample_senders"].append(header_value)
                                elif header_name == "date":
                                    date = header_value
                                    if not email_analysis["date_range"]["earliest"]:
                                        email_analysis["date_range"]["earliest"] = header_value
                                    email_analysis["date_range"]["latest"] = header_value
                        
                        # Check for target terms in snippet and subject
                        snippet = msg.get("snippet", "").lower()
                        subject_lower = subject.lower()
                        
                        if any(term in snippet or term in subject_lower for term in target_terms):
                            email_analysis["contains_target_terms"] += 1
                        
                        # Check for exact matches
                        if "inv-1001" in snippet or "inv-1001" in subject_lower:
                            email_analysis["exact_matches"].append({
                                "id": msg.get("id"),
                                "subject": subject,
                                "sender": sender,
                                "snippet": snippet[:100] + "..." if len(snippet) > 100 else snippet
                            })
                    
                    tracer.log_step(
                        "Real Email Data Analysis",
                        {"raw_mcp_response": f"{len(messages)} messages found"},
                        email_analysis,
                        "Analyze real email data returned from MCP call"
                    )
                    
                    # Step 9: REAL LLM Result Analysis
                    print(f"\n🤖 CALLING REAL LLM FOR RESULT ANALYSIS...")
                    
                    websocket_manager.clear_streaming_content()
                    
                    # Import LLMService for the analysis
                    from app.services.llm_service import LLMService
                    
                    # Call real LLM for result analysis
                    final_analysis = await gmail_agent._analyze_email_results_with_llm(
                        user_query, {"messages": messages}, test_state
                    )
                    
                    # Get the full LLM response
                    full_analysis_response = websocket_manager.get_full_response()
                    
                    tracer.log_step(
                        "REAL LLM Result Analysis",
                        {
                            "original_query": user_query,
                            "email_count": len(messages),
                            "llm_provider": llm_provider,
                            "exact_matches_found": len(email_analysis["exact_matches"])
                        },
                        {
                            "final_analysis": final_analysis,
                            "full_llm_response": full_analysis_response,
                            "analysis_length": len(final_analysis),
                            "is_real_llm": True
                        },
                        "Real LLM analyzes email results and provides final response"
                    )
                    
                else:
                    tracer.log_step(
                        "No Email Results",
                        {"mcp_response": email_data},
                        {
                            "message": "No emails found matching the search criteria",
                            "has_error": has_error,
                            "error_message": error_message
                        },
                        "MCP call returned no results or encountered an error"
                    )
                
            except Exception as mcp_error:
                tracer.log_step(
                    "MCP Call Error",
                    {"search_query": search_query},
                    {
                        "error_type": type(mcp_error).__name__,
                        "error_message": str(mcp_error),
                        "mcp_failed": True
                    },
                    "MCP call failed - check server connectivity"
                )
                raise
        
        # Print Pipeline Summary
        print(f"\n🎯 REAL PIPELINE TRANSFORMATION SUMMARY")
        print(f"{'='*80}")
        summary = tracer.get_summary()
        print(f"Total Steps: {summary['total_steps']}")
        print(f"\nPipeline Flow:")
        for i, step_name in enumerate(summary['pipeline_summary'], 1):
            print(f"  {i}. {step_name}")
        
        print(f"\n✅ REAL QUERY TRANSFORMATION TRACE COMPLETED SUCCESSFULLY")
        print(f"⏰ Completed at: {datetime.now().isoformat()}")
        
        return summary
        
    except Exception as e:
        print(f"\n❌ REAL TRACE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main function to run the real query transformation trace."""
    
    # Test query that should trigger search transformation
    test_query = "Find all emails from with keywords invoice or INV-1001 anywhere in subject or body of email, from last month"
    
    print("🔍 Gmail Query Transformation Tracing Tool - REAL MODE")
    print("=" * 80)
    print("This tool traces the complete query transformation pipeline")
    print("using REAL LLM calls and REAL MCP responses (no mocks).")
    print("=" * 80)
    
    # Check environment setup
    print(f"\n🔧 ENVIRONMENT CHECK:")
    os.environ["LLM_PROVIDER"] = "gemini"  # Force Gemini
    llm_provider = os.getenv("LLM_PROVIDER", "gemini")
    print(f"   LLM Provider: {llm_provider}")
    
    api_key_env = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY", 
        "google": "GOOGLE_API_KEY",
        "gemini": "GOOGLE_API_KEY"
    }.get(llm_provider.lower())
    
    api_key = os.getenv(api_key_env) if api_key_env else None
    print(f"   API Key: {'✅ Configured' if api_key else '❌ Missing'}")
    
    if not api_key:
        print(f"\n❌ ERROR: {api_key_env} environment variable not set!")
        print(f"   Please set your API key: export {api_key_env}=your_key_here")
        return
    
    print(f"   MCP Server: http://localhost:9002/mcp")
    print(f"   Mock Mode: ❌ DISABLED (using real calls)")
    
    # Run the trace
    result = await trace_gmail_query_transformation_real(test_query)
    
    if result:
        print(f"\n📊 REAL TRACE STATISTICS:")
        print(f"   - Total transformation steps: {result['total_steps']}")
        print(f"   - Pipeline completed successfully: ✅")
        print(f"   - Used real LLM calls: ✅")
        print(f"   - Used real MCP calls: ✅")
    else:
        print(f"\n💥 REAL TRACE FAILED - Check error messages above")
        sys.exit(1)


if __name__ == "__main__":
    print("Starting REAL Gmail Query Transformation Trace...")
    asyncio.run(main())