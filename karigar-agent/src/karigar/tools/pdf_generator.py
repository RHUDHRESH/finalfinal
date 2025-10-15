from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


class PDFGenerator:
    """Utility for generating purchase order PDFs."""

    UPLOAD_DIR = Path("./uploads/pdfs")

    def __init__(self) -> None:
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def generate_purchase_order(self, order_data: dict, order_id: str) -> str:
        filename = f"PO_{order_id}.pdf"
        filepath = self.UPLOAD_DIR / filename

        c = canvas.Canvas(str(filepath), pagesize=letter)
        width, height = letter

        c.setFont("Helvetica-Bold", 20)
        c.drawString(72, height - 72, "PURCHASE ORDER")

        y = height - 120
        c.setFont("Helvetica", 12)
        c.drawString(72, y, f"PO Number: {order_id}")
        y -= 18
        c.drawString(72, y, f"Date: {datetime.utcnow().strftime('%Y-%m-%d')}")

        y -= 36
        c.setFont("Helvetica-Bold", 14)
        c.drawString(72, y, "Buyer Details")
        y -= 18
        c.setFont("Helvetica", 12)
        c.drawString(72, y, f"Name: {order_data.get('buyer_name', 'N/A')}")
        y -= 16
        c.drawString(72, y, f"Phone: {order_data.get('buyer_phone', 'N/A')}")
        y -= 16
        c.drawString(72, y, f"Address: {order_data.get('buyer_address', 'N/A')}")

        y -= 32
        c.setFont("Helvetica-Bold", 14)
        c.drawString(72, y, "Supplier Details")
        y -= 18
        c.setFont("Helvetica", 12)
        c.drawString(72, y, f"Name: {order_data.get('supplier_name', 'N/A')}")
        y -= 16
        c.drawString(72, y, f"Phone: {order_data.get('supplier_phone', 'N/A')}")

        y -= 32
        c.setFont("Helvetica-Bold", 14)
        c.drawString(72, y, "Items")
        y -= 18

        c.setFont("Helvetica-Bold", 12)
        c.drawString(72, y, "Item")
        c.drawString(260, y, "Quantity")
        c.drawString(360, y, "Rate")
        c.drawString(450, y, "Amount")
        y -= 14
        c.line(72, y, width - 72, y)
        y -= 14

        c.setFont("Helvetica", 12)
        for item in order_data.get("items", []):
            c.drawString(72, y, str(item.get("name", "")))
            c.drawString(260, y, str(item.get("quantity", "")))
            c.drawString(360, y, f"₹{float(item.get('rate', 0)):.2f}")
            c.drawString(450, y, f"₹{float(item.get('amount', 0)):.2f}")
            y -= 16

        y -= 8
        c.line(72, y, width - 72, y)
        y -= 20

        total = float(order_data.get("total_amount", 0))
        delivery = float(order_data.get("delivery_charge", 0))
        grand_total = total + delivery

        c.setFont("Helvetica-Bold", 12)
        c.drawString(360, y, "Subtotal:")
        c.drawString(450, y, f"₹{total:.2f}")
        y -= 16
        c.setFont("Helvetica", 12)
        c.drawString(360, y, "Delivery:")
        c.drawString(450, y, f"₹{delivery:.2f}")
        y -= 16
        c.setFont("Helvetica-Bold", 12)
        c.drawString(360, y, "Total:")
        c.drawString(450, y, f"₹{grand_total:.2f}")

        c.setFont("Helvetica-Oblique", 10)
        c.drawString(72, 72, "This is a computer generated document and does not require a signature.")

        c.save()

        return str(filepath)
