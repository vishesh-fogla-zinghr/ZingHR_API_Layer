from MicroServices.ZingAuth.Application.Integration.Models.WorkFlowGroupDetails import ResponseModel
from pydantic import BaseModel, Field

class LoginCommand(BaseModel):
    """Command to handle user login"""
    
    subscription_name: str = Field(..., description="The subscription name for the tenant")
    emp_code: str = Field(..., description="Employee code/username")
    password: str = Field(..., description="User password")
    
    class Config:
        schema_extra = {
            "example": {
                "subscription_name": "qadb",
                "emp_code": "EMP001",
                "password": "password123",
            }
        }
