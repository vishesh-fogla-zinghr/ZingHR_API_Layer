from pydantic import BaseModel
from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.identity_service import IdentityService
from app.services.dal_service import DALService

# Define Request Model
class EmployeeAttributeDetailQuery(BaseModel):
    attribute_id: Optional[int] = 0

# Define Response Modelx
class ResponseModel(BaseModel):
    code: int
    data: List[dict]

# Initialize Router
router = APIRouter()

@router.get("/employee/attribute-detail", response_model=ResponseModel)
async def get_employee_attribute_detail(
    request: EmployeeAttributeDetailQuery,
    db: Session = Depends(get_db),
    identity_service: IdentityService = Depends(),
    dal_service: DALService = Depends(),
):
    # Get Employee Identity
    identity = identity_service.get_identity()
    
    # Set Query Parameters
    parameters = {
        "attributeId": request.attribute_id,
        "employeecode": identity["employee_code"]
    }

    # Execute Stored Procedure
    response = dal_service.execute_stored_procedure("ED.EmployeeAttributeList", parameters, db)

    return ResponseModel(code=1, data=response)
