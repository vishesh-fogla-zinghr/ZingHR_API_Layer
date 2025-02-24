# app/repositories/recruitment_repository.py
from sqlalchemy.orm import Session
from app.models.recruitment_model import Recruitment
from app.schemas.recruitment_schema import RecruitmentCreate, RecruitmentUpdate

def get_recruitment(db: Session, recruitment_id: int):
    return db.query(Recruitment).filter(Recruitment.id == recruitment_id).first()

def get_recruitments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Recruitment).offset(skip).limit(limit).all()

def create_recruitment(db: Session, recruitment: RecruitmentCreate):
    db_recruitment = Recruitment(
        candidate_name=recruitment.candidate_name,
        position=recruitment.position,
        status=recruitment.status
    )
    db.add(db_recruitment)
    db.commit()
    db.refresh(db_recruitment)
    return db_recruitment

def update_recruitment(db: Session, db_recruitment: Recruitment, recruitment_update: RecruitmentUpdate):
    if recruitment_update.candidate_name is not None:
        db_recruitment.candidate_name = recruitment_update.candidate_name
    if recruitment_update.position is not None:
        db_recruitment.position = recruitment_update.position
    if recruitment_update.status is not None:
        db_recruitment.status = recruitment_update.status
    db.commit()
    db.refresh(db_recruitment)
    return db_recruitment

def delete_recruitment(db: Session, db_recruitment: Recruitment):
    db.delete(db_recruitment)
    db.commit()
