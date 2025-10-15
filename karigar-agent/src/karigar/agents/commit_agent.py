"""
CommitAgent: Selects the best quote and creates a formal order.
"""

from karigar.schemas.state import KarigarState
from karigar.tools.payment_tools import PaymentTools
from karigar.tools.pdf_generator import PDFGenerator
from karigar.memory.sql_memory import get_session
from karigar.schemas.models import Order, SupplierQuote, Artisan, Supplier, MaterialRequest

class CommitAgent:
    """
    Selects the best quote, creates an Order record, generates a Purchase Order (PO),
    and creates a payment link.
    """
    
    def __init__(self):
        """Initialize the agent with necessary tools."""
        self.payment_tool = PaymentTools()
        self.pdf_tool = PDFGenerator()

    def process(self, state: KarigarState) -> dict:
        """
        Process the state to commit to an order.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with updates to state
        """
        try:
            quotes = state.get("supplier_quotes")
            request_id = state.get("request_id")
            artisan_id = state.get("artisan_id")

            if not quotes:
                return {"status": "error", "error": "No supplier quotes available to commit."}

            print(f"\n[CommitAgent] Selecting best quote from {len(quotes)} options.")

            # Simple selection logic: choose the cheapest quote
            selected_quote_dict = min(quotes, key=lambda q: q["total_price"] + q["delivery_charge"])
            
            print(f"[CommitAgent] Selected quote ID: {selected_quote_dict['id']}")

            session = get_session()
            try:
                # Get full objects from DB for PO generation
                quote_obj = session.query(SupplierQuote).filter_by(id=selected_quote_dict['id']).first()
                artisan_obj = session.query(Artisan).filter_by(id=artisan_id).first()
                supplier_obj = session.query(Supplier).filter_by(id=quote_obj.supplier_id).first()
                request_obj = session.query(MaterialRequest).filter_by(id=request_id).first()

                if not all([quote_obj, artisan_obj, supplier_obj, request_obj]):
                    return {"status": "error", "error": "Could not retrieve full order details from DB."}

                # Mark quote as selected
                quote_obj.selected = True

                total_amount = quote_obj.total_price + quote_obj.delivery_charge

                # Create Order in DB
                new_order = Order(
                    artisan_id=artisan_id,
                    request_id=request_id,
                    quote_id=quote_obj.id,
                    total_amount=total_amount,
                    status="confirmed"
                )
                session.add(new_order)
                session.commit()
                session.refresh(new_order)
                order_id = new_order.id

                print(f"[CommitAgent] Created Order {order_id} in database.")

                # Generate payment package (UPI link + QR code)
                payment_package = self.payment_tool.create_payment_package(
                    order_id=order_id,
                    amount=total_amount,
                    merchant_name=supplier_obj.name
                )
                new_order.upi_link = payment_package["upi_link"]

                # Generate Purchase Order PDF
                po_data = {
                    "buyer_name": artisan_obj.name,
                    "buyer_phone": artisan_obj.phone,
                    "buyer_address": artisan_obj.location,
                    "supplier_name": supplier_obj.name,
                    "supplier_phone": supplier_obj.phone,
                    "items": [
                        {
                            "name": f"{request_obj.material} ({request_obj.unit})",
                            "quantity": request_obj.quantity,
                            "rate": quote_obj.price_per_unit,
                            "amount": quote_obj.total_price
                        }
                    ],
                    "total_amount": quote_obj.total_price,
                    "delivery_charge": quote_obj.delivery_charge
                }
                po_path = self.pdf_tool.generate_purchase_order(po_data, order_id)
                new_order.po_path = po_path

                # Commit all changes to the order
                session.commit()

                print(f"[CommitAgent] Generated PO: {po_path} and Payment Link: {payment_package['upi_link']}")

                return {
                    "order_id": order_id,
                    "selected_quote": selected_quote_dict,
                    "order_details": {
                        "total_amount": total_amount,
                        "status": "confirmed"
                    },
                    "payment_info": payment_package,
                    "po_path": po_path,
                    "status": "commit_complete"
                }

            except Exception as e:
                session.rollback()
                print(f"[CommitAgent] Database or file generation error: {e}")
                return {"status": "error", "error": f"DB/File Error: {str(e)}"}
            finally:
                session.close()

        except Exception as e:
            print(f"[CommitAgent] Error: {e}")
            return {"status": "error", "error": str(e)}