from dataclasses import dataclass
from typing import Optional

@dataclass
class IdentityModel:
    subscription_id: int
    subscription_name: str
    employee_code: str
    name: str
    is_admin: bool
    is_manager: bool
    photo: Optional[str] = None
    employee_id: int = 0
    email: Optional[str] = None
    country_id: Optional[str] = None
    cycle_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

@dataclass
class OBIdentityModel:
    subscription_name: str
    user_id: str
    role_description: str

@dataclass
class ApplicantPortalIdentityModel:
    subscription_name: str
    user_id: str
    role_description: str
