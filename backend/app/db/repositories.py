"""Database repositories for data access."""
import logging
from typing import List, Optional
from datetime import datetime

from app.db.mongodb import MongoDB
from app.models.plan import Plan
from app.models.message import AgentMessage

logger = logging.getLogger(__name__)


class PlanRepository:
    """Repository for plan operations."""
    
    @staticmethod
    async def create(plan: Plan) -> str:
        """Create a new plan."""
        db = MongoDB.get_database()
        collection = db["plans"]
        
        plan_dict = plan.model_dump(by_alias=True)
        plan_dict["plan_id"] = plan.id
        
        result = await collection.insert_one(plan_dict)
        logger.info(f"Created plan: {plan.id}")
        return plan.id
    
    @staticmethod
    async def get_by_id(plan_id: str) -> Optional[Plan]:
        """Get plan by ID."""
        db = MongoDB.get_database()
        collection = db["plans"]
        
        plan_dict = await collection.find_one({"plan_id": plan_id})
        if plan_dict:
            plan_dict["id"] = plan_dict["plan_id"]
            return Plan(**plan_dict)
        return None
    
    @staticmethod
    async def get_all(session_id: Optional[str] = None) -> List[Plan]:
        """Get all plans, optionally filtered by session_id, sorted by created_at descending (newest first)."""
        db = MongoDB.get_database()
        collection = db["plans"]
        
        query = {"session_id": session_id} if session_id else {}
        # Sort by created_at descending (newest first) for reverse chronological order
        cursor = collection.find(query).sort("created_at", -1)
        
        plans = []
        async for plan_dict in cursor:
            plan_dict["id"] = plan_dict["plan_id"]
            plans.append(Plan(**plan_dict))
        
        return plans
    
    @staticmethod
    async def update_status(plan_id: str, status: str) -> bool:
        """Update plan status."""
        db = MongoDB.get_database()
        collection = db["plans"]
        
        result = await collection.update_one(
            {"plan_id": plan_id},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    @staticmethod
    async def update_agent_progress(plan_id: str, agent_name: str, status: str) -> bool:
        """Update or add agent progress entry."""
        db = MongoDB.get_database()
        collection = db["plans"]
        
        progress_entry = {
            "agent_name": agent_name,
            "status": status,
            "timestamp": datetime.utcnow()
        }
        
        # First, remove existing entry for this agent (if any)
        await collection.update_one(
            {"plan_id": plan_id},
            {"$pull": {"agent_progress": {"agent_name": agent_name}}}
        )
        
        # Then add the new entry
        result = await collection.update_one(
            {"plan_id": plan_id},
            {
                "$push": {"agent_progress": progress_entry},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return result.modified_count > 0
    
    @staticmethod
    async def update_extraction_data(plan_id: str, extraction_data: dict) -> bool:
        """Store extraction data in plan."""
        db = MongoDB.get_database()
        collection = db["plans"]
        
        result = await collection.update_one(
            {"plan_id": plan_id},
            {"$set": {"extraction_data": extraction_data, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0


class MessageRepository:
    """Repository for message operations."""
    
    @staticmethod
    async def create(message: AgentMessage) -> str:
        """Create a new message."""
        db = MongoDB.get_database()
        collection = db["messages"]
        
        message_dict = message.model_dump()
        result = await collection.insert_one(message_dict)
        logger.info(f"Created message for plan: {message.plan_id}")
        return str(result.inserted_id)
    
    @staticmethod
    async def get_by_plan_id(plan_id: str) -> List[AgentMessage]:
        """Get all messages for a plan."""
        db = MongoDB.get_database()
        collection = db["messages"]
        
        cursor = collection.find({"plan_id": plan_id}).sort("timestamp", 1)
        
        messages = []
        async for message_dict in cursor:
            messages.append(AgentMessage(**message_dict))
        
        return messages


class InvoiceExtractionRepository:
    """Repository for invoice extraction operations."""
    
    @staticmethod
    async def store_extraction(plan_id: str, extraction_result: any, approved_by: str = "user") -> str:
        """
        Store approved invoice extraction to database.
        
        Args:
            plan_id: Plan identifier
            extraction_result: ExtractionResult object
            approved_by: User who approved the extraction
            
        Returns:
            Extraction ID
        """
        db = MongoDB.get_database()
        collection = db["invoice_extractions"]
        
        # Convert extraction result to dict
        extraction_dict = {
            "plan_id": plan_id,
            "success": extraction_result.success,
            "invoice_data": extraction_result.invoice_data.model_dump() if extraction_result.invoice_data else None,
            "validation_errors": extraction_result.validation_errors,
            "extraction_time": extraction_result.extraction_time,
            "model_used": extraction_result.model_used,
            "approved_by": approved_by,
            "approved_at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        
        # Convert dates and decimals to strings for MongoDB
        if extraction_dict["invoice_data"]:
            invoice_data = extraction_dict["invoice_data"]
            for key, value in invoice_data.items():
                if hasattr(value, 'isoformat'):  # date/datetime
                    invoice_data[key] = value.isoformat()
                elif hasattr(value, '__str__') and key not in ['vendor_name', 'vendor_address', 'invoice_number', 'currency', 'payment_terms', 'notes', 'line_items']:
                    invoice_data[key] = str(value)
            
            # Handle line items
            if invoice_data.get('line_items'):
                for item in invoice_data['line_items']:
                    for k, v in item.items():
                        if hasattr(v, '__str__') and k != 'description':
                            item[k] = str(v)
        
        result = await collection.insert_one(extraction_dict)
        extraction_id = str(result.inserted_id)
        
        logger.info(f"📊 Stored invoice extraction for plan {plan_id}: {extraction_id}")
        return extraction_id
    
    @staticmethod
    async def get_extraction(plan_id: str) -> Optional[dict]:
        """
        Get invoice extraction by plan ID.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Extraction dict or None
        """
        db = MongoDB.get_database()
        collection = db["invoice_extractions"]
        
        extraction = await collection.find_one({"plan_id": plan_id})
        
        if extraction:
            # Convert ObjectId to string
            extraction["_id"] = str(extraction["_id"])
            logger.info(f"📊 Retrieved invoice extraction for plan {plan_id}")
            return extraction
        
        logger.info(f"📊 No invoice extraction found for plan {plan_id}")
        return None
    
    @staticmethod
    async def get_all_extractions(limit: int = 100) -> List[dict]:
        """
        Get all invoice extractions.
        
        Args:
            limit: Maximum number of extractions to return
            
        Returns:
            List of extraction dicts
        """
        db = MongoDB.get_database()
        collection = db["invoice_extractions"]
        
        cursor = collection.find().sort("created_at", -1).limit(limit)
        
        extractions = []
        async for extraction in cursor:
            extraction["_id"] = str(extraction["_id"])
            extractions.append(extraction)
        
        logger.info(f"📊 Retrieved {len(extractions)} invoice extractions")
        return extractions
    
    @staticmethod
    def export_extraction_json(extraction: dict) -> dict:
        """
        Export extraction as JSON.
        
        Args:
            extraction: Extraction dict from database
            
        Returns:
            Formatted JSON dict
        """
        return {
            "plan_id": extraction.get("plan_id"),
            "invoice_data": extraction.get("invoice_data"),
            "validation_errors": extraction.get("validation_errors", []),
            "extraction_metadata": {
                "model_used": extraction.get("model_used"),
                "extraction_time": extraction.get("extraction_time"),
                "approved_by": extraction.get("approved_by"),
                "approved_at": extraction.get("approved_at").isoformat() if extraction.get("approved_at") else None
            }
        }
    
    @staticmethod
    def export_extraction_csv(extraction: dict) -> str:
        """
        Export extraction as CSV.
        
        Args:
            extraction: Extraction dict from database
            
        Returns:
            CSV string
        """
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        invoice_data = extraction.get("invoice_data", {})
        
        # Write header
        writer.writerow([
            "Plan ID",
            "Vendor Name",
            "Vendor Address",
            "Invoice Number",
            "Invoice Date",
            "Due Date",
            "Currency",
            "Subtotal",
            "Tax Amount",
            "Total Amount",
            "Payment Terms",
            "Approved At"
        ])
        
        # Write data
        writer.writerow([
            extraction.get("plan_id", ""),
            invoice_data.get("vendor_name", ""),
            invoice_data.get("vendor_address", ""),
            invoice_data.get("invoice_number", ""),
            invoice_data.get("invoice_date", ""),
            invoice_data.get("due_date", ""),
            invoice_data.get("currency", ""),
            invoice_data.get("subtotal", ""),
            invoice_data.get("tax_amount", ""),
            invoice_data.get("total_amount", ""),
            invoice_data.get("payment_terms", ""),
            extraction.get("approved_at").isoformat() if extraction.get("approved_at") else ""
        ])
        
        # Write line items if present
        line_items = invoice_data.get("line_items", [])
        if line_items:
            writer.writerow([])
            writer.writerow(["Line Items"])
            writer.writerow(["Description", "Quantity", "Unit Price", "Total"])
            for item in line_items:
                writer.writerow([
                    item.get("description", ""),
                    item.get("quantity", ""),
                    item.get("unit_price", ""),
                    item.get("total", "")
                ])
        
        return output.getvalue()
