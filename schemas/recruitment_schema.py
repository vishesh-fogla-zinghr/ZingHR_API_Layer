# app/schemas/recruitment_schema.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RecruitmentBase(BaseModel):
    candidate_name: str
    position: str
    status: Optional[str] = "applied"

class RecruitmentCreate(RecruitmentBase):
    pass

class RecruitmentUpdate(BaseModel):
    candidate_name: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None

class Recruitment(RecruitmentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
