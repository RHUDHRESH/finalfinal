"""
SupplierAgent: Finds suppliers and gets quotes for material requests.
"""

import os

from karigar.schemas.state import KarigarState
from karigar.tools.quote_generator import QuoteGeneratorTool
from karigar.tools.supplier_search import SupplierSearchTool

class SupplierAgent:
    """
    Uses the SupplierSearchTool to find potential suppliers and the
    QuoteGeneratorTool to create quotes for a given material request.
    """
    
    def __init__(self):
        """Initialize the agent with necessary tools."""
        self.search_tool = SupplierSearchTool(perplexity_api_key=os.getenv("PERPLEXITY_API_KEY"))
        self.quote_tool = QuoteGeneratorTool()
    
    async def process(self, state: KarigarState) -> dict:
        """
        Process the state to find suppliers and generate quotes.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with updates to state
        """
        try:
            request_id = state.get("request_id")
            material_request = state.get("material_request")
            
            if not request_id or not material_request:
                return {"status": "error", "error": "Missing material request details."}

            print(f"\n[SupplierAgent] Finding suppliers for request: {request_id}")

            # Find suppliers
            suppliers = await self.search_tool.search(
                material=material_request["material"],
                location=material_request.get("location", "Delhi"),
                use_web_fallback=False # Keep this false for now to avoid API costs
            )

            if not suppliers:
                print("[SupplierAgent] No suppliers found.")
                return {"status": "error", "error": "No suppliers found for the material and location."}

            print(f"[SupplierAgent] Found {len(suppliers)} suppliers. Generating quotes...")

            # Generate and save quotes
            quotes = self.quote_tool.generate_quotes_for_request(
                request_id=request_id,
                suppliers=suppliers
            )

            if not quotes:
                return {"status": "error", "error": "Failed to generate quotes."}

            # Convert SQLAlchemy objects to dicts for state
            quotes_list = [
                {
                    "id": q.id,
                    "supplier_id": q.supplier_id,
                    "price_per_unit": q.price_per_unit,
                    "total_price": q.total_price,
                    "delivery_charge": q.delivery_charge,
                    "delivery_days": q.delivery_days
                } for q in quotes
            ]
            
            print(f"[SupplierAgent] Generated {len(quotes_list)} quotes.")

            return {
                "supplier_quotes": quotes_list,
                "status": "supplier_search_complete"
            }

        except Exception as e:
            print(f"[SupplierAgent] Error: {e}")
            return {"status": "error", "error": str(e)}
