# app/routers/claims_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.claims_schema import Claim, ClaimCreate, ClaimUpdate
from app.services import claims_service
from app.database.mysql_connector import SessionLocal

router = APIRouter()

# Dependency to get DB session
def get_db():
    """
    Generate a database session for performing operations and ensure its closure.
    Parameters:
        - None
    Returns:
        - generator: A generator yielding a database session object.
    Example:
        - Using the generator: 
          with get_db() as db_session:
              # perform database operations using db_session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[Claim])
def read_claims(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of claims from the database with pagination.
    Parameters:
        - skip (int): Number of results to skip for pagination. Defaults to 0.
        - limit (int): Maximum number of results to return. Defaults to 100.
        - db (Session): Database session dependency.
    Returns:
        - List[Claim]: A list of claims retrieved from the database based on provided pagination parameters.
    Example:
        - read_claims(skip=10, limit=5) -> [<Claim1>, <Claim2>, <Claim3>, <Claim4>, <Claim5>]
    """
    claims = claims_service.list_claims_service(db, skip=skip, limit=limit)
    return claims

@router.get("/{claim_id}", response_model=Claim)
def read_claim(claim_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a claim by its ID from the database.
    Parameters:
        - claim_id (int): The unique identifier of the claim to retrieve.
        - db (Session): The database session to use for retrieving the claim. Defaults to a session provided by dependency injection (Depends(get_db)).
    Returns:
        - dict: A dictionary representing the claim if found.
    Example:
        - read_claim(123) -> {"id": 123, "status": "pending", "amount": 100.0, ...}
    """
    claim = claims_service.get_claim_service(db, claim_id)
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return claim

@router.post("/", response_model=Claim, status_code=status.HTTP_201_CREATED)
def create_claim(claim: ClaimCreate, db: Session = Depends(get_db)):
    """
    Creates a new claim in the database.
    Parameters:
        - claim (ClaimCreate): The claim information to be created.
        - db (Session, optional): The database session for interacting with the database, defaults to a dependency injection.
    Returns:
        - Claim: The newly created claim object.
    Example:
        create_claim(claim=ClaimCreate(type='medical', amount=500), db=session) -> Claim(id=1, type='medical', amount=500)
    """
    try:
        new_claim = claims_service.create_claim_service(db, claim)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return new_claim

@router.put("/{claim_id}", response_model=Claim)
def update_claim(claim_id: int, claim_update: ClaimUpdate, db: Session = Depends(get_db)):
    """
    Update an existing claim in the database with provided updates.
    Parameters:
        - claim_id (int): The ID of the claim to be updated.
        - claim_update (ClaimUpdate): An instance containing the fields to update in the claim.
        - db (Session, optional): The database session dependency for performing database operations.
    Returns:
        - Claim: The updated claim object after applying the specified changes.
    Example:
        - update_claim(123, ClaimUpdate(status='approved')) -> Claim(id=123, status='approved', ...)
    """
    try:
        updated_claim = claims_service.update_claim_service(db, claim_id, claim_update)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return updated_claim

@router.delete("/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_claim(claim_id: int, db: Session = Depends(get_db)):
    """
    Delete a claim from the database using the given claim ID.
    Parameters:
        - claim_id (int): The unique identifier for the claim to be deleted.
        - db (Session): The database session dependency for interacting with the database, defaults to a session acquired from 'get_db'.
    Returns:
        - None: This function does not return any value upon successful deletion.
    Example:
        - delete_claim(123, db) -> None
    """
    try:
        claims_service.delete_claim_service(db, claim_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
