from fastapi import APIRouter, Depends
from typing import Optional
from app.dependencies import get_mediator
from app.queries import (
    GetGeneralEmployeeInfoQuery
)

router = APIRouter(prefix="/api/v2/employee")

@router.get("/general-info")
async def get_general_employee_info(mediator=Depends(get_mediator)):
    return await mediator.send(GetGeneralEmployeeInfoQuery())
