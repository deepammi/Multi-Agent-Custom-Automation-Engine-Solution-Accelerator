# LangGraph Refactoring Quick Start Guide

## Overview

This guide provides step-by-step instructions to begin the LangGraph refactoring. Follow these steps to set up your development environment and start Phase 1.

## Prerequisites

- Python 3.10+
- MongoDB or SQLite
- Existing backend running
- Git access to repository

## Step 1: Install Dependencies

```bash
cd backend

# Add to requirements.txt
echo "langgraph>=0.0.40" >> requirements.txt
echo "langchain>=0.1.0" >> requirements.txt
echo "langchain-openai>=0.0.5" >> requirements.txt
echo "langchain-anthropic>=0.1.0" >> requirements.txt

# Install
pip install -r requirements.txt
```

## Step 2: Create Feature Branch

```bash
git checkout -b feature/langgraph-refactor
```

## Step 3: Set Up Checkpointer

### Option A: MongoDB Checkpointer (Recommended)

```python
# backend/app/agents/checkpointer.py
from langgraph.checkpoint.mongodb import MongoDBSaver
from app.db.mongodb import MongoDB
import logging

logger = logging.getLogger(__name__)

_checkpointer = None

def get_checkpointer():
    """Get MongoDB checkpointer for persistent state."""
    global _checkpointer
    
    if _checkpointer is None:
        try:
            db = MongoDB.get_database()
            _checkpointer = MongoDBSaver(
                db=db,
                collection_name="langgraph_checkpoints"
            )
            logger.info("MongoDB checkpointer initialized")
        except Exception as e:
            logger.error(f"Failed to initialize checkpointer: {e}")
            raise
    
    return _checkpointer
```

### Option B: SQLite Checkpointer (Simpler)

```python
# backend/app/agents/checkpointer.py
from langgraph.checkpoint.sqlite import SqliteSaver
import logging

logger = logging.getLogger(__name__)

_checkpointer = None

def get_checkpointer():
    """Get SQLite checkpointer for persistent state."""
    global _checkpointer
    
    if _checkpointer is None:
        _checkpointer = SqliteSaver.from_conn_string("checkpoints.db")
        logger.info("SQLite checkpointer initialized")
    
    return _checkpointer
```

## Step 4: Update State Schema

```python
# backend/app/agents/state.py
from typing import TypedDict, Annotated, Sequence, Any
from langgraph.graph import add_messages

class AgentState(TypedDict):
    """Enhanced state for LangGraph execution."""
    
    # Core fields
    messages: Annotated[Sequence[dict], add_messages]
    plan_id: str
    session_id: str
    task_description: str
    
    # Agent routing
    current_agent: str
    next_agent: str | None
    
    # Execution state
    final_result: str
    iteration_count: int
    execution_history: list[dict]
    
    # HITL state
    approval_required: bool
    approved: bool | None
    clarification_request_id: str | None
    awaiting_user_input: bool
    user_response: str | None
    feedback: str | None
    
    # Extraction state (for invoice agent)
    requires_extraction_approval: bool
    extraction_result: dict | None
    extraction_approved: bool | None
    
    # Configuration
    websocket_manager: Any
    llm_provider: str | None
    llm_temperature: float | None
    
    # Memory
    chat_history: list[dict]
```

## Step 5: Create Router Functions

```python
# backend/app/agents/routers.py
from app.agents.state import AgentState
import logging

logger = logging.getLogger(__name__)


def approval_router(state: AgentState) -> str:
    """Route based on plan approval decision."""
    approved = state.get("approved")
    
    if approved is True:
        logger.info("Plan approved, continuing to agent")
        return "approved"
    elif approved is False:
        logger.info("Plan rejected, ending execution")
        return "rejected"
    else:
        logger.warning("Approval status unclear, defaulting to rejected")
        return "rejected"


def hitl_router(state: AgentState) -> str:
    """Route based on HITL decision (approval vs revision)."""
    user_response = state.get("user_response", "").strip().upper()
    
    # Check for approval keywords
    approval_keywords = ["OK", "YES", "APPROVE", "APPROVED", "LOOKS GOOD", "LGTM"]
    
    if any(keyword in user_response for keyword in approval_keywords):
        logger.info("User approved, completing task")
        return "approved"
    else:
        logger.info("User requested revision, looping back")
        return "revision"


def supervisor_router(state: AgentState) -> str:
    """Route to appropriate specialized agent based on planner decision."""
    next_agent = state.get("next_agent")
    
    valid_agents = ["invoice", "closing", "audit", "salesforce", "zoho"]
    
    if next_agent in valid_agents:
        logger.info(f"Routing to {next_agent} agent")
        return next_agent
    else:
        logger.warning(f"Unknown agent '{next_agent}', defaulting to invoice")
        return "invoice"


def should_use_tools(state: AgentState) -> str:
    """Determine if agent should use tools."""
    # Check if agent needs to call tools
    # This is a placeholder - implement based on agent logic
    needs_tools = state.get("needs_tools", False)
    
    if needs_tools:
        return "tools"
    else:
        return "continue"
```

