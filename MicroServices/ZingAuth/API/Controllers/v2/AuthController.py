from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.LoginCommand import LoginCommand  # Import command classes
from Containers.container.AppContainer import mediator
from MicroServices.ZingAuth.Application.Integration.Models.WorkFlowGroupDetails import ResponseModel
import jwt
import os
from datetime import datetime

router = APIRouter()
security = HTTPBearer()


async def validate_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Validate JWT token - equivalent to ASP.NET Core's JWT validation"""
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET"),
            algorithms=["HS256"],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iss": True,
                "verify_aud": True,
                "require_exp": True,
            }
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"Token-Expired": "true"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

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

# All other routes in this router will require authorization by default
# router = APIRouter(dependencies=[Depends(validate_token)])