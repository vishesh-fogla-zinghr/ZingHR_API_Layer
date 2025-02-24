# app/services/claims_service.py
from sqlalchemy.orm import Session
from app.repositories import claims_repository
from app.schemas.claims_schema import ClaimCreate, ClaimUpdate

def get_claim_service(db: Session, claim_id: int):
    claim = claims_repository.get_claim(db, claim_id)
    return claim

def list_claims_service(db: Session, skip: int = 0, limit: int = 100):
    return claims_repository.get_claims(db, skip=skip, limit=limit)

def create_claim_service(db: Session, claim: ClaimCreate):
    existing_claim = claims_repository.get_claim_by_claim_number(db, claim.claim_number)
    if existing_claim:
        raise Exception("Claim with this number already exists")
    return claims_repository.create_claim(db, claim)

def update_claim_service(db: Session, claim_id: int, claim_update: ClaimUpdate):
    db_claim = claims_repository.get_claim(db, claim_id)
    if not db_claim:
        raise Exception("Claim not found")
    return claims_repository.update_claim(db, db_claim, claim_update)

def delete_claim_service(db: Session, claim_id: int):
    db_claim = claims_repository.get_claim(db, claim_id)
    if not db_claim:
        raise Exception("Claim not found")
    claims_repository.delete_claim(db, db_claim)
