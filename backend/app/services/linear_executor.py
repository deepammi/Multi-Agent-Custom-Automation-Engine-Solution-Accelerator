"""Linear Workflow Executor for managing sequential agent execution."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from langgraph.graph import StateGraph
from app.agents.state import AgentState
from app.services.websocket_service import WebSocketManager
from app.services.hitl_interface import HITLInterface
from app.services.error_handler import WorkflowErrorHandler, ErrorSeverity
from app.services.workflow_stability_monitor import WorkflowStabilityMonitor

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of workflow execution."""
    success: bool
    final_state: Optional[AgentState]
    error: Optional[str]
    execution_time: float
    completed_agents: List[str]
    failed_agent: Optional[str]


@dataclass
class ExecutionConfig:
    """Configuration for workflow execution."""
    global_timeout: int = 900  # 15 minutes in seconds
    agent_timeout: int = 180   # 3 minutes per agent in seconds
    max_concurrent_workflows: int = 10
    enable_progress_updates: bool = True
    enable_timeout_warnings: bool = True


class LinearExecutor:
    """
    Linear Workflow Executor for managing sequential agent execution.
    
    This class manages the execution of LangGraph workflows with:
    - Progress tracking and WebSocket status updates
    - Timeout management (15-minute global, 3-minute per agent)
    - Concurrent workflow limits (10 per user)
    - Error handling and graceful termination
    - Integration with HITL approval system
    """
    
    def __init__(
        self,
        websocket_manager: WebSocketManager,
        hitl_interface: HITLInterface,
        config: Optional[ExecutionConfig] = None,
        error_handler: Optional[WorkflowErrorHandler] = None,
        stability_monitor: Optional[WorkflowStabilityMonitor] = None
    ):
        self.websocket_manager = websocket_manager
        self.hitl_interface = hitl_interface
        self.config = config or ExecutionConfig()
        self.error_handler = error_handler
        self.stability_monitor = stability_monitor
        
        # Track active workflows per user
        self._active_workflows: Dict[str, List[str]] = {}  # user_id -> [plan_ids]
        self._workflow_start_times: Dict[str, datetime] = {}  # plan_id -> start_time
        self._workflow_tasks: Dict[str, asyncio.Task] = {}  # plan_id -> task
        
        logger.info("LinearExecutor initialized with config: %s", self.config)
    
    async def execute_workflow(
        self,
        graph: StateGraph,
        initial_state: AgentState,
        user_id: str
    ) -> ExecutionResult:
        """
        Execute agents in predetermined linear sequence.
        
        Args:
            graph: Compiled LangGraph with linear connections
            initial_state: Initial workflow state
            user_id: User identifier for concurrency limits
            
        Returns:
            ExecutionResult with success status and final state
        """
        plan_id = initial_state["plan_id"]
        start_time = datetime.utcnow()
        
        logger.info(f"Starting linear workflow execution for plan {plan_id}")
        
        try:
            # Check stability monitor approval
            if self.stability_monitor:
                if not await self.stability_monitor.record_workflow_start(plan_id, user_id):
                    return ExecutionResult(
                        success=False,
                        final_state=None,
                        error="Workflow blocked by stability monitor",
                        execution_time=0.0,
                        completed_agents=[],
                        failed_agent=None
                    )
            
            # Check concurrent workflow limits
            if not await self._check_concurrency_limits(user_id, plan_id):
                return ExecutionResult(
                    success=False,
                    final_state=None,
                    error=f"Concurrent workflow limit exceeded ({self.config.max_concurrent_workflows})",
                    execution_time=0.0,
                    completed_agents=[],
                    failed_agent=None
                )
            
            # Register workflow
            await self._register_workflow(user_id, plan_id, start_time)
            
            # Execute with timeout
            execution_task = asyncio.create_task(
                self._execute_with_progress_tracking(graph, initial_state)
            )
            self._workflow_tasks[plan_id] = execution_task
            
            try:
                result = await asyncio.wait_for(
                    execution_task,
                    timeout=self.config.global_timeout
                )
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"Workflow {plan_id} completed successfully in {execution_time:.2f}s")
                
                # Record success in stability monitor
                if self.stability_monitor:
                    await self.stability_monitor.record_workflow_success(plan_id, execution_time)
                
                return ExecutionResult(
                    success=True,
                    final_state=result,
                    error=None,
                    execution_time=execution_time,
                    completed_agents=result.get("completed_agents", []),
                    failed_agent=None
                )
                
            except asyncio.TimeoutError:
                logger.warning(f"Workflow {plan_id} timed out after {self.config.global_timeout}s")
                execution_task.cancel()
                
                await self._send_timeout_notification(plan_id)
                
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Handle timeout with error handler and stability monitor
                if self.error_handler:
                    await self.error_handler.handle_workflow_timeout(
                        plan_id=plan_id,
                        timeout_duration=self.config.global_timeout,
                        user_id=user_id,
                        context={"execution_time": execution_time}
                    )
                
                if self.stability_monitor:
                    await self.stability_monitor.record_workflow_failure(
                        plan_id, ErrorSeverity.HIGH, execution_time
                    )
                
                return ExecutionResult(
                    success=False,
                    final_state=None,
                    error=f"Workflow timed out after {self.config.global_timeout} seconds",
                    execution_time=execution_time,
                    completed_agents=[],
                    failed_agent="timeout"
                )
                
        except Exception as e:
            logger.error(f"Workflow {plan_id} failed with error: {str(e)}")
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Handle error with comprehensive error handling
            if self.error_handler:
                await self.error_handler.handle_system_error(
                    plan_id=plan_id,
                    error=e,
                    user_id=user_id,
                    context={"execution_time": execution_time}
                )
            else:
                # Fallback to original error handling
                await self.handle_agent_failure(plan_id, "execution", e)
            
            if self.stability_monitor:
                error_severity = ErrorSeverity.CRITICAL if isinstance(e, (SystemError, MemoryError)) else ErrorSeverity.HIGH
                await self.stability_monitor.record_workflow_failure(
                    plan_id, error_severity, execution_time
                )
            
            return ExecutionResult(
                success=False,
                final_state=None,
                error=str(e),
                execution_time=execution_time,
                completed_agents=[],
                failed_agent="execution"
            )
            
        finally:
            # Clean up workflow tracking
            await self._unregister_workflow(user_id, plan_id)
    
    async def _execute_with_progress_tracking(
        self,
        graph: StateGraph,
        initial_state: AgentState
    ) -> AgentState:
        """
        Execute workflow with progress tracking and WebSocket updates.
        
        Args:
            graph: Compiled LangGraph
            initial_state: Initial state
            
        Returns:
            Final workflow state
        """
        plan_id = initial_state["plan_id"]
        agent_sequence = initial_state.get("agent_sequence", [])
        total_steps = len(agent_sequence)
        
        # Initialize progress tracking
        current_state = initial_state.copy()
        current_state["total_steps"] = total_steps
        current_state["current_step"] = 0
        current_state["completed_agents"] = []
        
        logger.info(f"Executing workflow {plan_id} with {total_steps} agents: {agent_sequence}")
        
        # Send workflow start notification
        await self._send_progress_update(
            plan_id, 0, total_steps, "workflow", "Workflow execution started"
        )
        
        # Execute the graph
        config = {"configurable": {"thread_id": plan_id}}
        
        try:
            # Stream execution results
            async for event in graph.astream(current_state, config=config):
                logger.debug(f"Graph event for {plan_id}: {event}")
                
                # Update progress based on agent completion
                if isinstance(event, dict):
                    for node_name, node_result in event.items():
                        if node_name != "__end__" and isinstance(node_result, dict):
                            # Agent completed
                            completed_agents = current_state.get("completed_agents", [])
                            if node_name not in completed_agents:
                                completed_agents.append(node_name)
                                current_state["completed_agents"] = completed_agents
                                current_state["current_step"] = len(completed_agents)
                                current_state["current_agent"] = node_name
                                
                                # Send progress update
                                await self._send_progress_update(
                                    plan_id,
                                    len(completed_agents),
                                    total_steps,
                                    node_name,
                                    f"Agent {node_name} completed"
                                )
                            
                            # Update state with agent results
                            current_state.update(node_result)
            
            # Send completion notification
            await self._send_progress_update(
                plan_id, total_steps, total_steps, "workflow", "Workflow execution completed"
            )
            
            return current_state
            
        except Exception as e:
            logger.error(f"Graph execution failed for {plan_id}: {str(e)}")
            
            # Handle graph execution error
            if self.error_handler:
                await self.error_handler.handle_agent_failure(
                    plan_id=plan_id,
                    agent_name=current_state.get("current_agent", "unknown"),
                    error=e,
                    context={"execution_phase": "graph_execution"}
                )
            
            raise
    
    async def handle_agent_failure(self, plan_id: str, agent: str, error: Exception) -> None:
        """
        Handle agent failures gracefully.
        
        Args:
            plan_id: Plan identifier
            agent: Failed agent name
            error: Exception that caused the failure
        """
        logger.error(f"Agent {agent} failed in workflow {plan_id}: {str(error)}")
        
        # Send failure notification via WebSocket
        await self.websocket_manager.send_message(plan_id, {
            "type": "agent_failure",
            "data": {
                "agent_name": agent,
                "error": str(error),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "status": "failed"
            }
        })
        
        # Notify HITL about the failure
        try:
            await self.hitl_interface.send_error_notification(
                plan_id=plan_id,
                agent_name=agent,
                error_message=str(error),
                error_type=type(error).__name__
            )
        except Exception as hitl_error:
            logger.error(f"Failed to send HITL error notification: {str(hitl_error)}")
        
        # Log failure for monitoring
        logger.info(f"Workflow {plan_id} terminated due to agent {agent} failure")
    
    async def _check_concurrency_limits(self, user_id: str, plan_id: str) -> bool:
        """
        Check if user has exceeded concurrent workflow limits.
        
        Args:
            user_id: User identifier
            plan_id: Plan identifier
            
        Returns:
            True if within limits, False otherwise
        """
        user_workflows = self._active_workflows.get(user_id, [])
        
        # Clean up completed workflows
        active_workflows = []
        for workflow_plan_id in user_workflows:
            if workflow_plan_id in self._workflow_tasks:
                task = self._workflow_tasks[workflow_plan_id]
                if not task.done():
                    active_workflows.append(workflow_plan_id)
        
        self._active_workflows[user_id] = active_workflows
        
        # Check limit
        if len(active_workflows) >= self.config.max_concurrent_workflows:
            logger.warning(
                f"User {user_id} exceeded concurrent workflow limit: "
                f"{len(active_workflows)}/{self.config.max_concurrent_workflows}"
            )
            return False
        
        return True
    
    async def _register_workflow(self, user_id: str, plan_id: str, start_time: datetime) -> None:
        """Register workflow for tracking."""
        if user_id not in self._active_workflows:
            self._active_workflows[user_id] = []
        
        self._active_workflows[user_id].append(plan_id)
        self._workflow_start_times[plan_id] = start_time
        
        logger.info(f"Registered workflow {plan_id} for user {user_id}")
    
    async def _unregister_workflow(self, user_id: str, plan_id: str) -> None:
        """Unregister workflow and clean up resources."""
        # Remove from active workflows
        if user_id in self._active_workflows:
            if plan_id in self._active_workflows[user_id]:
                self._active_workflows[user_id].remove(plan_id)
        
        # Clean up tracking data
        self._workflow_start_times.pop(plan_id, None)
        
        # Clean up task reference
        if plan_id in self._workflow_tasks:
            task = self._workflow_tasks.pop(plan_id)
            if not task.done():
                task.cancel()
        
        logger.info(f"Unregistered workflow {plan_id} for user {user_id}")
    
    async def _send_progress_update(
        self,
        plan_id: str,
        current_step: int,
        total_steps: int,
        agent: str,
        message: str
    ) -> None:
        """
        Send progress update via WebSocket.
        
        Args:
            plan_id: Plan identifier
            current_step: Current step number
            total_steps: Total number of steps
            agent: Current agent name
            message: Progress message
        """
        if not self.config.enable_progress_updates:
            return
        
        try:
            await self.websocket_manager.send_message(plan_id, {
                "type": "progress_update",
                "data": {
                    "current_step": current_step,
                    "total_steps": total_steps,
                    "agent_name": agent,
                    "message": message,
                    "progress_percentage": (current_step / total_steps * 100) if total_steps > 0 else 0,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            })
        except Exception as e:
            logger.error(f"Failed to send progress update for {plan_id}: {str(e)}")
    
    async def _send_timeout_notification(self, plan_id: str) -> None:
        """Send timeout notification via WebSocket."""
        try:
            await self.websocket_manager.send_message(plan_id, {
                "type": "workflow_timeout",
                "data": {
                    "message": f"Workflow timed out after {self.config.global_timeout} seconds",
                    "timeout_seconds": self.config.global_timeout,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            })
        except Exception as e:
            logger.error(f"Failed to send timeout notification for {plan_id}: {str(e)}")
    
    def get_active_workflows(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about active workflows.
        
        Args:
            user_id: Optional user filter
            
        Returns:
            Dictionary with workflow information
        """
        if user_id:
            user_workflows = self._active_workflows.get(user_id, [])
            return {
                "user_id": user_id,
                "active_count": len(user_workflows),
                "workflows": user_workflows,
                "limit": self.config.max_concurrent_workflows
            }
        else:
            total_workflows = sum(len(workflows) for workflows in self._active_workflows.values())
            return {
                "total_active_workflows": total_workflows,
                "users_with_active_workflows": len(self._active_workflows),
                "workflows_by_user": {
                    user_id: len(workflows) 
                    for user_id, workflows in self._active_workflows.items()
                }
            }
    
    def get_workflow_stats(self) -> Dict[str, Any]:
        """
        Get workflow execution statistics.
        
        Returns:
            Dictionary with execution statistics
        """
        now = datetime.utcnow()
        
        # Calculate running times for active workflows
        running_times = []
        for plan_id, start_time in self._workflow_start_times.items():
            if plan_id in self._workflow_tasks and not self._workflow_tasks[plan_id].done():
                running_time = (now - start_time).total_seconds()
                running_times.append(running_time)
        
        return {
            "active_workflows": len(self._workflow_tasks),
            "average_running_time": sum(running_times) / len(running_times) if running_times else 0,
            "longest_running_time": max(running_times) if running_times else 0,
            "config": {
                "global_timeout": self.config.global_timeout,
                "agent_timeout": self.config.agent_timeout,
                "max_concurrent_workflows": self.config.max_concurrent_workflows
            }
        }