"""API v3 routes."""
import logging
import uuid
from typing import List, Optional
import asyncio

from fastapi import APIRouter, Query, HTTPException, BackgroundTasks, File, UploadFile

from app.models.plan import Plan, PlanResponse, ProcessRequestInput, ProcessRequestResponse, Step
from app.models.message import AgentMessage
from app.models.team import TeamConfiguration
from app.models.approval import PlanApprovalRequest, PlanApprovalResponse
from app.db.repositories import PlanRepository, MessageRepository
from app.services.agent_service import AgentService
from app.services.file_parser_service import FileParserService

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
    Phase 8: Will handle team initialization.
    """
    logger.info(f"Initializing team (switched: {team_switched})")
    return {
        "status": "initialized",
        "team_id": str(uuid.uuid4())
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
