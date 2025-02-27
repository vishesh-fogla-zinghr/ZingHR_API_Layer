from pydantic import field_validator
from Commands import PunchInOutCommand
import ZingHR_API_Layer.MicroServices.PUNCHIN.AppLogics.CommonValidator as CommonValidator


class PunchInOutCommandValidator(PunchInOutCommand):
    @field_validator("Latitude")
    @classmethod
    def validate_latitude(cls, value):
        if not CommonValidator.check_lat_long(value):
            raise ValueError("Please check Latitude.")
        return value

    @field_validator("Longitude")
    @classmethod
    def validate_longitude(cls, value):
        if not CommonValidator.check_lat_long(value):
            raise ValueError("Please check Longitude.")
        return value
