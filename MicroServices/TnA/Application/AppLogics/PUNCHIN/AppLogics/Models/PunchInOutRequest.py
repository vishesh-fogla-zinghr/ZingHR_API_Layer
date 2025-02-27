from typing import Optional
from pydantic import BaseModel, Field

class PunchInOutRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: str = ""
    formatted_address: str = ""
    application_version: str
    device_id: str
    is_request_from_mobile: bool = True
    selfie_path: Optional[str] = None
    type: str = ""
    late_coming_reason: str = Field(default="", regex=r"^[^<>]*$")  
