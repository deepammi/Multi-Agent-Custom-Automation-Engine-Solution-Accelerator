"""API v3 routes."""
import logging
import uuid
from typing import List, Optional
import asyncio

from fastapi import APIRouter, Query, HTTPException, BackgroundTasks

from app.models.plan import Plan, PlanResponse, ProcessRequestInput, ProcessRequestResponse, Step
from app.models.message import AgentMessage
from app.models.team import TeamConfiguration
from app.models.approval import PlanApprovalRequest, PlanApprovalResponse
from app.db.repositories import PlanRepository, MessageRepository
from app.services.agent_service import AgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v3", tags=["v3"])


@router.post("/process_request", response_model=ProcessRequestResponse)
async def process_request(request: ProcessRequestInput, background_tasks: BackgroundTasks):
    """
    Process a new task request and create a plan.
    Phase 3: Integrates with LangGraph agent execution.
    """
    logger.info(f"Processing request: {request.description[:50]}...")
    
    # Generate IDs
    plan_id = str(uuid.uuid4())
    session_id = request.session_id or str(uuid.uuid4())
    
    # Create plan with steps
    plan = Plan(
        id=plan_id,
        session_id=session_id,
        description=request.description,
        status="pending",
        steps=[
            Step(
                id=f"{plan_id}-step-1",
                description="Analyze task requirements",
                agent="Planner",
                status="pending"
            ),
            Step(
                id=f"{plan_id}-step-2",
                description="Execute task",
                agent="Invoice",
                status="pending"
            )
        ]
    )
    
    # Save to database
    await PlanRepository.create(plan)
    
    # Execute agent workflow in background
    background_tasks.add_task(
        AgentService.execute_task,
        plan_id,
        session_id,
        request.description
    )
    
    return ProcessRequestResponse(
        plan_id=plan_id,
        status="created",
        session_id=session_id
    )


@router.get("/plans", response_model=List[PlanResponse])
async def get_plans(session_id: Optional[str] = Query(None)):
    """
    Get all plans, optionally filtered by session_id.
    """
    logger.info(f"Getting plans for session: {session_id}")
    plans = await PlanRepository.get_all(session_id=session_id)
    return [PlanResponse.from_plan(plan) for plan in plans]


@router.get("/plan")
async def get_plan(plan_id: str = Query(...)):
    """
    Get a single plan by ID with messages.
    """
    logger.info(f"Getting plan: {plan_id}")
    
    plan = await PlanRepository.get_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    messages = await MessageRepository.get_by_plan_id(plan_id)
    
    return {
        "plan": PlanResponse.from_plan(plan),
        "messages": messages,
        "m_plan": None,
        "team": None,
        "streaming_message": None
    }


@router.post("/plan_approval", response_model=PlanApprovalResponse)
async def plan_approval(request: PlanApprovalRequest, background_tasks: BackgroundTasks):
    """
    Handle plan approval/rejection.
    Phase 6: Resumes or stops execution based on approval.
    """
    logger.info(f"Plan approval request for {request.m_plan_id}: approved={request.approved}")
    
    # Resume execution with approval decision
    background_tasks.add_task(
        AgentService.resume_after_approval,
        request.m_plan_id,
        request.approved,
        request.feedback
    )
    
    return PlanApprovalResponse(
        status="processing",
        message="Approval received, resuming execution"
    )


@router.post("/user_clarification")
async def user_clarification(request: dict, background_tasks: BackgroundTasks):
    """
    Handle user clarification responses.
    Phase 7: Processes approval vs revision and loops back if needed.
    """
    logger.info(f"User clarification received for plan {request.get('plan_id')}")
    
    plan_id = request.get("plan_id")
    request_id = request.get("request_id", "")
    answer = request.get("answer", "")
    
    if not plan_id:
        raise HTTPException(status_code=400, detail="plan_id is required")
    
    # Process clarification in background
    background_tasks.add_task(
        AgentService.handle_user_clarification,
        plan_id,
        request_id,
        answer
    )
    
    return {
        "status": "processing",
        "session_id": request.get("session_id", str(uuid.uuid4()))
    }


@router.post("/agent_message")
async def agent_message(request: dict):
    """
    Store agent messages.
    """
    logger.info(f"Agent message received: {request.get('agent')}")
    
    message = AgentMessage(
        plan_id=request.get("plan_id", ""),
        agent_name=request.get("agent", "Unknown"),
        agent_type=request.get("agent_type", "unknown"),
        content=request.get("content", "")
    )
    
    await MessageRepository.create(message)
    return message.dict()


@router.get("/teams")
async def get_teams():
    """
    Get available team configurations.
    Phase 8: Will return actual team configurations.
    """
    logger.info("Getting teams")
    return []


@router.get("/init_team")
async def init_team(team_switched: bool = Query(False)):
    """
    Initialize a team.
    Phase 8: Will handle team initialization.
    """
    logger.info(f"Initializing team (switched: {team_switched})")
    return {
        "status": "initialized",
        "team_id": str(uuid.uuid4())
    }
