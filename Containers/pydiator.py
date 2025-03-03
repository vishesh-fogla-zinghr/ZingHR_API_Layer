from pydiator_core.mediatr import pydiator
from pydiator_core.mediatr_container import MediatrContainer
from pydiator_core.pipelines.log_pipeline import LogPipeline
from zinghr_backend.app.MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.LoginCommand import (
    LoginCommand
)
from zinghr_backend.app.MicroServices.ZingAuth.Application.AppLogics.AuthToken.Handlers.LoginHandler import (
    LoginHandler
)
# Global variable to hold the singleton instance
_pydiator_instance = None

def setup_pydiator():
    global _pydiator_instance

    if _pydiator_instance is None:  # Ensure only one instance exists
        container = MediatrContainer()
        
        print("Before registration, requests:", container.get_requests())

        try:
            container.register_request(LoginCommand, LoginHandler)
            print("Successfully registered LoginCommand -> LoginHandler")
        except Exception as e:
            print(f"Failed to register request: {e}")
            
        container.register_pipeline(LogPipeline())
        
        print("After registration, requests:", container.get_requests())

        pydiator.ready(container=container)
        _pydiator_instance = pydiator
        
        print(f"Registering LoginCommand: {LoginCommand}, ID: {id(LoginCommand)}")
        print(f"Registering LoginHandler: {LoginHandler}, ID: {id(LoginHandler)}")

        print("Registered requests:", container.get_requests())  # Should now show LoginCommand
    

    return _pydiator_instance  # Return the same instance every time