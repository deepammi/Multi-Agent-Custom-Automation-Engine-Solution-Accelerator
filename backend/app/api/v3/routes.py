"""API v3 routes."""
import logging
import uuid
from datetime import datetime
from typing import List, Optional
import asyncio

from fastapi import APIRouter, Query, HTTPException, BackgroundTasks, File, UploadFile

from app.models.plan import Plan, PlanResponse, ProcessRequestInput, ProcessRequestResponse, Step
from app.models.message import AgentMessage
from app.models.team import TeamConfiguration
from app.models.approval import PlanApprovalRequest, PlanApprovalResponse
from app.db.repositories import PlanRepository, MessageRepository
from app.services.agent_service_refactored import AgentServiceRefactored
from app.services.langgraph_service import LangGraphService
from app.services.ai_planner_service import AIPlanner
from app.services.llm_service import LLMService
from app.services.file_parser_service import FileParserService
from app.services.workflow_context_service import WorkflowStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v3", tags=["v3"])


@router.post("/process_request", response_model=ProcessRequestResponse)
async def process_request(request: ProcessRequestInput, background_tasks: BackgroundTasks):
    """
    Process a new task request and create a plan.
    Updated for Task 10: Integrates workflow context service for execution tracking.
    """
    logger.info(f"Processing request with workflow context: {request.description[:50]}...")
    
    # Generate IDs
    plan_id = str(uuid.uuid4())
    session_id = request.session_id or str(uuid.uuid4())
    
    # Use AI Planner to generate agent sequence
    from app.services.ai_planner_service import AIPlanner
    from app.services.llm_service import LLMService
    from app.services.workflow_context_service import get_workflow_context_service
    
    try:
        # Initialize AI Planner
        llm_service = LLMService()
        ai_planner = AIPlanner(llm_service)
        
        # Generate AI-driven workflow plan
        planning_summary = await ai_planner.plan_workflow(request.description)
        
        if planning_summary.success:
            agent_sequence = planning_summary.agent_sequence.agents
            logger.info(f"AI Planner generated sequence: {' → '.join(agent_sequence)}")
        else:
            # Use fallback sequence
            fallback_sequence = ai_planner.get_fallback_sequence(request.description)
            agent_sequence = fallback_sequence.agents
            logger.warning(f"AI Planner failed, using fallback: {' → '.join(agent_sequence)}")
        
        # Create workflow context for tracking
        workflow_context_service = get_workflow_context_service()
        workflow_context = workflow_context_service.create_workflow_context(
            plan_id=plan_id,
            session_id=session_id,
            task_description=request.description,
            agent_sequence=agent_sequence
        )
        
        # Create plan steps from AI-generated sequence
        steps = []
        for i, agent in enumerate(agent_sequence):
            steps.append(Step(
                id=f"{plan_id}-step-{i+1}",
                description=f"Execute {agent.capitalize()} agent",
                agent=agent.capitalize(),
                status="pending"
            ))
        
    except Exception as e:
        logger.error(f"AI Planner failed: {e}, using default sequence")
        # Fallback to default sequence
        agent_sequence = ["planner", "invoice"]
        
        # Create workflow context for fallback
        workflow_context_service = get_workflow_context_service()
        workflow_context = workflow_context_service.create_workflow_context(
            plan_id=plan_id,
            session_id=session_id,
            task_description=request.description,
            agent_sequence=agent_sequence
        )
        
        # Add error event to workflow context
        workflow_context_service.add_event(
            plan_id,
            "ai_planner_fallback",
            message=f"AI Planner failed: {str(e)}, using fallback sequence"
        )
        
        steps = [
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
    
    # Create plan with AI-generated or fallback steps
    plan = Plan(
        id=plan_id,
        session_id=session_id,
        description=request.description,
        status="pending",
        steps=steps
    )
    
    # Save to database
    await PlanRepository.create(plan)
    
    # Update workflow context status
    workflow_context_service.update_workflow_status(
        plan_id,
        WorkflowStatus.PLANNING,
        "Plan created, starting execution"
    )
    
    # Execute using new LangGraphService with AI Planner
    # IMPORTANT: Start execution in background but allow WebSocket coordination
    from app.services.langgraph_service import LangGraphService
    from app.services.websocket_service import get_websocket_manager
    websocket_manager = get_websocket_manager()
    
    # Store the task for delayed execution until WebSocket connects
    websocket_manager.register_pending_task(
        plan_id=plan_id,
        task_func=LangGraphService.execute_task_with_ai_planner,
        task_args=(plan_id, session_id, request.description, websocket_manager)
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
    Updated for Task 4.1: Uses MessagePersistenceService to retrieve messages from database.
    """
    logger.info(f"Getting plan: {plan_id}")
    
    plan = await PlanRepository.get_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Use MessagePersistenceService to retrieve messages from database
    from app.services.message_persistence_service import get_message_persistence_service
    message_persistence_service = get_message_persistence_service()
    messages = await message_persistence_service.get_messages_for_plan(plan_id)
    
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
    Handle plan approval/rejection with workflow context integration.
    Updated for Task 10: Integrates workflow context service with existing plan approval.
    Supports both plan approval and final approval using the same endpoint.
    """
    logger.info(f"Plan approval request for {request.m_plan_id}: approved={request.approved}")
    
    # Integrate workflow context service
    from app.services.workflow_context_service import get_workflow_context_service
    from app.services.plan_approval_service import get_plan_approval_service
    
    try:
        workflow_context_service = get_workflow_context_service()
        plan_approval_service = get_plan_approval_service()
        
        # Get workflow context to determine approval type
        context = workflow_context_service.get_workflow_context(request.m_plan_id)
        
        # Determine if this is plan approval or final approval based on context
        is_final_approval = (
            context and 
            context.status.value in ["executing", "awaiting_final_approval"]
        )
        
        if is_final_approval:
            # Handle final results approval using workflow context
            logger.info(f"Processing final approval for plan {request.m_plan_id}")
            
            # Update workflow context with final approval
            workflow_context_service.set_final_approval(
                request.m_plan_id,
                request.approved,
                request.feedback or ""
            )
            
            if request.approved:
                # Final results approved - complete workflow
                await PlanRepository.update_status(request.m_plan_id, "completed")
                
                # Send completion message via WebSocket
                from app.services.websocket_service import get_websocket_manager
                websocket_manager = get_websocket_manager()
                await websocket_manager.send_message(request.m_plan_id, {
                    "type": "final_result_message",
                    "data": {
                        "content": "Task completed successfully. Final results approved by user.",
                        "status": "completed",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                })
                
                return PlanApprovalResponse(
                    status="completed",
                    message="Final results approved, task completed"
                )
            else:
                # Final results rejected - user wants to restart
                await PlanRepository.update_status(request.m_plan_id, "restarted")
                
                # Send restart message via WebSocket
                from app.services.websocket_service import get_websocket_manager
                websocket_manager = get_websocket_manager()
                await websocket_manager.send_message(request.m_plan_id, {
                    "type": "final_result_message",
                    "data": {
                        "content": f"User requested workflow restart. {request.feedback or 'Please submit a new task.'}",
                        "status": "restarted",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                })
                
                return PlanApprovalResponse(
                    status="restarted",
                    message="Workflow restart requested. Please submit a new task."
                )
        
        else:
            # Handle plan approval using existing service with workflow context integration
            logger.info(f"Processing plan approval for plan {request.m_plan_id}")
            
            # Update workflow context with plan approval
            workflow_context_service.set_plan_approval(
                request.m_plan_id,
                request.approved,
                request.feedback or ""
            )
            
            # Use existing plan approval service
            response = await plan_approval_service.handle_plan_approval_response(
                plan_id=request.m_plan_id,
                approved=request.approved,
                feedback=request.feedback
            )
            
            if response["status"] == "approved":
                # Plan approved - resume execution
                logger.info(f"Plan {request.m_plan_id} approved")
                
                # Resume execution using LangGraphService
                from app.services.langgraph_service import LangGraphService
                updates = {
                    "plan_approved": True,
                    "hitl_feedback": request.feedback or "Plan approved"
                }
                
                background_tasks.add_task(
                    LangGraphService.resume_execution,
                    request.m_plan_id,
                    updates
                )
                
                return PlanApprovalResponse(
                    status="processing",
                    message="Plan approved, resuming execution"
                )
                
            elif response["status"] == "rejected":
                # Plan rejected
                logger.info(f"Plan {request.m_plan_id} rejected")
                
                return PlanApprovalResponse(
                    status="rejected",
                    message=f"Plan rejected. {response.get('feedback', '')}"
                )
                
            else:
                # Error occurred
                logger.error(f"Plan approval service error: {response.get('error', 'Unknown error')}")
                
                return PlanApprovalResponse(
                    status="error",
                    message=f"Approval processing failed: {response.get('error', 'Unknown error')}"
                )
            
    except Exception as e:
        logger.error(f"Plan approval handling failed: {e}")
        
        # Fallback to simple approval logic with workflow context
        try:
            workflow_context_service = get_workflow_context_service()
            
            if request.approved:
                # Update workflow context and plan status
                workflow_context_service.set_plan_approval(request.m_plan_id, True, request.feedback or "")
                await PlanRepository.update_status(request.m_plan_id, "approved")
                
                # Resume execution using LangGraphService
                from app.services.langgraph_service import LangGraphService
                updates = {
                    "plan_approved": True,
                    "hitl_feedback": request.feedback or "Plan approved"
                }
                
                background_tasks.add_task(
                    LangGraphService.resume_execution,
                    request.m_plan_id,
                    updates
                )
                
                return PlanApprovalResponse(
                    status="processing",
                    message="Plan approved (fallback), resuming execution"
                )
            else:
                # Update workflow context and plan status
                workflow_context_service.set_plan_approval(request.m_plan_id, False, request.feedback or "")
                await PlanRepository.update_status(request.m_plan_id, "rejected")
                
                # Send rejection message via WebSocket
                from app.services.websocket_service import get_websocket_manager
                websocket_manager = get_websocket_manager()
                await websocket_manager.send_message(request.m_plan_id, {
                    "type": "final_result_message",
                    "data": {
                        "content": f"Plan rejected. {request.feedback or ''}",
                        "status": "rejected",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                })
                
                return PlanApprovalResponse(
                    status="rejected",
                    message="Plan rejected (fallback)"
                )
                
        except Exception as fallback_error:
            logger.error(f"Fallback plan approval handling also failed: {fallback_error}")
            return PlanApprovalResponse(
                status="error",
                message=f"Approval processing failed: {str(e)}"
            )


@router.post("/user_clarification")
async def user_clarification(request: dict, background_tasks: BackgroundTasks):
    """
    Handle user clarification responses with simplified approve/restart workflow.
    Task 10: Simplified to use workflow context service with basic approve/restart logic.
    """
    logger.info(f"User clarification received for plan {request.get('plan_id')}")
    
    plan_id = request.get("plan_id")
    request_id = request.get("request_id", "")
    answer = request.get("answer", "")
    
    if not plan_id:
        raise HTTPException(status_code=400, detail="plan_id is required")
    
    # Use workflow context service for simplified clarification handling
    from app.services.workflow_context_service import get_workflow_context_service
    from app.services.langgraph_service import LangGraphService
    
    try:
        workflow_context_service = get_workflow_context_service()
        
        # Get workflow context
        context = workflow_context_service.get_workflow_context(plan_id)
        if not context:
            raise HTTPException(status_code=404, detail="Workflow context not found")
        
        # Add clarification event to workflow context
        workflow_context_service.add_event(
            plan_id,
            "user_clarification_received",
            message=f"User provided clarification: {answer[:100]}..."
        )
        
        # Simple approval logic - check for approval keywords
        approval_keywords = ["ok", "yes", "approve", "approved", "good", "correct", "fine", "proceed"]
        rejection_keywords = ["no", "reject", "wrong", "incorrect", "restart", "start over", "new task"]
        
        answer_lower = answer.strip().lower()
        
        # Check for explicit approval
        is_approval = any(keyword in answer_lower for keyword in approval_keywords)
        is_rejection = any(keyword in answer_lower for keyword in rejection_keywords)
        
        if is_approval and not is_rejection:
            # User approved - complete task or continue execution
            logger.info(f"✅ User approved clarification for plan {plan_id}")
            
            # Update workflow context
            workflow_context_service.set_final_approval(plan_id, True, answer)
            
            # Complete the workflow
            await PlanRepository.update_status(plan_id, "completed")
            
            # Send completion message via WebSocket
            from app.services.websocket_service import get_websocket_manager
            websocket_manager = get_websocket_manager()
            await websocket_manager.send_message(plan_id, {
                "type": "final_result_message",
                "data": {
                    "content": f"Task completed successfully. User feedback: {answer}",
                    "status": "completed",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            })
            
            return {
                "status": "approved",
                "session_id": request.get("session_id", str(uuid.uuid4())),
                "message": "Task completed successfully"
            }
            
        elif is_rejection or "restart" in answer_lower:
            # User wants to restart - mark workflow as restarted
            logger.info(f"🔄 User requested restart for plan {plan_id}")
            
            # Update workflow context
            workflow_context_service.set_final_approval(plan_id, False, answer)
            
            # Mark as restarted
            await PlanRepository.update_status(plan_id, "restarted")
            
            # Send restart message via WebSocket
            from app.services.websocket_service import get_websocket_manager
            websocket_manager = get_websocket_manager()
            await websocket_manager.send_message(plan_id, {
                "type": "final_result_message",
                "data": {
                    "content": f"User requested workflow restart. {answer}. Please submit a new task.",
                    "status": "restarted",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            })
            
            return {
                "status": "restart_requested",
                "session_id": request.get("session_id", str(uuid.uuid4())),
                "message": "Workflow restart requested. Please submit a new task."
            }
            
        else:
            # User provided additional feedback - treat as revision request
            logger.info(f"🔄 User provided additional feedback for plan {plan_id}")
            
            # Add feedback event
            workflow_context_service.add_event(
                plan_id,
                "additional_feedback",
                message=f"User provided additional feedback: {answer}"
            )
            
            # Resume execution with the feedback as additional context
            updates = {
                "result_approved": False,
                "hitl_feedback": answer,
                "awaiting_user_input": False,
                "task_description": f"{context.task_description}\n\nAdditional feedback: {answer}"
            }
            
            background_tasks.add_task(
                LangGraphService.resume_execution,
                plan_id,
                updates
            )
            
            return {
                "status": "processing_feedback",
                "session_id": request.get("session_id", str(uuid.uuid4())),
                "message": "Processing additional feedback"
            }
            
    except Exception as e:
        logger.error(f"Simplified clarification handling failed: {e}", exc_info=True)
        
        # Fallback to basic approval/rejection logic
        try:
            workflow_context_service = get_workflow_context_service()
            
            # Simple fallback logic
            is_approval = answer.strip().upper() in ["OK", "YES", "APPROVE", "APPROVED"]
            
            if is_approval:
                # Update workflow context and complete
                workflow_context_service.set_final_approval(plan_id, True, answer)
                await PlanRepository.update_status(plan_id, "completed")
                
                return {
                    "status": "approved",
                    "session_id": request.get("session_id", str(uuid.uuid4())),
                    "message": "Task completed (fallback)"
                }
            else:
                # Update workflow context and restart
                workflow_context_service.set_final_approval(plan_id, False, answer)
                await PlanRepository.update_status(plan_id, "restarted")
                
                return {
                    "status": "restart_requested",
                    "session_id": request.get("session_id", str(uuid.uuid4())),
                    "message": "Workflow restart requested (fallback)"
                }
                
        except Exception as fallback_error:
            logger.error(f"Fallback clarification handling also failed: {fallback_error}")
            raise HTTPException(status_code=500, detail=f"Clarification processing failed: {str(e)}")
    
    return {
        "status": "processing",
        "session_id": request.get("session_id", str(uuid.uuid4()))
    }


@router.post("/extraction_approval")
async def extraction_approval(request: dict, background_tasks: BackgroundTasks):
    """
    Handle invoice extraction approval/rejection.
    Phase 4: Processes extraction approval and continues or stops workflow.
    """
    logger.info(f"Extraction approval received for plan {request.get('plan_id')}: approved={request.get('approved')}")
    
    plan_id = request.get("plan_id")
    approved = request.get("approved", False)
    feedback = request.get("feedback", "")
    edited_data = request.get("edited_data")
    
    if not plan_id:
        raise HTTPException(status_code=400, detail="plan_id is required")
    
    # Process extraction approval in background
    background_tasks.add_task(
        AgentService.handle_extraction_approval,
        plan_id,
        approved,
        feedback,
        edited_data
    )
    
    return {
        "status": "processing",
        "message": "Extraction approval received"
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
    Phase 8: Returns team configurations from database.
    """
    logger.info("Getting teams")
    
    from app.db.mongodb import MongoDB
    
    db = MongoDB.get_database()
    teams_collection = db["teams"]
    
    teams = []
    async for team_doc in teams_collection.find():
        # Remove MongoDB _id field
        team_doc.pop('_id', None)
        teams.append(team_doc)
    
    return teams


@router.post("/teams/upload")
async def upload_teams(teams_data: dict):
    """
    Upload team configurations from JSON file.
    Stores multiple team configurations to database.
    """
    logger.info("Uploading team configurations")
    
    from app.db.mongodb import MongoDB
    
    try:
        teams_list = teams_data.get("teams", [])
        
        if not teams_list:
            raise HTTPException(status_code=400, detail="No teams found in upload data")
        
        db = MongoDB.get_database()
        teams_collection = db["teams"]
        
        # Clear existing teams and insert new ones
        await teams_collection.delete_many({})
        
        if teams_list:
            await teams_collection.insert_many(teams_list)
        
        logger.info(f"Uploaded {len(teams_list)} team configurations")
        
        return {
            "status": "success",
            "message": f"Uploaded {len(teams_list)} teams",
            "teams": teams_list
        }
        
    except Exception as e:
        logger.error(f"Failed to upload teams: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload teams: {str(e)}")


@router.get("/init_team")
async def init_team(team_switched: bool = Query(False)):
    """
    Initialize a team.
    Updated for Task 11: Enhanced team initialization with AI planning support.
    """
    logger.info(f"Initializing team (switched: {team_switched})")
    
    # Generate team ID
    team_id = str(uuid.uuid4())
    
    # Initialize AI Planner for the team
    from app.services.ai_planner_service import AIPlanner
    from app.services.llm_service import LLMService
    
    try:
        llm_service = LLMService()
        ai_planner = AIPlanner(llm_service)
        
        # Get available agents for the team
        available_agents = ai_planner.available_agents
        
        logger.info(f"Team {team_id} initialized with AI planning support")
        logger.info(f"Available agents: {', '.join(available_agents)}")
        
        return {
            "status": "initialized",
            "team_id": team_id,
            "ai_planning_enabled": True,
            "available_agents": available_agents,
            "capabilities": ai_planner.agent_capabilities
        }
        
    except Exception as e:
        logger.error(f"AI Planner initialization failed: {e}")
        return {
            "status": "initialized",
            "team_id": team_id,
            "ai_planning_enabled": False,
            "error": str(e)
        }


@router.get("/ai_planning/analyze")
async def analyze_task_preview(task: str = Query(...)):
    """
    Preview AI task analysis without executing.
    Task 11: New endpoint for frontend to show AI planning capabilities.
    """
    logger.info(f"AI task analysis preview: {task[:50]}...")
    
    from app.services.ai_planner_service import AIPlanner
    from app.services.llm_service import LLMService
    
    try:
        # Initialize AI Planner
        llm_service = LLMService()
        ai_planner = AIPlanner(llm_service)
        
        # Analyze task
        analysis = await ai_planner.analyze_task(task)
        
        return {
            "success": True,
            "analysis": {
                "complexity": analysis.complexity,
                "required_systems": analysis.required_systems,
                "business_context": analysis.business_context,
                "data_sources_needed": analysis.data_sources_needed,
                "estimated_agents": analysis.estimated_agents,
                "confidence_score": analysis.confidence_score,
                "reasoning": analysis.reasoning
            }
        }
        
    except Exception as e:
        logger.error(f"AI task analysis failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "fallback_available": True
        }


@router.get("/ai_planning/sequence")
async def generate_sequence_preview(task: str = Query(...)):
    """
    Preview AI agent sequence generation without executing.
    Task 11: New endpoint for frontend to show AI sequence planning.
    """
    logger.info(f"AI sequence generation preview: {task[:50]}...")
    
    from app.services.ai_planner_service import AIPlanner
    from app.services.llm_service import LLMService
    
    try:
        # Initialize AI Planner
        llm_service = LLMService()
        ai_planner = AIPlanner(llm_service)
        
        # Generate complete workflow plan
        planning_summary = await ai_planner.plan_workflow(task)
        
        if planning_summary.success:
            return {
                "success": True,
                "planning_summary": {
                    "task_analysis": {
                        "complexity": planning_summary.task_analysis.complexity,
                        "required_systems": planning_summary.task_analysis.required_systems,
                        "confidence_score": planning_summary.task_analysis.confidence_score
                    },
                    "agent_sequence": {
                        "agents": planning_summary.agent_sequence.agents,
                        "reasoning": planning_summary.agent_sequence.reasoning,
                        "estimated_duration": planning_summary.agent_sequence.estimated_duration,
                        "complexity_score": planning_summary.agent_sequence.complexity_score
                    },
                    "total_duration": planning_summary.total_duration
                }
            }
        else:
            # Return fallback sequence
            fallback_sequence = ai_planner.get_fallback_sequence(task)
            return {
                "success": False,
                "error": planning_summary.error_message,
                "fallback_sequence": {
                    "agents": fallback_sequence.agents,
                    "reasoning": fallback_sequence.reasoning,
                    "estimated_duration": fallback_sequence.estimated_duration
                }
            }
        
    except Exception as e:
        logger.error(f"AI sequence generation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/extraction/{plan_id}/json")
async def get_extraction_json(plan_id: str):
    """
    Get invoice extraction as JSON.
    Phase 5: Returns structured extraction data.
    """
    logger.info(f"Getting extraction JSON for plan {plan_id}")
    
    from app.db.repositories import InvoiceExtractionRepository
    
    extraction = await InvoiceExtractionRepository.get_extraction(plan_id)
    
    if not extraction:
        raise HTTPException(status_code=404, detail="Extraction not found")
    
    return InvoiceExtractionRepository.export_extraction_json(extraction)


@router.get("/extraction/{plan_id}/csv")
async def get_extraction_csv(plan_id: str):
    """
    Get invoice extraction as CSV.
    Phase 5: Returns CSV formatted extraction data.
    """
    logger.info(f"Getting extraction CSV for plan {plan_id}")
    
    from fastapi.responses import Response
    from app.db.repositories import InvoiceExtractionRepository
    
    extraction = await InvoiceExtractionRepository.get_extraction(plan_id)
    
    if not extraction:
        raise HTTPException(status_code=404, detail="Extraction not found")
    
    csv_content = InvoiceExtractionRepository.export_extraction_csv(extraction)
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=invoice_{plan_id}.csv"
        }
    )


@router.get("/extractions")
async def get_all_extractions(limit: int = Query(100, le=1000)):
    """
    Get all invoice extractions.
    Phase 5: Returns list of all extractions.
    """
    logger.info(f"Getting all extractions (limit={limit})")
    
    from app.db.repositories import InvoiceExtractionRepository
    
    extractions = await InvoiceExtractionRepository.get_all_extractions(limit=limit)
    
    return {
        "extractions": extractions,
        "count": len(extractions)
    }


@router.get("/extraction/{plan_id}/visualize")
async def get_extraction_visualization(plan_id: str):
    """
    Get HTML visualization of extraction using langextract.
    Returns HTML content that can be displayed in an iframe.
    """
    logger.info(f"Getting visualization for plan {plan_id}")
    
    from fastapi.responses import HTMLResponse
    from app.services.langextract_service import LangExtractService
    
    # Try to get cached visualization first
    html_content = LangExtractService.get_visualization(plan_id)
    
    if not html_content:
        # If not cached, try to generate from database
        from app.db.repositories import InvoiceExtractionRepository
        
        extraction = await InvoiceExtractionRepository.get_extraction(plan_id)
        
        if not extraction:
            raise HTTPException(status_code=404, detail="Extraction not found")
        
        # Generate visualization
        html_content = LangExtractService.visualize_extraction(extraction, plan_id)
        
        if not html_content:
            raise HTTPException(status_code=500, detail="Failed to generate visualization")
    
    return HTMLResponse(content=html_content)


@router.post("/upload_file")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and extract text from invoice files.
    Supports: .txt, .docx
    
    Args:
        file: Uploaded file (multipart/form-data)
        
    Returns:
        JSON response with extracted text content
    """
    logger.info(f"File upload request: {file.filename}")
    
    try:
        # Get file size before reading
        content = await file.read()
        file_size = len(content)
        
        # Reset file pointer for extraction
        await file.seek(0)
        
        # Extract text from file
        extracted_text = await FileParserService.extract_text(file)
        
        logger.info(f"Successfully extracted text from {file.filename} ({file_size} bytes)")
        
        return {
            "success": True,
            "filename": file.filename,
            "content": extracted_text,
            "file_size": file_size,
            "file_type": file.content_type
        }
        
    except ValueError as e:
        # Client errors (bad file type, empty file, etc.)
        logger.warning(f"File validation error for {file.filename}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        # Server errors (parsing failures, etc.)
        logger.error(f"File processing error for {file.filename}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process file: {str(e)}"
        )


@router.get("/workflows")
async def list_workflows():
    """
    List available workflow templates.
    Phase 4: Workflow integration endpoint.
    
    Returns:
        List of available workflows with metadata
    """
    try:
        result = await AgentServiceRefactored.list_workflows()
        if result["status"] == "success":
            return result["workflows"]
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute_workflow")
async def execute_workflow(request: dict, background_tasks: BackgroundTasks):
    """
    Execute a specific workflow template.
    Phase 4: Direct workflow execution endpoint.
    
    Args:
        request: {
            "workflow_name": str,
            "plan_id": str,
            "session_id": str,
            "parameters": dict
        }
        
    Returns:
        Execution result
    """
    try:
        workflow_name = request.get("workflow_name")
        plan_id = request.get("plan_id")
        session_id = request.get("session_id")
        parameters = request.get("parameters", {})
        
        if not all([workflow_name, plan_id, session_id]):
            raise HTTPException(
                status_code=400,
                detail="workflow_name, plan_id, and session_id are required"
            )
        
        # Execute workflow using WorkflowFactory directly
        from app.agents.workflows.factory import WorkflowFactory
        
        result = await WorkflowFactory.execute_workflow(
            workflow_name=workflow_name,
            plan_id=plan_id,
            session_id=session_id,
            parameters=parameters
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process_request_ai", response_model=ProcessRequestResponse)
async def process_request_ai(request: ProcessRequestInput, background_tasks: BackgroundTasks):
    """
    Process request using AI Planner with full workflow analysis.
    Task 11: New endpoint that showcases AI-driven planning capabilities.
    
    This endpoint uses the AI Planner to analyze tasks and generate optimal
    agent sequences, then executes using the LinearGraphFactory.
    """
    logger.info(f"Processing AI-driven request: {request.description[:50]}...")
    
    # Generate IDs
    plan_id = str(uuid.uuid4())
    session_id = request.session_id or str(uuid.uuid4())
    
    # Use AI Planner for comprehensive task analysis
    from app.services.ai_planner_service import AIPlanner
    from app.services.llm_service import LLMService
    
    try:
        # Initialize AI Planner
        llm_service = LLMService()
        ai_planner = AIPlanner(llm_service)
        
        # Generate comprehensive AI-driven workflow plan
        planning_summary = await ai_planner.plan_workflow(request.description)
        
        if planning_summary.success:
            agent_sequence = planning_summary.agent_sequence.agents
            complexity = planning_summary.task_analysis.complexity
            estimated_duration = planning_summary.agent_sequence.estimated_duration
            
            logger.info(f"AI analysis: {complexity} task, {len(agent_sequence)} agents, ~{estimated_duration}s")
            
            # Create detailed plan steps with AI reasoning
            steps = []
            for i, agent in enumerate(agent_sequence):
                reasoning = planning_summary.agent_sequence.reasoning.get(agent, f"Execute {agent} capabilities")
                steps.append(Step(
                    id=f"{plan_id}-step-{i+1}",
                    description=reasoning,
                    agent=agent.capitalize(),
                    status="pending"
                ))
        else:
            # Use fallback sequence with error info
            fallback_sequence = ai_planner.get_fallback_sequence(request.description)
            agent_sequence = fallback_sequence.agents
            
            logger.warning(f"AI planning failed: {planning_summary.error_message}")
            
            steps = []
            for i, agent in enumerate(agent_sequence):
                steps.append(Step(
                    id=f"{plan_id}-step-{i+1}",
                    description=f"Fallback: Execute {agent.capitalize()} agent",
                    agent=agent.capitalize(),
                    status="pending"
                ))
        
    except Exception as e:
        logger.error(f"AI Planner initialization failed: {e}")
        # Ultimate fallback
        agent_sequence = ["analysis"]
        steps = [Step(
            id=f"{plan_id}-step-1",
            description="General task analysis and processing",
            agent="Analysis",
            status="pending"
        )]
    
    # Create plan with AI-generated steps
    plan = Plan(
        id=plan_id,
        session_id=session_id,
        description=request.description,
        status="pending",
        steps=steps
    )
    
    # Save to database
    await PlanRepository.create(plan)
    
    # Execute using AI-driven LangGraph service
    from app.services.langgraph_service import LangGraphService
    from app.services.websocket_service import get_websocket_manager
    websocket_manager = get_websocket_manager()
    
    background_tasks.add_task(
        LangGraphService.execute_task_with_ai_planner,
        plan_id,
        session_id,
        request.description,
        websocket_manager
    )
    
    return ProcessRequestResponse(
        plan_id=plan_id,
        status="created",
        session_id=session_id
    )


@router.post("/process_request_v2", response_model=ProcessRequestResponse)
async def process_request_v2(request: ProcessRequestInput, background_tasks: BackgroundTasks):
    """
    Process request using refactored agent service with workflow support.
    Phase 4: Smart routing between workflows and regular agents.
    
    This endpoint automatically detects if the task should use a workflow
    or regular agent routing based on the task description.
    """
    logger.info(f"Processing request v2: {request.description[:50]}...")
    
    # Generate IDs
    plan_id = str(uuid.uuid4())
    session_id = request.session_id or str(uuid.uuid4())
    
    # Create plan
    plan = Plan(
        id=plan_id,
        session_id=session_id,
        description=request.description,
        status="pending",
        steps=[]
    )
    
    # Store plan
    await PlanRepository.create(plan)
    
    # Execute using refactored service in background
    background_tasks.add_task(
        AgentServiceRefactored.execute_task,
        plan_id,
        session_id,
        request.description,
        request.require_hitl
    )
    
    return ProcessRequestResponse(
        plan_id=plan_id,
        status="pending",
        session_id=session_id
    )


@router.get("/comprehensive_results/{plan_id}")
async def get_comprehensive_results(plan_id: str):
    """
    Get comprehensive results compilation for a completed plan.
    Task 7: Returns formatted comprehensive results from all agents.
    """
    logger.info(f"Getting comprehensive results for plan {plan_id}")
    
    from app.services.results_compiler_service import get_results_compiler_service
    from app.services.langgraph_service import LangGraphService
    
    try:
        # Get current agent state
        agent_state = await LangGraphService.get_agent_state(plan_id)
        
        if not agent_state:
            raise HTTPException(status_code=404, detail="Plan state not found")
        
        # Compile comprehensive results
        results_compiler = get_results_compiler_service()
        comprehensive_results = await results_compiler.compile_comprehensive_results(
            plan_id=plan_id,
            agent_state=agent_state
        )
        
        return comprehensive_results
        
    except Exception as e:
        logger.error(f"Failed to get comprehensive results for plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compile results: {str(e)}")




@router.get("/workflow_context/{plan_id}")
async def get_workflow_context(plan_id: str):
    """
    Get simple workflow context information.
    Task 10: Simple workflow context tracking without complex revisions.
    """
    logger.info(f"Getting workflow context for plan {plan_id}")
    
    from app.services.workflow_context_service import get_workflow_context_service
    
    try:
        workflow_context_service = get_workflow_context_service()
        context = workflow_context_service.get_workflow_context(plan_id)
        
        if not context:
            raise HTTPException(status_code=404, detail="Workflow context not found")
        
        return context.to_dict()
        
    except Exception as e:
        logger.error(f"Failed to get workflow context for plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow context: {str(e)}")


@router.get("/workflow_summary/{plan_id}")
async def get_workflow_summary(plan_id: str):
    """
    Get workflow execution summary.
    Task 10: Simple workflow summary without complex revision analytics.
    """
    logger.info(f"Getting workflow summary for plan {plan_id}")
    
    from app.services.workflow_context_service import get_workflow_context_service
    
    try:
        workflow_context_service = get_workflow_context_service()
        summary = workflow_context_service.get_workflow_summary(plan_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="Workflow summary not found")
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get workflow summary for plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow summary: {str(e)}")


@router.post("/user_browser_language")
async def user_browser_language(request: dict):
    """
    Receive user browser language information.
    
    Args:
        request: Dictionary containing language information
        
    Returns:
        Status response
    """
    try:
        language = request.get('language', 'en')
        logger.info(f"📍 User browser language: {language}")
        
        # For now, just log the language. In the future, this could be used for
        # internationalization or user preferences
        
        return {"status": "success", "message": "Language preference recorded"}
        
    except Exception as e:
        logger.error(f"❌ Error processing browser language: {e}")
        raise HTTPException(status_code=500, detail="Failed to process language preference")