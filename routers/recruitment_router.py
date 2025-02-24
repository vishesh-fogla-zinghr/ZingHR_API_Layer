# app/routers/recruitment_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.recruitment_schema import Recruitment, RecruitmentCreate, RecruitmentUpdate
from app.services import recruitment_service
from app.database.cockroach_connector import CockroachSessionLocal

router = APIRouter()

# Dependency to get DB session for CockroachDB
def get_db():
    db = CockroachSessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[Recruitment])
def read_recruitments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return recruitment_service.list_recruitments_service(db, skip, limit)

@router.get("/{recruitment_id}", response_model=Recruitment)
def read_recruitment(recruitment_id: int, db: Session = Depends(get_db)):
    recruitment = recruitment_service.get_recruitment_service(db, recruitment_id)
    if not recruitment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruitment not found")
    return recruitment

@router.post("/", response_model=Recruitment, status_code=status.HTTP_201_CREATED)
def create_recruitment(recruitment: RecruitmentCreate, db: Session = Depends(get_db)):
    return recruitment_service.create_recruitment_service(db, recruitment)

@router.put("/{recruitment_id}", response_model=Recruitment)
def update_recruitment(recruitment_id: int, recruitment_update: RecruitmentUpdate, db: Session = Depends(get_db)):
    try:
        return recruitment_service.update_recruitment_service(db, recruitment_id, recruitment_update)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/{recruitment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recruitment(recruitment_id: int, db: Session = Depends(get_db)):
    try:
        recruitment_service.delete_recruitment_service(db, recruitment_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
