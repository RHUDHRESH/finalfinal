from fastapi import APIRouter, Depends, File, UploadFile
from pathlib import Path
from karigar.tools.image_tools import ImageTools
from karigar.api.auth_routes import get_current_user
from karigar.memory.sql_memory import get_session
from karigar.schemas.models import Review, Order # Assuming Supplier model exists

router = APIRouter(prefix="/api", tags=["misc"])

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    """Upload product/profile image"""
    contents = await file.read()
    filepath = ImageTools.save_image(contents)
    return {"url": f"/images/{Path(filepath).name}"}

@router.post("/reviews")
async def create_review(review: dict, user_id: str = Depends(get_current_user)):
    """Submit a review after order completion"""
    pass

@router.get("/reviews/supplier/{supplier_id}")
async def get_supplier_reviews(supplier_id: str):
    """Get all reviews for a supplier"""
    pass

@router.get("/suppliers/search")
async def search_suppliers(
    material: str = None,
    min_rating: float = None,
    max_distance_km: float = None,
    sort_by: str = "rating"  # 'rating', 'price', 'distance'
):
    """Advanced supplier search with filters"""
    # from karigar.schemas.models import Supplier # Import here to avoid circular dependency issues if Supplier model is in the same file
    # query = session.query(Supplier)
    
    # if material:
    #     query = query.filter(Supplier.materials.contains(material))
    
    # if min_rating:
    #     query = query.filter(Supplier.rating >= min_rating)
    
    # # Apply sorting
    # if sort_by == "rating":
    #     query = query.order_by(Supplier.rating.desc())
    
    # return query.all()
    pass
