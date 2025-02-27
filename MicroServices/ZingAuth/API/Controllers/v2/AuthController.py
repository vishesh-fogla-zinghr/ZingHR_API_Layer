from fastapi import APIRouter, Depends
from dependency_injector.wiring import Provide, inject
from typing import Any
from .BaseController import BaseController # Assuming ResponseModel exists
from zinghr_backend.app.MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.LoginCommand import LoginCommand  # Import command classes

router = APIRouter()

class AuthController(BaseController):
    """Authentication Controller using FastAPI & mediatr"""

    @router.post("/login", response_model=None)
    async def login(self, command: LoginCommand):
        """Handles user login"""
        response = await self.mediator.send(command)
        return response 