from fastapi import Depends
from mediatr import Mediator
from Containers.copydiator import setup_pydiator
from dependency_injector.wiring import inject

def get_mediator() -> Mediator:
    """Dependency provider for Mediator"""
    return setup_pydiator()

class BaseController:
    """Base controller using FastAPI and Mediatr"""
    
    
    
    def __init__(self):
        self._mediator = get_mediator()

    @property
    def mediator(self) -> Mediator:
        return self._mediator

    def get_mediatr(self) -> Mediator: 
        return self._mediator