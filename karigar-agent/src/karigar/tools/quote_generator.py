"""
Tool for generating supplier quotes.
"""

import random
from karigar.memory.sql_memory import get_session
from karigar.schemas.models import MaterialRequest, SupplierQuote, Supplier

class QuoteGeneratorTool:
    """
    Generates quotes from suppliers for a given material request.
    In a real-world scenario, this would involve calling supplier APIs or sending emails.
    Here, we simulate it by generating random quotes based on the request budget.
    """

    def generate_quotes_for_request(self, request_id: str, suppliers: list[dict]) -> list[SupplierQuote]:
        """
        Generates and saves quotes for a material request from a list of suppliers.

        Args:
            request_id: The ID of the material request.
            suppliers: A list of supplier dictionaries, as returned by the SupplierSearchTool.

        Returns:
            A list of saved SupplierQuote ORM objects.
        """
        session = get_session()
        try:
            # Get the material request from the database
            material_request = session.query(MaterialRequest).filter_by(id=request_id).first()
            if not material_request:
                raise ValueError(f"MaterialRequest with id {request_id} not found.")

            created_quotes = []
            budget = material_request.budget
            quantity = material_request.quantity

            # Base price per unit from budget, or a default if budget is zero
            base_price_per_unit = (budget / quantity) if quantity > 0 and budget > 0 else 50.0

            for supplier_data in suppliers:
                supplier_id = supplier_data.get("id")
                if not supplier_id:
                    continue

                # Check if supplier exists in DB, otherwise create it
                supplier = session.query(Supplier).filter_by(id=supplier_id).first()
                if not supplier:
                    supplier = Supplier(
                        id=supplier_id,
                        name=supplier_data.get("name", "Unknown Supplier"),
                        phone=supplier_data.get("phone"),
                        email=supplier_data.get("email"),
                        address=supplier_data.get("address"),
                        city=supplier_data.get("city", "Unknown City"),
                        state=supplier_data.get("state"),
                        delivery_radius_km=supplier_data.get("delivery_radius_km", 0),
                        materials=supplier_data.get("materials", []),
                        rating=supplier_data.get("rating", 3.0),
                        total_reviews=supplier_data.get("total_reviews", 0)
                    )
                    session.add(supplier)
                    session.flush()

                # Simulate price variation (e.g., 80% to 150% of base price)
                base_price = supplier_data.get("base_price", base_price_per_unit)
                price_per_unit = base_price * random.uniform(0.9, 1.1)
                total_price = price_per_unit * quantity
                delivery_charge = random.uniform(100, 500)
                delivery_days = random.randint(1, 5)

                # Create a new quote
                new_quote = SupplierQuote(
                    request_id=request_id,
                    supplier_id=supplier.id,
                    price_per_unit=round(price_per_unit, 2),
                    total_price=round(total_price, 2),
                    delivery_charge=round(delivery_charge, 2),
                    delivery_days=delivery_days,
                )
                session.add(new_quote)
                created_quotes.append(new_quote)

            # Commit all new quotes to the database
            session.commit()

            # Refresh objects to get DB-assigned values
            for quote in created_quotes:
                session.refresh(quote)

            print(f"[QuoteGeneratorTool] Generated and saved {len(created_quotes)} quotes for request {request_id}")
            return created_quotes

        except Exception as e:
            session.rollback()
            print(f"[QuoteGeneratorTool] Error generating quotes: {e}")
            return []
        finally:
            session.close()
