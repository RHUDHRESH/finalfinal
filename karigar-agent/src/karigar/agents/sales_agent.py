"""
SalesAgent: Creates a micro-store for the artisan to sell products.
"""

from karigar.schemas.state import KarigarState
from karigar.tools.store_generator import StoreGenerator
from karigar.memory.sql_memory import get_session
from karigar.schemas.models import MicroStore, Artisan

class SalesAgent:
    """
    Creates a simple, shareable micro-store (product page) for an artisan.
    This helps artisans showcase their work and get direct orders.
    """
    
    def __init__(self):
        """Initialize the agent with necessary tools."""
        self.store_tool = StoreGenerator()

    def process(self, state: KarigarState) -> dict:
        """
        Process the state to create a micro-store.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with updates to state
        """
        try:
            artisan_id = state.get("artisan_id")
            order_details = state.get("order_details") # Using order details as a trigger

            # The SalesAgent might not run for every transaction.
            # For this MVP, we'll create a store based on the first successful order.
            if not artisan_id or not order_details:
                print("\n[SalesAgent] Skipping, no artisan or order details found.")
                return {"status": "sales_skipped"}

            print(f"\n[SalesAgent] Checking if a store should be created for artisan {artisan_id}")

            session = get_session()
            try:
                # For simplicity, create one store per artisan
                existing_store = session.query(MicroStore).filter_by(artisan_id=artisan_id).first()
                if existing_store:
                    print(f"[SalesAgent] Artisan {artisan_id} already has a store. Skipping.")
                    return {"store_url": existing_store.store_url, "status": "sales_skipped"}

                artisan = session.query(Artisan).filter_by(id=artisan_id).first()
                if not artisan:
                    return {"status": "error", "error": "Artisan not found."}

                # Create a product based on the artisan's profile (this is a simplified example)
                product_data = {
                    "name": f"{artisan.name}'s Handiwork",
                    "description": f"Beautiful, handcrafted products by {artisan.name}. Contact at {artisan.phone}.",
                    "price": 500.00,
                    "image": "https://via.placeholder.com/600x400?text=Karigar+Store",
                    "phone": artisan.phone
                }

                # Generate the static HTML page for the store
                store_path, store_url = self.store_tool.create_store_page(
                    artisan_name=artisan.name,
                    product=product_data
                )

                # Save the store to the database
                new_store = MicroStore(
                    artisan_id=artisan_id,
                    product_name=product_data["name"],
                    description=product_data["description"],
                    price=product_data["price"],
                    image_path=product_data["image"],
                    store_url=store_url,
                    is_active=True
                )
                session.add(new_store)
                session.commit()
                session.refresh(new_store)
                store_id = new_store.id

                print(f"[SalesAgent] Created MicroStore {store_id} at URL: {store_url}")

                return {
                    "store_id": store_id,
                    "store_url": store_url,
                    "status": "sales_complete"
                }

            except Exception as e:
                session.rollback()
                print(f"[SalesAgent] Database or file error: {e}")
                return {"status": "error", "error": f"DB/File Error: {str(e)}"}
            finally:
                session.close()

        except Exception as e:
            print(f"[SalesAgent] Error: {e}")
            return {"status": "error", "error": str(e)}