## Step 6: Create New Graph (Parallel to Old)

```python
# backend/app/agents/graph_v2.py
from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.checkpointer import get_checkpointer
from app.agents.routers import approval_router, hitl_router, supervisor_router
from app.agents.nodes import (
    planner_node,
    invoice_agent_node,
    closing_agent_node,
    audit_agent_node,
)
from app.agents.salesforce_node import salesforce_agent_node
from app.agents.zoho_agent_node import zoho_agent_node
import logging

logger = logging.getLogger(__name__)


def create_approval_node(state: AgentState) -> dict:
    """Approval checkpoint node."""
    logger.info(f"Approval node reached for plan {state['plan_id']}")
    # Just pass through - actual approval handled by interrupt
    return {"approval_required": True}


def create_hitl_node(state: AgentState) -> dict:
    """HITL checkpoint node."""
    logger.info(f"HITL node reached for plan {state['plan_id']}")
    # Increment iteration count
    iteration = state.get("iteration_count", 0) + 1
    return {
        "awaiting_user_input": True,
        "iteration_count": iteration
    }


def create_agent_graph_v2():
    """
    Create LangGraph workflow with proper state management.
    Version 2 - uses checkpointer and interrupts.
    """
    logger.info("Creating LangGraph v2 workflow")
    
    # Get checkpointer
    checkpointer = get_checkpointer()
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("approval", create_approval_node)
    workflow.add_node("invoice", invoice_agent_node)
    workflow.add_node("closing", closing_agent_node)
    workflow.add_node("audit", audit_agent_node)
    workflow.add_node("salesforce", salesforce_agent_node)
    workflow.add_node("zoho", zoho_agent_node)
    workflow.add_node("hitl", create_hitl_node)
    
    # Set entry point
    workflow.set_entry_point("planner")
    
    # Planner → Approval (always)
    workflow.add_edge("planner", "approval")
    
    # Approval → Agent or End (conditional)
    workflow.add_conditional_edges(
        "approval",
        approval_router,
        {
            "approved": supervisor_router,  # Returns agent name
            "rejected": END
        }
    )
    
    # All agents → HITL
    workflow.add_edge("invoice", "hitl")
    workflow.add_edge("closing", "hitl")
    workflow.add_edge("audit", "hitl")
    workflow.add_edge("salesforce", "hitl")
    workflow.add_edge("zoho", "hitl")
    
    # HITL → End or Loop (conditional)
    workflow.add_conditional_edges(
        "hitl",
        hitl_router,
        {
            "approved": END,
            "revision": supervisor_router  # Loop back to agent
        }
    )
    
    # Compile with checkpointer and interrupts
    graph = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["approval", "hitl"]  # Pause for human input
    )
    
    logger.info("LangGraph v2 workflow created successfully")
    return graph


# Create singleton instance
_agent_graph_v2 = None

def get_agent_graph_v2():
    """Get or create agent graph v2."""
    global _agent_graph_v2
    if _agent_graph_v2 is None:
        _agent_graph_v2 = create_agent_graph_v2()
    return _agent_graph_v2
```

## Step 7: Create Parallel Service (Feature Flag)

