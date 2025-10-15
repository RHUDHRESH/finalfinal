"""
FastAPI Application Entry Point
This is the main file that starts the backend server.

Run with: uvicorn src.karigar.main:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os
from pathlib import Path

# Import database initialization
from karigar.memory.sql_memory import init_db, get_session
from karigar.schemas.models import MaterialRequest, Artisan

# Create FastAPI app
app = FastAPI(
    title="KarigarAgent API",
    description="Production-grade artisan material management system with AI agents",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc"  # ReDoc at http://localhost:8000/redoc
)

# CORS Configuration - Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Mount static files for images, PDFs, QR codes
uploads_dir = Path("./uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ============================================================================
# STARTUP EVENT - Initialize Database
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Run when the application starts.
    Initializes the database if not already initialized.
    """
    print("=" * 60)
    print("🚀 Starting KarigarAgent Backend...")
    print("=" * 60)
    
    # Initialize database
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
    
    print(f"📡 API running at: http://localhost:8000")
    print(f"📚 API Docs at: http://localhost:8000/docs")
    print("=" * 60)


# ============================================================================
# PYDANTIC MODELS (Request/Response Schemas)
# ============================================================================

class MaterialRequestInput(BaseModel):
    """Schema for incoming material request from frontend"""
    artisan_id: str
    artisan_name: Optional[str] = "Unknown Artisan"
    artisan_phone: Optional[str] = "0000000000"
    message: str  # Natural language input like "I need 50kg cement in Delhi"
    
    class Config:
        json_schema_extra = {
            "example": {
                "artisan_id": "ART123",
                "artisan_name": "Ravi Kumar",
                "artisan_phone": "9876543210",
                "message": "I need 100 kg of cement in Delhi by next week, budget 5000 rupees"
            }
        }


class MaterialRequestResponse(BaseModel):
    """Schema for response after processing request"""
    success: bool
    request_id: Optional[str] = None
    message: str
    data: Optional[dict] = None


