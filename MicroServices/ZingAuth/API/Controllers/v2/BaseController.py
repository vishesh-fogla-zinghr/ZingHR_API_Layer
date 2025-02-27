from fastapi import APIRouter, Depends
from mediatr import Mediator
from zinghr_backend.app.Containers.pydiator import setup_pydiator
from dependency_injector.wiring import inject

pydiator = setup_pydiator()

class BaseController:
    """Base controller using FastAPI and mediatr"""

    @inject
    def __init__(self, mediator: Mediator = Depends(lambda: pydiator)):
        self._mediator = mediator

    @property
    def mediator(self) -> Mediator:
        return self._mediator