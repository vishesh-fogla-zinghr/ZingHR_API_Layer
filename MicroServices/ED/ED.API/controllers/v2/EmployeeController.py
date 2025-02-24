from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from app.services.mediator_service import MediatorService
from app.models.response_model import ResponseModel

router = APIRouter(prefix="/api/v2/employee", tags=["Employee"])

# Request Models
class EmployeeSearchQuery(BaseModel):
    include_logged_in_empcode: bool = True
    page_size: int = 50
    page_index: int = 1
    search_term: Optional[str] = ""

class EmployeeDirectoryQuery(BaseModel):
    trans_type: str
    page_size: int = 50
    page_index: int = 1
    search_term: Optional[str] = ""
    
class EmployeeAttributeDetailQuery(BaseModel):
    attribute_id: Optional[int] = 0

# Endpoints
@router.get("/search", response_model=ResponseModel)
async def employee_search(
    include_logged_in_empcode: bool = Query(True),
    page_size: int = Query(50),
    page_index: int = Query(1),
    search_term: Optional[str] = Query(""),
    mediator: MediatorService = Depends()
):
    """Search for employees based on criteria."""
    query = EmployeeSearchQuery(
        include_logged_in_empcode=include_logged_in_empcode,
        page_size=page_size,
        page_index=page_index,
        search_term=search_term
    )
    response = await mediator.send(query)
    return response

@router.get("/directory", response_model=ResponseModel)
async def get_employee_directory(
    trans_type: str,
    page_size: int = Query(50),
    page_index: int = Query(1),
    search_term: Optional[str] = Query(""),
    mediator: MediatorService = Depends()
):
    """Retrieve employee directory based on transaction type."""
    query = EmployeeDirectoryQuery(
        trans_type=trans_type,
        page_size=page_size,
        page_index=page_index,
        search_term=search_term
    )
    response = await mediator.send(query)
    return response

@router.get("/attribute-detail", response_model=ResponseModel)
async def employee_attribute_detail(
    attribute_id: Optional[int] = Query(0),
    mediator: MediatorService = Depends()
):
    """Retrieve employee attribute details."""
    query = EmployeeAttributeDetailQuery(attribute_id=attribute_id)
    response = await mediator.send(query)
    return response