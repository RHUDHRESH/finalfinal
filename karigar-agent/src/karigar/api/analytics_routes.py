from fastapi import APIRouter, Depends
from karigar.memory.sql_memory import get_session
from karigar.schemas.models import Order, MaterialRequest
from sqlalchemy import func
from karigar.api.auth_routes import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/overview")
async def get_analytics(user_id: str = Depends(get_current_user)):
    """Get user's business analytics"""
    session = get_session()
    
    # Total orders
    total_orders = session.query(Order).filter_by(artisan_id=user_id).count()
    
    # Total revenue
    total_revenue = session.query(func.sum(Order.amount)).filter_by(
        artisan_id=user_id,
        status="completed"
    ).scalar()
    
    # Popular materials
    popular_materials = session.query(
        MaterialRequest.material,
        func.count(MaterialRequest.id)
    ).filter_by(artisan_id=user_id).group_by(MaterialRequest.material).all()
    
    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "popular_materials": popular_materials,
        # ... more metrics
    }