```python
# backend/app/services/agent_service_v2.py
import logging
import os
from typing import Dict, Any
from datetime import datetime

from app.agents.graph_v2 import get_agent_graph_v2
from app.agents.state import AgentState
from app.db.repositories import PlanRepository
from app.services.websocket_service import websocket_manager

logger = logging.getLogger(__name__)


class AgentServiceV2:
    """Agent service using LangGraph v2."""
    
    @staticmethod
    async def execute_task(
        plan_id: str,
        session_id: str,
        task_description: str,
        require_hitl: bool = True
    ) -> Dict[str, Any]:
        """Execute task using LangGraph v2."""
        logger.info(f"[V2] Executing task for plan {plan_id}")
        
        # Update plan status
        await PlanRepository.update_status(plan_id, "in_progress")
        
        # Create initial state
        initial_state: AgentState = {
            "messages": [],
            "plan_id": plan_id,
            "session_id": session_id,
            "task_description": task_description,
            "current_agent": "",
            "next_agent": None,
            "final_result": "",
            "iteration_count": 0,
            "execution_history": [],
            "approval_required": False,
            "approved": None,
            "clarification_request_id": None,
            "awaiting_user_input": False,
            "user_response": None,
            "feedback": None,
            "requires_extraction_approval": False,
            "extraction_result": None,
            "extraction_approved": None,
            "websocket_manager": websocket_manager,
            "llm_provider": None,
            "llm_temperature": None,
            "chat_history": []
        }
        
        # Get graph
        graph = get_agent_graph_v2()
        
        # Create thread ID for this execution
        thread_id = f"plan_{plan_id}"
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # Invoke graph - will stop at first interrupt (approval)
            result = await graph.ainvoke(initial_state, config)
            
            logger.info(f"[V2] Graph stopped at approval for plan {plan_id}")
            
            # Send approval request via WebSocket
            # (Similar to old implementation)
            await AgentServiceV2._send_approval_request(plan_id, result)
            
            # Update plan status
            await PlanRepository.update_status(plan_id, "pending_approval")
            
            return {
                "status": "pending_approval",
                "thread_id": thread_id
            }
            
        except Exception as e:
            logger.error(f"[V2] Task execution failed for plan {plan_id}: {e}")
            await PlanRepository.update_status(plan_id, "failed")
            raise
    
    @staticmethod
    async def resume_after_approval(
        plan_id: str,
        approved: bool,
        feedback: str = None
    ) -> Dict[str, Any]:
        """Resume execution after approval."""
        logger.info(f"[V2] Resuming plan {plan_id} with approval={approved}")
        
        thread_id = f"plan_{plan_id}"
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # Get graph
            graph = get_agent_graph_v2()
            
            # Get current state
            state = await graph.aget_state(config)
            
            # Update state with approval decision
            state.values["approved"] = approved
            if feedback:
                state.values["feedback"] = feedback
            
            if not approved:
                # Plan rejected
                await PlanRepository.update_status(plan_id, "rejected")
                return {"status": "rejected"}
            
            # Resume execution - will stop at next interrupt (HITL)
            await PlanRepository.update_status(plan_id, "in_progress")
            result = await graph.ainvoke(None, config)
            
            logger.info(f"[V2] Graph stopped at HITL for plan {plan_id}")
            
            # Send HITL request via WebSocket
            await AgentServiceV2._send_hitl_request(plan_id, result)
            
            # Update plan status
            await PlanRepository.update_status(plan_id, "pending_clarification")
            
            return {
                "status": "pending_clarification",
                "thread_id": thread_id
            }
            
        except Exception as e:
            logger.error(f"[V2] Resume failed for plan {plan_id}: {e}")
            await PlanRepository.update_status(plan_id, "failed")
            raise
    
    @staticmethod
    async def handle_user_clarification(
        plan_id: str,
        answer: str
    ) -> Dict[str, Any]:
        """Handle user clarification."""
        logger.info(f"[V2] Processing clarification for plan {plan_id}")
        
        thread_id = f"plan_{plan_id}"
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # Get graph
            graph = get_agent_graph_v2()
            
            # Get current state
            state = await graph.aget_state(config)
            
            # Update state with user response
            state.values["user_response"] = answer
            
            # Resume execution
            await PlanRepository.update_status(plan_id, "in_progress")
            result = await graph.ainvoke(None, config)
            
            # Check if we're done or looping
            if result.get("awaiting_user_input"):
                # Looped back for another revision
                logger.info(f"[V2] Looping back for revision, plan {plan_id}")
                
                await AgentServiceV2._send_hitl_request(plan_id, result)
                await PlanRepository.update_status(plan_id, "pending_clarification")
                
                return {
                    "status": "pending_clarification",
                    "iteration": result.get("iteration_count", 0)
                }
            else:
                # Completed
                logger.info(f"[V2] Task completed, plan {plan_id}")
                
                await PlanRepository.update_status(plan_id, "completed")
                
                return {
                    "status": "completed",
                    "result": result.get("final_result")
                }
                
        except Exception as e:
            logger.error(f"[V2] Clarification handling failed for plan {plan_id}: {e}")
            await PlanRepository.update_status(plan_id, "failed")
            raise
    
    @staticmethod
    async def _send_approval_request(plan_id: str, state: dict):
        """Send approval request via WebSocket."""
        # Implementation similar to old version
        pass
    
    @staticmethod
    async def _send_hitl_request(plan_id: str, state: dict):
        """Send HITL clarification request via WebSocket."""
        # Implementation similar to old version
        pass
```

