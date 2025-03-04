from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.LoginCommand import LoginCommand  # Import command classes
from Containers.container.AppContainer import mediator
from MicroServices.ZingAuth.Application.Integration.Models.WorkFlowGroupDetails import ResponseModel

router = APIRouter()

class AuthController():
    """Authentication Controller using FastAPI & Mediatr"""
    
    def __init__(self, mediator_instance):
        """Initialize the controller with the mediator instance."""
        self.mediator = mediator_instance

    async def login(self, command: LoginCommand):
        """
        Handles user login
        
        This endpoint authenticates a user based on their credentials and subscription.
        
        Returns:
            ResponseModel: Contains authentication token and user information if successful
        """
        try:
            response = await self.mediator.send(command)
            return response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {str(e)}"
            )

# Create an instance of the controller
auth_controller = AuthController(mediator)
# Add route using the controller method
router.add_api_route(
    "/login", 
    auth_controller.login, 
    methods=["POST"],
    response_model=ResponseModel,
    summary="User Login",
    description="Authenticate a user and get an auth token"
)