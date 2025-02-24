from sqlalchemy.orm import Session
from app.models.claims_model import Claim
from app.schemas.claims_schema import ClaimCreate, ClaimUpdate

def get_claim(db: Session, claim_id: int) -> Claim | None:
    """Fetch a claim by its ID."""
    return db.query(Claim).filter_by(id=claim_id).first()

def get_claim_by_claim_number(db: Session, claim_number: str) -> Claim | None:
    """Fetch a claim by its claim number."""
    return db.query(Claim).filter_by(claim_number=claim_number).first()

def get_claims(db: Session, skip: int = 0, limit: int = 100) -> list[Claim]:
    """Fetch multiple claims with optional pagination."""
    return db.query(Claim).offset(skip).limit(limit).all()

def create_claim(db: Session, claim: ClaimCreate) -> Claim:
    """Create a new claim."""
    db_claim = Claim(**claim.dict())  # Unpacking dictionary for cleaner code
    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)
    return db_claim

def update_claim(db: Session, db_claim: Claim, claim_update: ClaimUpdate) -> Claim:
    """Update an existing claim."""
    for key, value in claim_update.dict(exclude_unset=True).items():
        setattr(db_claim, key, value)  # Dynamically update fields
    db.commit()
    db.refresh(db_claim)
    return db_claim

def delete_claim(db: Session, db_claim: Claim) -> None:
    """Delete a claim."""
    db.delete(db_claim)
    db.commit()
