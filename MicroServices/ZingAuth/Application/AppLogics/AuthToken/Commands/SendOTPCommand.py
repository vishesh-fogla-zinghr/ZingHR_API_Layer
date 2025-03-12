from pydantic import BaseModel, Field

class SendOTPCommand(BaseModel):
    """Command for sending OTP"""
    phone_number: str = Field(..., pattern=r'^\+?1?\d{9,15}$', description="Phone number in international format (E.164)")
    subscription_name: str = Field(..., description="The subscription name for the tenant") 