from typing import Any
from pydantic import BaseModel, Field, constr
from fastapi import APIRouter, Depends, HTTPException, status, Security, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.SendOTPCommand import SendOTPCommand
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.LoginCommand import LoginCommand  # Import command classes
from Containers.container.AppContainer import mediator
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.VerifyOTPCommand import VerifyOTPCommand
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
                "verify_exp": False,
                "verify_nbf": False,
                "verify_iss": False,
                "verify_aud": False,
                "require_exp": False,
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

    async def login(self, command: LoginCommand, response: Response):
        """
        Handles user login
        
        This endpoint authenticates a user based on their credentials and subscription.
        
        Returns:
            ResponseModel: Contains authentication token and user information if successful
        """
        try:
            result = await self.mediator.send(command)
            
            if result.code == 1 and result.data and "response" in result.data:
                # Get the response object from the result
                login_response = result.data.pop("response")
                
                # Copy cookies from login response to the actual response
                for cookie in login_response.raw_headers:
                    if cookie[0].decode().lower() == 'set-cookie':
                        response.raw_headers.append(cookie)
            
            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {str(e)}"
            )
            
    async def send_otp(self, command: SendOTPCommand):
        """
        Send OTP to phone number
        
        This endpoint sends a 6-digit OTP to the provided phone number.
        Does not require authorization as it's part of the login process.
        
        Returns:
            SendOTPResponse: Contains reference ID and expiry time
        """
        try:
            # Create and send command
            result = await self.mediator.send(command)
            
            if result.code != 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.message
                )
                
            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send OTP: {str(e)}"
            )

    async def verify_otp(self, command: VerifyOTPCommand, response: Response):
        """
        Verify OTP and login user
        
        This endpoint verifies the OTP and if valid, logs in the user.
        Does not require authorization as it's part of the login process.
        
        Returns:
            ResponseModel: Contains authentication token and user information if successful
        """
        
        try:
            
            result = await self.mediator.send(command)
            
            if result.code != 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.message
                )
            
            # If result contains response object with cookies, copy them
            if result.data and "response" in result.data:
                # Get the response object from the result
                login_response = result.data.pop("response")
                
                # Copy cookies from login response to the actual response
                for cookie in login_response.raw_headers:
                    if cookie[0].decode().lower() == 'set-cookie':
                        response.raw_headers.append(cookie)
            
            return result
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to verify OTP: {str(e)}"
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

router.add_api_route(
    "/send-otp",
    auth_controller.send_otp,
    methods=["POST"],
    response_model=ResponseModel,
    summary="Send OTP",
    description="Send a 6-digit OTP to the provided phone number"
)

router.add_api_route(
    "/verify-otp",
    auth_controller.verify_otp,
    methods=["POST"],
    response_model=ResponseModel,
    summary="Verify OTP",
    description="Verify OTP and get auth token"
)

# All other routes in this router will require authorization by default
# router = APIRouter(dependencies=[Depends(validate_token)])