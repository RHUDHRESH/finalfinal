import httpx
from typing import Tuple, List, Optional
from geopy.distance import geodesic

class LocationTools:
    """All location/map related utilities"""
    
    @staticmethod
    async def geocode_address(address: str) -> Tuple[float, float]:
        """Convert address to lat/lng using Nominatim"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": address,
                    "format": "json",
                    "limit": 1
                },
                headers={"User-Agent": "KarigarApp/1.0"}
            )
            data = response.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
            raise ValueError("Address not found")
    
    @staticmethod
    def calculate_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance in km between two coordinates"""
        return geodesic(coord1, coord2).kilometers
    
    @staticmethod
    async def find_suppliers_nearby(
        artisan_location: Tuple[float, float],
        max_distance_km: float = 50
    ) -> List[dict]:
        """Find suppliers within radius"""
        # Query database for suppliers with coordinates
        # Filter by distance
        pass
    
    @staticmethod
    async def get_route(
        start: Tuple[float, float],
        end: Tuple[float, float]
    ) -> dict:
        """Get optimal route using OSRM"""
        async with httpx.AsyncClient() as client:
            url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}"
            response = await client.get(url, params={"overview": "full", "geometries": "geojson"})
            return response.json()
    
    @staticmethod
    def calculate_delivery_charge(distance_km: float, base_rate: float = 50) -> float:
        """Calculate delivery charge based on distance"""
        if distance_km <= 5:
            return base_rate
        return base_rate + (distance_km - 5) * 10  # ₹10 per km after 5km
