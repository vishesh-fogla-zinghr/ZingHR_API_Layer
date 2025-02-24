# app/models/recruitment_model.py
from sqlalchemy import Column, Integer, String, DateTime, func
from app.database.cockroach_connector import CockroachBase

class Recruitment(CockroachBase):
    __tablename__ = "recruitments"

    id = Column(Integer, primary_key=True, index=True)
    candidate_name = Column(String(100), nullable=False)
    position = Column(String(100), nullable=False)
    status = Column(String(50), default="applied")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
