from MicroServices.ZingAuth.Application.Integration.Models.WorkFlowGroupDetails import ResponseModel
from pydantic import BaseModel, Field
from typing import Optional


class LoginCommand(BaseModel):
    """Command to handle user login"""
    
    subscription_name: str = Field(..., description="The subscription name for the tenant")
    emp_code: str = Field(..., description="Employee code/username")
    password: Optional[str] = Field(None, description="User password (not required for OTP login)")
    is_otp_login: bool = Field(False, description="Whether this is an OTP-based login")

    
    class Config:
        schema_extra = {
            "example": {
                "subscription_name": "qadb",
                "emp_code": "EMP001",
                "password": "password123",
                "is_otp_login": False

            }
        }
