from PunchInOutRequest import PunchInOutRequest


class PunchInOutRequestWithQuickPin(PunchInOutRequest):
    device_manufacturer_name: str
    device_os: str
    quick_pin: int
    token_request: str
    subscription_name: str
    type: str = ""
    selfie_path: str = ""
