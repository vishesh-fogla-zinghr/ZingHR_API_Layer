# app/schemas/claims_schema.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ClaimBase(BaseModel):
    claim_number: str
    user_id: int
    amount: float
    status: Optional[str] = "pending"

class ClaimCreate(ClaimBase):
    pass

class ClaimUpdate(BaseModel):
    amount: Optional[float] = None
    status: Optional[str] = None

class Claim(ClaimBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
