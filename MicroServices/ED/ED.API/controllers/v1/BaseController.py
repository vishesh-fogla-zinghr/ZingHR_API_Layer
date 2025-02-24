from fastapi import APIRouter, Depends
from app.services.mediator_service import MediatorService
from app.auth.auth_dependency import get_current_user  # Example authorization dependency

class BaseController:
    """Base controller providing MediatorService dependency."""

    def __init__(self, mediator: MediatorService = Depends()):
        self.mediator = mediator

# Example usage in a controller
router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_current_user)])  # Authorization dependency

@router.get("/example")
async def example_endpoint(mediator: MediatorService = Depends()):
    """Example endpoint using the mediator."""
    response = await mediator.send({"message": "Hello from BaseController"})
    return response
