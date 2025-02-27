from pydiator_core import Mediator  # Replacing MediatR with pydiator
from typing import Optional
from TnA.Application.AppLogics.ZingUser.Queries import ValidateUserQuery
from Common.Logger import IZingLogging  # Assuming this is adapted to Python
from Common.Models import ResponseModel
from Common.ZingHttp import IZingHttpService
from Models.PunchInOutRequest import PunchInOutRequest
from TnA.Application.AppLogics.PunchIN.Commands import PunchInOutWhileLoginCommand

class PunchInWithLoginCommand(PunchInOutRequest):
    def __init__(self, subscription: str, employee_code: str, password: str, sync_val: str, **kwargs):
        super().__init__(**kwargs)  # Initialize base class PunchInOutRequest
        self.subscription = subscription
        self.employee_code = employee_code
        self.password = password
        self.sync_val = sync_val

    async def handle(self, mediator: Mediator, zing_http_service: IZingHttpService, zing_logging: IZingLogging[PunchInWithLoginCommand]) -> ResponseModel:
        # Dependency injection via method parameters (simulating constructor DI)
        self._mediator = mediator
        self._zing_http_service = zing_http_service
        self._zing_logging = zing_logging

        # Logic from C# Handle method
        request_source = "mobile" if self.is_request_from_mobile else "web"

        # Check valid user
        valid_user_response = await self._mediator.send(ValidateUserQuery(
            application_version=self.application_version,
            device_id=self.device_id,
            employee_code=self.employee_code,
            location=self.location,
            password=self.password,
            source=request_source,
            subscription=self.subscription,
            sync_val=self.sync_val
        ))

        if valid_user_response.code == 0:
            return valid_user_response

        # Check valid location (implied in original, proceeding to next command)
        response = await self._mediator.send(PunchInOutWhileLoginCommand(
            application_version=self.application_version,
            device_id=self.device_id,
            employee_code=self.employee_code,
            formatted_address=self.formatted_address,
            is_login=True,
            is_request_from_mobile=self.is_request_from_mobile,
            latitude=self.latitude,
            location=self.location,
            longitude=self.longitude,
            subscription_name=self.subscription,
            selfie_path=self.selfie_path,
            type=self.type,
            late_coming_reason=self.late_coming_reason
        ))

        return response

