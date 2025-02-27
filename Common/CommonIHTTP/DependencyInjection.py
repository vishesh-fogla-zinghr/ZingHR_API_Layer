from fastapi import Depends
from starlette.requests import Request
from dependency_injector import containers, providers

# Define a simple HTTP service equivalent to IProductHttpService
class ProductHttpService:
    def __init__(self, request: Request):
        self.request = request

# Dependency Injection Container
class Container(containers.DeclarativeContainer):
    http_context_accessor = providers.Singleton(Request)  # Equivalent to IHttpContextAccessor