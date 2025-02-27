from pydantic import BaseModel

class GeoConfiguration(BaseModel):
    multiple_login_enable_to_user: int = 0
    force_geo_location: int = 0
    message: str = ""
    check_device_id: int = 0
    is_punch_in: bool = False
    is_google_sso: bool = False
    is_proxy_login_enable: int = 0
    theme_configuration: bool = False
    app_configuration: bool = False
    ip_check_enabled_on_mobile: bool = False
    client_version: str = ""
    company_logo: str = ""
    digital_id: bool = False
    scan_digital_id: bool = False
    selfie_with_punch_in: bool = False
    face_punchin_out_allowed: bool = False
    trigger_survey: bool = False
    one_device_one_user: bool = False
    one_device_one_user_days: int = 0
    is_multi_shift: bool = False
    is_fingerprint_configuration: bool = False
    enable_cowin: bool = False
    advantage_club_enabled: bool = False
    tag_code: str = ""
    enable_reaction: bool = False
    is_dynamic_pointing: bool = False
    dynamic_pointing_m_services: str = ""
    dynamic_pointing_apis: str = ""
    dynamic_pointing_vd: str = ""
    dynamic_pointing_blob: str = ""
    dynamic_pointing_zing_next: str = ""
    enable_zing_id: bool = False
    max_device_limit: int = 0
    auto_approve_device: int = 0

    def __repr__(self):
        return f"GeoConfiguration(client_version='{self.client_version}')"
