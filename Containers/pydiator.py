from pydiator_core.mediatr import pydiator
from pydiator_core.mediatr_container import MediatrContainer
from pydiator_core.pipelines.log_pipeline import LogPipeline
from zinghr_backend.app.MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands import (
    LoginCommand
)
from zinghr_backend.app.MicroServices.ZingAuth.Application.AppLogics.AuthToken.Handlers import (
    LoginHandler
)

def setup_pydiator():
    container = MediatrContainer()
    container.register_request(LoginCommand, LoginHandler)
    container.register_pipeline(LogPipeline())
    pydiator.ready(container=container)
    return pydiator