## Step 8: Add Feature Flag

```python
# backend/.env
USE_LANGGRAPH_V2=false  # Set to true to enable new implementation
```

```python
# backend/app/api/v3/routes.py
import os
from app.services.agent_service import AgentService
from app.services.agent_service_v2 import AgentServiceV2

USE_LANGGRAPH_V2 = os.getenv("USE_LANGGRAPH_V2", "false").lower() == "true"

@router.post("/process_request")
async def process_request(request: ProcessRequestInput):
    """Process user request."""
    
    if USE_LANGGRAPH_V2:
        # Use new LangGraph implementation
        result = await AgentServiceV2.execute_task(...)
    else:
        # Use old implementation
        result = await AgentService.execute_task(...)
    
    return result
```

## Step 9: Test Basic Flow

```python
# backend/test_langgraph_v2.py
import asyncio
from app.services.agent_service_v2 import AgentServiceV2
from app.db.mongodb import MongoDB

async def test_basic_flow():
    """Test basic LangGraph v2 flow."""
    
    # Connect to database
    await MongoDB.connect()
    
    try:
        # Execute task
        print("1. Executing task...")
        result1 = await AgentServiceV2.execute_task(
            plan_id="test-lg-1",
            session_id="session-1",
            task_description="Test LangGraph v2"
        )
        print(f"   Status: {result1['status']}")
        assert result1["status"] == "pending_approval"
        
        # Approve
        print("2. Approving plan...")
        result2 = await AgentServiceV2.resume_after_approval(
            plan_id="test-lg-1",
            approved=True
        )
        print(f"   Status: {result2['status']}")
        assert result2["status"] == "pending_clarification"
        
        # Approve final
        print("3. Approving final result...")
        result3 = await AgentServiceV2.handle_user_clarification(
            plan_id="test-lg-1",
            answer="OK"
        )
        print(f"   Status: {result3['status']}")
        assert result3["status"] == "completed"
        
        print("\n✅ All tests passed!")
        
    finally:
        await MongoDB.disconnect()

if __name__ == "__main__":
    asyncio.run(test_basic_flow())
```

Run the test:
```bash
cd backend
python3 test_langgraph_v2.py
```

## Step 10: Visualize with LangGraph Studio (Optional)

```bash
# Install LangGraph Studio
pip install langgraph-studio

# Export graph
python3 -c "from app.agents.graph_v2 import get_agent_graph_v2; graph = get_agent_graph_v2(); graph.get_graph().draw_mermaid_png(output_file_path='graph.png')"

# View graph.png
```

## Next Steps

1. ✅ Complete Phase 1 setup
2. Test with simple tasks
3. Compare behavior with old implementation
4. Gradually enable for more users
5. Monitor performance and errors
6. Proceed to Phase 2 (full graph refactoring)

## Troubleshooting

### Issue: Checkpointer connection fails
**Solution**: Check MongoDB connection string, ensure database is running

### Issue: Graph doesn't stop at interrupts
**Solution**: Verify `interrupt_before` parameter in `compile()`

### Issue: State not persisting
**Solution**: Check checkpointer is properly initialized and connected

### Issue: Import errors
**Solution**: Ensure all dependencies installed: `pip install -r requirements.txt`

## Resources

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Checkpointer Guide](https://python.langchain.com/docs/langgraph/checkpointing)
- [HITL Tutorial](https://python.langchain.com/docs/langgraph/how-tos/human_in_the_loop)

---

**Ready to start?** Follow these steps and you'll have a working LangGraph v2 implementation running in parallel with your existing system!
