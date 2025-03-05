# from MicroServices.ZingAuth.Application.Integration.Models.WorkFlowGroupDetails import ResponseModel
# from pydantic import BaseModel, Field

# class LoginCommand(BaseModel):
#     """Command to handle user login"""
    
#     subscription_name: str = Field(..., description="The subscription name for the tenant")
#     emp_code: str = Field(..., description="Employee code/username")
#     password: str = Field(..., description="User password")
    
#     class Config:
#         schema_extra = {
#             "example": {
#                 "subscription_name": "qadb",
#                 "emp_code": "EMP001",
#                 "password": "password123",
#             }
#         }
# MicroServices/ZingAuth/Application/AppLogics/AuthToken/Commands/LoginCommand.py
from pydantic import BaseModel
from typing import Optional

class LoginCommand(BaseModel):
    subscription_name: Optional[str] = None
    emp_code: Optional[str] = None
    proxy_emp_code: Optional[str] = None
    password: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    computer_name: Optional[str] = None
    guid: Optional[str] = None
    session_id: Optional[str] = None
    latitude: Optional[float] = 0.0
    longitude: Optional[float] = 0.0
    location: Optional[str] = None
    source: Optional[str] = None
    kill_previous_session: bool = False
    proxy_creator: bool = False
    user_type: str = "E"
    app_version: Optional[str] = None
    device_id: Optional[str] = None
    signup_id: Optional[int] = None  # Added signup_id as an optional integer
