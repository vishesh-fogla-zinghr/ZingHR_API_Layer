from fastapi import APIRouter, Depends
from typing import Any
from zinghr_backend.app.MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.LoginCommand import LoginCommand  # Import command classes
from zinghr_backend.app.Containers.container.AppContainer import mediator

router = APIRouter()

class AuthController():
    """Authentication Controller using FastAPI & Mediatr"""
    
    def __init__(self, mediator_instance):
        """Initialize the controller with the mediator instance."""
        self.mediator = mediator_instance

    async def login(self, command: LoginCommand):
        """Handles user login"""
        response = await self.mediator.send(command)
        return response

# Create an instance of the controller
auth_controller = AuthController(mediator)
# Add route using the controller method
router.add_api_route("/login", auth_controller.login, methods=["POST"])