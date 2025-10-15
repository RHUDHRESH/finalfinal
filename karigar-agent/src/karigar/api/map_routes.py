from fastapi import APIRouter, HTTPException
from karigar.tools.location_tools import LocationTools
from karigar.memory.sql_memory import get_session

router = APIRouter(prefix="/api/map", tags=["maps"])

@router.get("/artisan/{artisan_id}")
async def get_artisan_map_data(artisan_id: str):
    """Get artisan location and nearby suppliers"""
    session = get_session()
    
    # Get artisan location
    artisan_loc = session.query(Location).filter_by(
        entity_type="artisan",
        entity_id=artisan_id
    ).first()
    
    if not artisan_loc:
        raise HTTPException(404, "Artisan location not found")
    
    # Find nearby suppliers
    suppliers = await LocationTools.find_suppliers_nearby(
        (artisan_loc.latitude, artisan_loc.longitude),
        max_distance_km=50
    )
    
    return {
        "location": {
            "lat": artisan_loc.latitude,
            "lng": artisan_loc.longitude,
            "address": artisan_loc.address
        },
        "nearby_suppliers": suppliers
    }

@router.post("/route")
async def get_route(data: dict):
    """Get route between two points"""
    start = (data["start"]["lat"], data["start"]["lng"])
    end = (data["end"]["lat"], data["end"]["lng"])
    
    route = await LocationTools.get_route(start, end)
    return route

@router.post("/geocode")
async def geocode_address(address: str):
    """Convert address to coordinates"""
    lat, lng = await LocationTools.geocode_address(address)
    return {"lat": lat, "lng": lng}

@router.get("/tracking/{order_id}")
async def track_delivery(order_id: str):
    """Get real-time delivery location"""
    session = get_session()
    tracking = session.query(DeliveryTracking).filter_by(order_id=order_id).first()
    
    if not tracking:
        raise HTTPException(404, "Tracking not found")
    
    return {
        "current_location": {
            "lat": tracking.current_lat,
            "lng": tracking.current_lng
        },
        "status": tracking.status,
        "eta": tracking.estimated_arrival
    }