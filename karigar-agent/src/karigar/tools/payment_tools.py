from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import qrcode


class PaymentTools:
    """Utility helpers for generating UPI links and QR codes."""

    UPLOAD_DIR = Path("./uploads/qr_codes")

    def __init__(self) -> None:
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def generate_upi_link(amount: float, upi_id: str, name: str, note: str) -> str:
        base_url = "upi://pay"
        params = (
            f"?pa={upi_id}"
            f"&pn={quote(name)}"
            f"&am={amount:.2f}"
            f"&tn={quote(note)}"
            f"&cu=INR"
        )
        return base_url + params

    def generate_qr_code(self, upi_link: str, order_id: str) -> str:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(upi_link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        filename = f"qr_{order_id or uuid4()}.png"
        filepath = self.UPLOAD_DIR / filename
        img.save(filepath)
        return str(filepath)

    def create_payment_package(
        self,
        order_id: str,
        amount: float,
        merchant_upi: str = "merchant@paytm",
        merchant_name: str = "KarigarAgent"
    ) -> dict:
        upi_link = self.generate_upi_link(
            amount=amount,
            upi_id=merchant_upi,
            name=merchant_name,
            note=f"Order {order_id}"
        )
        qr_path = self.generate_qr_code(upi_link, order_id)

        return {
            "upi_link": upi_link,
            "qr_code_path": qr_path,
            "amount": round(amount, 2)
        }
