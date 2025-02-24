# app/services/recruitment_service.py
from sqlalchemy.orm import Session
from app.repositories import recruitment_repository
from app.schemas.recruitment_schema import RecruitmentCreate, RecruitmentUpdate

def get_recruitment_service(db: Session, recruitment_id: int):
    return recruitment_repository.get_recruitment(db, recruitment_id)

def list_recruitments_service(db: Session, skip: int = 0, limit: int = 100):
    return recruitment_repository.get_recruitments(db, skip, limit)

def create_recruitment_service(db: Session, recruitment: RecruitmentCreate):
    return recruitment_repository.create_recruitment(db, recruitment)

def update_recruitment_service(db: Session, recruitment_id: int, recruitment_update: RecruitmentUpdate):
    db_recruitment = recruitment_repository.get_recruitment(db, recruitment_id)
    if not db_recruitment:
        raise Exception("Recruitment not found")
    return recruitment_repository.update_recruitment(db, db_recruitment, recruitment_update)

def delete_recruitment_service(db: Session, recruitment_id: int):
    db_recruitment = recruitment_repository.get_recruitment(db, recruitment_id)
    if not db_recruitment:
        raise Exception("Recruitment not found")
    recruitment_repository.delete_recruitment(db, db_recruitment)