class StatusResponse(BaseModel):
    """Schema for status check response"""
    request_id: str
    status: str
    details: Optional[dict] = None


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """
    Root endpoint - health check
    """
    return {
        "status": "running",
        "message": "KarigarAgent API is operational",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "request_material": "/api/request",
            "check_status": "/api/status/{request_id}",
            "list_requests": "/api/requests"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    session = get_session()
    try:
        # Try to query database
        count = session.query(Artisan).count()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    finally:
        session.close()
    
    return {
        "status": "healthy",
        "database": db_status,
        "api_version": "1.0.0"
    }


# ============================================================================
# MAIN AGENT ENDPOINT
# ============================================================================

@app.post("/api/request", response_model=MaterialRequestResponse)
async def create_material_request(request: MaterialRequestInput):
    """
    Main endpoint - receives material request and triggers agent workflow.
    
    This endpoint:
    1. Receives natural language request from frontend
    2. Triggers IntakeAgent to parse it
    3. Triggers SupplierAgent to find suppliers
    4. Returns request ID for tracking
    """
    try:
        print(f"\n{'='*60}")
        print(f"📥 NEW REQUEST from {request.artisan_name}")
        print(f"📝 Message: {request.message}")
        print(f"{'='*60}\n")
        
        # Import agents (lazy import to avoid circular dependencies)
        from karigar.agents.intake_agent import IntakeAgent
        from karigar.schemas.state import KarigarState
        
        # Create initial state
        initial_state: KarigarState = {
            "messages": [{"role": "user", "content": request.message}],
            "artisan_id": request.artisan_id,
            "artisan_name": request.artisan_name,
            "artisan_phone": request.artisan_phone,
            "artisan_location": None,
            "material_request": None,
            "request_id": None,
            "supplier_quotes": [],
            "selected_quote": None,
            "order_id": None,
            "order_details": None,
            "payment_info": None,
            "po_path": None,
            "store_url": None,
            "store_id": None,
            "status": "started",
            "error": None
        }
        
        # Run IntakeAgent
        intake_agent = IntakeAgent()
        intake_result = intake_agent.process(initial_state)
        
        # Check for errors from IntakeAgent
        if intake_result.get("status") == "error":
            raise HTTPException(status_code=400, detail=intake_result.get("error", "Processing failed"))

        # Update state with intake results
        current_state = {**initial_state, **intake_result}

        # Now, run SupplierAgent
        from karigar.agents.supplier_agent import SupplierAgent
        supplier_agent = SupplierAgent()
        supplier_result = await supplier_agent.process(current_state)

        # Check for errors from SupplierAgent
        if supplier_result.get("status") == "error":
            print(f"SupplierAgent failed: {supplier_result.get('error')}")
            return MaterialRequestResponse(
                success=True,
                request_id=current_state.get("request_id"),
                message="Material request processed. We are currently facing issues finding suppliers. We will notify you.",
                data={
                    "material": current_state.get("material_request", {}).get("material"),
                    "quantity": current_state.get("material_request", {}).get("quantity"),
                    "budget": current_state.get("material_request", {}).get("budget"),
                    "status": "supplier_search_failed"
                }
            )

        # Update state with supplier results
        final_state = {**current_state, **supplier_result}

        # Return a success response
        return MaterialRequestResponse(
            success=True,
            request_id=final_state.get("request_id"),
            message=f"Found {len(final_state.get('supplier_quotes', []))} potential suppliers for your request!",
            data={
                "material": final_state.get("material_request", {}).get("material"),
                "quantity": final_state.get("material_request", {}).get("quantity"),
                "budget": final_state.get("material_request", {}).get("budget"),
                "status": "supplier_search_complete",
                "quotes": final_state.get("supplier_quotes")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error processing request: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ============================================================================
# COMMIT AGENT ENDPOINT
# ============================================================================

class QuoteSelectionInput(BaseModel):
    """Schema for incoming quote selection from frontend"""
    request_id: str
    quote_id: str

@app.post("/api/select_quote")
async def select_quote(selection: QuoteSelectionInput):
    """
    Endpoint to select a quote and trigger the CommitAgent.
    """
    try:
        from karigar.agents.commit_agent import CommitAgent
        from karigar.schemas.state import KarigarState
        from karigar.schemas.models import SupplierQuote

        session = get_session()
        try:
            request = session.query(MaterialRequest).filter_by(id=selection.request_id).first()
            if not request:
                raise HTTPException(status_code=404, detail="MaterialRequest not found.")

            selected_quote = session.query(SupplierQuote).filter_by(id=selection.quote_id, request_id=selection.request_id).first()
            if not selected_quote:
                raise HTTPException(status_code=404, detail="SupplierQuote not found or does not belong to the request.")

            all_quotes = session.query(SupplierQuote).filter_by(request_id=selection.request_id).all()

            # Convert quotes to dicts for state
            supplier_quotes_list = [
                {
                    "id": q.id,
                    "supplier_id": q.supplier_id,
                    "price_per_unit": q.price_per_unit,
                    "total_price": q.total_price,
                    "delivery_charge": q.delivery_charge,
                    "delivery_days": q.delivery_days
                } for q in all_quotes
            ]

            initial_state: KarigarState = {
                "request_id": request.id,
                "artisan_id": request.artisan_id,
                "material_request": {
                    "material": request.material,
                    "quantity": request.quantity,
                    "budget": request.budget,
                    "timeline": request.timeline,
                    "location": request.artisan.location,
                },
                "supplier_quotes": supplier_quotes_list,
                "selected_quote": {
                    "id": selected_quote.id,
                    "supplier_id": selected_quote.supplier_id,
                    "price_per_unit": selected_quote.price_per_unit,
                    "total_price": selected_quote.total_price,
                    "delivery_charge": selected_quote.delivery_charge,
                    "delivery_days": selected_quote.delivery_days
                },
                "status": "quote_selected"
            }

            commit_agent = CommitAgent()
            commit_result = commit_agent.process(initial_state)

            if commit_result.get("status") == "error":
                raise HTTPException(status_code=500, detail=commit_result.get("error", "Failed to commit order."))

            return {
                "success": True,
                "message": "Order created successfully!",
                "data": commit_result
            }

        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error selecting quote: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ============================================================================
# STATUS CHECK ENDPOINT
# ============================================================================

@app.get("/api/status/{request_id}", response_model=StatusResponse)
async def get_request_status(request_id: str):
    """
    Check the status of a material request.
    """
    session = get_session()
    try:
        # Query the request
        request = session.query(MaterialRequest).filter_by(id=request_id).first()
        
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        return StatusResponse(
            request_id=request_id,
            status=request.status,
            details={
                "material": request.material,
                "quantity": request.quantity,
                "unit": request.unit,
                "budget": request.budget,
                "created_at": request.created_at.isoformat()
            }
        )
        
    finally:
        session.close()


# ============================================================================
# LIST ALL REQUESTS (FOR DEBUGGING)
# ============================================================================

@app.get("/api/requests")
async def list_all_requests():
    """
    List all material requests (for debugging/admin).
    """
    session = get_session()
    try:
        requests = session.query(MaterialRequest).order_by(
            MaterialRequest.created_at.desc()
        ).limit(50).all()
        
        return {
            "total": len(requests),
            "requests": [
                {
                    "id": req.id,
                    "artisan_id": req.artisan_id,
                    "material": req.material,
                    "quantity": req.quantity,
                    "budget": req.budget,
                    "status": req.status,
                    "created_at": req.created_at.isoformat()
                }
                for req in requests
            ]
        }
        
    finally:
        session.close()


# ============================================================================
# ARTISAN ENDPOINTS
# ============================================================================

@app.get("/api/artisan/{artisan_id}")
async def get_artisan_info(artisan_id: str):
    """
    Get artisan information and their requests.
    """
    session = get_session()
    try:
        artisan = session.query(Artisan).filter_by(id=artisan_id).first()
        
        if not artisan:
            raise HTTPException(status_code=404, detail="Artisan not found")
        
        # Get their requests
        requests = session.query(MaterialRequest).filter_by(
            artisan_id=artisan_id
        ).order_by(MaterialRequest.created_at.desc()).all()
        
        return {
            "artisan": {
                "id": artisan.id,
                "name": artisan.name,
                "phone": artisan.phone,
                "location": artisan.location,
                "created_at": artisan.created_at.isoformat()
            },
            "requests": [
                {
                    "id": req.id,
                    "material": req.material,
                    "quantity": req.quantity,
                    "status": req.status,
                    "created_at": req.created_at.isoformat()
                }
                for req in requests
            ]
        }
        
    finally:
        session.close()


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n🚀 Starting KarigarAgent Backend Server...")
    print("📡 Server will be available at: http://localhost:8000")
    print("📚 API Documentation at: http://localhost:8000/docs\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )