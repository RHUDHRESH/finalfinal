from typing import Dict, List, Optional

import httpx

class SupplierSearchTool:
    def __init__(self, perplexity_api_key: Optional[str] = None):
        self.api_key = perplexity_api_key
        self.local_suppliers = self._load_local_suppliers()

    def _load_local_suppliers(self) -> Dict[str, List[Dict]]:
        """Return a small in-memory catalogue of suppliers grouped by material."""
        return {
            "cement": [
                {
                    "id": "supplier_buildmart_delhi",
                    "name": "BuildMart Delhi",
                    "city": "Delhi",
                    "phone": "+91-9123456780",
                    "address": "Sector 15, Noida",
                    "state": "Delhi NCR",
                    "materials": ["cement", "sand", "steel"],
                    "rating": 4.6,
                    "total_reviews": 128,
                    "delivery_radius_km": 50,
                    "base_price": 360.0
                },
                {
                    "id": "supplier_quick_supply_noida",
                    "name": "Quick Supply Co",
                    "city": "Noida",
                    "phone": "+91-9123456781",
                    "address": "Sector 62, Noida",
                    "state": "Uttar Pradesh",
                    "materials": ["cement", "bricks", "tiles"],
                    "rating": 4.3,
                    "total_reviews": 98,
                    "delivery_radius_km": 50,
                    "base_price": 370.0
                },
                {
                    "id": "supplier_metro_builders",
                    "name": "Metro Builders Supply",
                    "city": "Delhi",
                    "phone": "+91-9123456782",
                    "address": "Dwarka, Delhi",
                    "state": "Delhi",
                    "materials": ["cement", "steel", "paint"],
                    "rating": 4.7,
                    "total_reviews": 205,
                    "delivery_radius_km": 50,
                    "base_price": 365.0
                }
            ],
            "bricks": [
                {
                    "id": "supplier_brickmart_gurgaon",
                    "name": "BrickMart Gurgaon",
                    "city": "Gurgaon",
                    "phone": "+91-9123456783",
                    "address": "Udyog Vihar, Gurgaon",
                    "state": "Haryana",
                    "materials": ["bricks", "cement"],
                    "rating": 4.4,
                    "total_reviews": 76,
                    "delivery_radius_km": 50,
                    "base_price": 9.0
                }
            ],
            "steel": [
                {
                    "id": "supplier_steelhub_delhi",
                    "name": "SteelHub",
                    "city": "Delhi",
                    "phone": "+91-9123456784",
                    "address": "Naraina Industrial Area, Delhi",
                    "state": "Delhi",
                    "materials": ["steel", "cement"],
                    "rating": 4.5,
                    "total_reviews": 142,
                    "delivery_radius_km": 60,
                    "base_price": 58.0
                }
            ]
        }

    async def search(
        self,
        material: str,
        location: Optional[str] = None,
        max_distance_km: float = 50,
        use_web_fallback: bool = False
    ) -> List[Dict]:
        """Search for suppliers matching the criteria."""
        if not material:
            return []

        material_key = material.lower()
        local_results = list(self.local_suppliers.get(material_key, []))

        filtered_local = [
            supplier for supplier in local_results
            if supplier.get("delivery_radius_km", 0) >= max_distance_km or max_distance_km <= 0
        ]

        if filtered_local:
            return filtered_local

        if use_web_fallback and self.api_key:
            web_results = await self._perplexity_search(material, location or "")
            return web_results

        return local_results

    async def _perplexity_search(self, material: str, location: str) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Find 3 suppliers for {material} in {location} with prices"
                        }
                    ]
                }
            )
            data = response.json()
            return self._parse_perplexity_response(data)

    def _parse_perplexity_response(self, response: Dict) -> List[Dict]:
        """Parse Perplexity API response. Placeholder returning empty list."""
        # TODO: Implement real parsing when Perplexity integration is enabled.
        return []
