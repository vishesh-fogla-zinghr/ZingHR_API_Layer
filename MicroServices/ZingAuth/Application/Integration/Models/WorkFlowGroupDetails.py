from typing import Generic, TypeVar
from dataclasses import dataclass
from pydantic import BaseModel

# Type variable for generic class
T = TypeVar("T")

@dataclass
class WorkFlowGroupDetail:
    group_id: int  # Equivalent to long in C#
    description: str = ""  # Default empty string
    menu_group: int = 0  # Assuming default value is 0

@dataclass
class ResponseModel(BaseModel, Generic[T]):
    data: T