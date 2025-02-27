from typing import Optional
from pydantic import BaseModel
from fastapi import Depends
from Models.PunchInOutRequest import PunchInOutRequest
from pydiator_core.mediatr import pydiator
from Common.Models import ResponseModel

# Command for validating a user (replacing first mediator.send)
class ValidateUserCommand(BaseModel):
    Subscription: str
    EmployeeCode: str
    DeviceId: str
    Source: str
    Location: str
    ApplicationVersion: str

# Command for punch-in action (replacing second mediator.send)
class PunchInCommand(BaseModel):
    ApplicationVersion: str
    DeviceId: str
    EmployeeCode: str
    FormattedAddress: Optional[str]
    IsLogin: bool
    IsRequestFromMobile: bool
    Latitude: Optional[float]
    Location: Optional[str]
    Longitude: Optional[float]
    SubscriptionName: str
    SelfiePath: Optional[str]
    LateComingReason: Optional[str]

# Identity service
class IdentityService:
    def get_identity(self):
        return {"EmployeeCode": "EMP123", "SubscriptionName": "SUB001"}

# Handler functions (minimal examples, typically in separate files)
async def handle_validate_user_command(request: ValidateUserCommand) -> ResponseModel:
    # Simulated validation logic
    return ResponseModel(code=1, message="User validated successfully")

async def handle_punch_in_command(request: PunchInCommand) -> ResponseModel:
    # Simulated punch-in logic
    return ResponseModel(code=1, message="Punch-in successful")

# Register handlers with pydiator (typically done at app startup)
pydiator.register_handler(ValidateUserCommand, handle_validate_user_command)
pydiator.register_handler(PunchInCommand, handle_punch_in_command)

# FastAPI handler
async def handle_punch_in_out(
    request: PunchInOutRequest,
    identity_service: IdentityService = Depends()
) -> ResponseModel:
    identity = identity_service.get_identity()
    employee_code = identity["EmployeeCode"]
    subscription = identity["SubscriptionName"]
    source = "Mobile" if request.is_request_from_mobile else "Web"

    # First command: Validate user
    validate_command = ValidateUserCommand(
        Subscription=subscription,
        EmployeeCode=employee_code,
        DeviceId=request.device_id if request.is_request_from_mobile else "Web",
        Source=source,
        Location="FACEDEVICE",
        ApplicationVersion=request.application_version
    )
    valid_user_response = await pydiator.send(validate_command)

    if valid_user_response.code == 0:
        return valid_user_response

    # Second command: Perform punch-in
    punch_in_command = PunchInCommand(
        ApplicationVersion=request.application_version,
        DeviceId=request.device_id,
        EmployeeCode=employee_code,
        FormattedAddress=request.formatted_address,
        IsLogin=True,
        IsRequestFromMobile=request.is_request_from_mobile,
        Latitude=request.latitude,
        Location=request.location,
        Longitude=request.longitude,
        SubscriptionName=subscription,
        SelfiePath=request.selfie_path,
        LateComingReason=request.late_coming_reason
    )
    response = await pydiator.send(punch_in_command)

    return response