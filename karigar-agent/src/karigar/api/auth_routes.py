from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

router = APIRouter(prefix="/api/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"])
security = HTTPBearer()

SECRET_KEY = "your-secret-key-change-this"

@router.post("/signup")
async def signup(data: dict):
    """Register new artisan/supplier"""
    # Check if phone/email exists
    # Send OTP
    # Create user after OTP verification
    pass

@router.post("/login")
async def login(phone: str, password: str):
    """Login with phone and password"""
    # Verify credentials
    # Generate JWT token
    token = jwt.encode(
        {"user_id": "123", "exp": datetime.utcnow() + timedelta(days=30)},
        SECRET_KEY
    )
    return {"token": token}

@router.post("/verify-otp")
async def verify_otp(phone: str, otp: str):
    """Verify OTP for signup/login"""
    pass

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except:
        raise HTTPException(401, "Invalid token")