import httpx
from typing import List

class NotificationService:
    @staticmethod
    async def send_push(user_id: str, title: str, body: str):
        """Send push notification (using Firebase Cloud Messaging)"""
        # Get user's FCM token from database
        # Send via FCM API
        pass
    
    @staticmethod
    async def send_whatsapp(phone: str, message: str):
        """Send WhatsApp message via Twilio/WATI"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.twilio.com/2010-04-01/Accounts/{ACCOUNT_SID}/Messages.json",
                auth=("SID", "TOKEN"),
                data={
                    "From": "whatsapp:+14155238886",
                    "To": f"whatsapp:{phone}",
                    "Body": message
                }
            )
            return response.json()
    
    @staticmethod
    async def send_sms(phone: str, message: str):
        """Send SMS via Twilio/MSG91"""
        pass
