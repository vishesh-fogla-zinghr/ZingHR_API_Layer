from pydantic import BaseModel
from typing import Optional
   
class RefreshToken(BaseModel):
    """Model for refresh token response"""
    token: str

class ExceptionResponse(BaseModel):
    """Model for exception response"""
    error_message: str

class RefreshTokenCommand(BaseModel):
    """Command to handle token refresh"""
    auth_token: str
    subscription_name: str 
    
class AliveTokenResult(BaseModel):
    """Model for refresh token stored procedure result"""
    signup_id: int
    subscription_name: str
    logged_in_emp_code: str
    salutation: Optional[str] = None
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    employee_photo: Optional[str] = None
    role_description: Optional[str] = None
    role_code: Optional[str] = None
    email: str
    employee_id: int

    @property
    def emp_name(self) -> str:
        """Get the full employee name by concatenating name parts"""
        name_parts = [
            part for part in [
                self.salutation,
                self.first_name,
                self.middle_name,
                self.last_name
            ] if part
        ]
        return " ".join(name_parts)