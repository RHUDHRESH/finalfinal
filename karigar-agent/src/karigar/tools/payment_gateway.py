import razorpay

class PaymentGateway:
    def __init__(self, key_id: str, key_secret: str):
        self.client = razorpay.Client(auth=(key_id, key_secret))
    
    def create_order(self, amount: float, currency: str = "INR"):
        """Create Razorpay order"""
        return self.client.order.create({
            "amount": int(amount * 100),  # Amount in paise
            "currency": currency,
            "payment_capture": 1
        })
    
    def verify_payment(self, payment_id: str, order_id: str, signature: str):
        """Verify payment signature"""
        try:
            self.client.utility.verify_payment_signature({
                "razorpay_payment_id": payment_id,
                "razorpay_order_id": order_id,
                "razorpay_signature": signature
            })
            return True
        except:
            return False
