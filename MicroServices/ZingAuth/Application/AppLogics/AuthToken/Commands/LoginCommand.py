from pydiator_core.interfaces import BaseRequest
from zinghr_backend.app.MicroServices.ZingAuth.Application.Integration.Models.WorkFlowGroupDetails import ResponseModel
from pydantic import BaseModel


class LoginCommand(BaseModel, BaseRequest):
    """Command to handle user login"""
    
    subscription_name: str
    emp_code: str
    password: str
    mac_address: str
    session_id: str
    latitude: str
    longitude: str
    source: str
    user_type: str = "E"
    application_version: str | None = None  # Optional field
    formatted_address: str | None = None  # Optional field