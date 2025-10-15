"""
API endpoints for interacting with the agent workflow.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from karigar.orchestrators.workflow import KarigarWorkflow
from karigar.memory.sql_memory import get_session
from karigar.schemas.models import MaterialRequest, MicroStore
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/agents", tags=["Agent Workflow"])

class RequestInput(BaseModel):
    artisan_id: str
    message: str
    artisan_phone: str # Added for user identification
    artisan_name: str = "Anonymous Artisan"

@router.post("/request")
async def create_material_request(input: RequestInput):
    """
    Endpoint to initiate a new material request workflow.
    """
    try:
        workflow = KarigarWorkflow()
        
        initial_state = {
            "messages": [{"role": "user", "content": input.message}],
            "artisan_id": input.artisan_id,
            "artisan_phone": input.artisan_phone,
            "artisan_name": input.artisan_name,
            "status": "started"
        }
        
        # Run the workflow
        result = await workflow.run(initial_state)
        
        # Check for errors during the workflow
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "An unknown workflow error occurred."))

        return {"message": "Workflow completed successfully", "final_state": result}

    except Exception as e:
        print(f"[API Error] /request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/requests/{request_id}/status")
async def get_request_status(request_id: str, db: Session = Depends(get_session)):
    """
    Endpoint to check the status of a specific material request.
    """
    try:
        request = db.query(MaterialRequest).filter(MaterialRequest.id == request_id).first()
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        return {"request_id": request.id, "status": request.status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/artisans/{artisan_id}/stores")
async def get_artisan_stores(artisan_id: str, db: Session = Depends(get_session)):
    """
    Endpoint to retrieve all micro-stores created for a specific artisan.
    """
    try:
        stores = db.query(MicroStore).filter(MicroStore.artisan_id == artisan_id).all()
        if not stores:
            return {"message": "No stores found for this artisan."}
        
        return [{"store_id": store.id, "store_url": store.store_url, "product_name": store.product_name} for store in stores]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
