from pydantic import BaseModel, Field

class VerifyOTPCommand(BaseModel):
    """Command to verify OTP and login user"""
    
    subscription_name: str = Field(..., description="The subscription name for the tenant")
    phone_number: str = Field(..., pattern=r'^\+?1?\d{9,15}$', description="Phone number in international format (E.164)")
    otp: str = Field(..., pattern=r'^\d{6}$', description="6-digit OTP code")
    reference_id: str = Field(..., description="Reference ID received from send-otp endpoint")
    
    class Config:
        schema_extra = {
            "example": {
                "subscription_name": "qadb",
                "phone_number": "+919876543210",
                "otp": "123456",
                "reference_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        } 