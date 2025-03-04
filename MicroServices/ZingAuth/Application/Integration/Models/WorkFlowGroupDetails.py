from typing import Generic, TypeVar, Optional, Any
from dataclasses import dataclass
from pydantic import BaseModel

# Type variable for generic class
T = TypeVar("T")

@dataclass
class WorkFlowGroupDetail:
    group_id: int  # Equivalent to long in C#
    description: str = ""  # Default empty string
    menu_group: int = 0  # Assuming default value is 0

class ResponseModel(BaseModel):
    code: int
    message: Optional[str] = None
    data: Optional[Any] = None