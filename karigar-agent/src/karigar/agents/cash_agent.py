"""
CashAgent: Manages the financial ledger for each artisan.
"""

from karigar.schemas.state import KarigarState
from karigar.memory.sql_memory import get_session
from karigar.schemas.models import Ledger, Artisan
from sqlalchemy import func

class CashAgent:
    """
    Records all financial transactions in the Ledger table to maintain a
    running balance for each artisan.
    """

    def process(self, state: KarigarState) -> dict:
        """
        Process the state to record a transaction in the ledger.
        
        Args:
            state: Current workflow state
            
        Returns:
            Dictionary with updates to state
        """
        try:
            artisan_id = state.get("artisan_id")
            order_id = state.get("order_id")
            order_details = state.get("order_details")

            if not all([artisan_id, order_id, order_details]):
                print("\n[CashAgent] Skipping, missing details for ledger entry.")
                return {"status": "cash_skipped"}

            print(f"\n[CashAgent] Recording transaction for order {order_id} in ledger.")

            session = get_session()
            try:
                # Get the artisan's current balance
                last_entry = session.query(Ledger).filter_by(artisan_id=artisan_id).order_by(Ledger.timestamp.desc()).first()
                current_balance = last_entry.balance_after if last_entry else 0

                # Create a debit entry for the material purchase
                amount = order_details.get("total_amount", 0)
                new_balance = current_balance - amount

                ledger_entry = Ledger(
                    artisan_id=artisan_id,
                    order_id=order_id,
                    type="debit",
                    amount=amount,
                    description=f"Material purchase for order {order_id}",
                    category="material_purchase",
                    balance_after=new_balance
                )

                session.add(ledger_entry)
                session.commit()

                print(f"[CashAgent] Ledger entry created. Artisan new balance: {new_balance}")

                return {"status": "cash_complete"}

            except Exception as e:
                session.rollback()
                print(f"[CashAgent] Database error: {e}")
                return {"status": "error", "error": f"DB Error: {str(e)}"}
            finally:
                session.close()

        except Exception as e:
            print(f"[CashAgent] Error: {e}")
            return {"status": "error", "error": str(e)}