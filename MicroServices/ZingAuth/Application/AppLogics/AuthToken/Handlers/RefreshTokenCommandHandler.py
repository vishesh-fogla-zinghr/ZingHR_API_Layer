from MicroServices.ZingAuth.Application.Integration.Models.WorkFlowGroupDetails import ResponseModel
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.RefreshTokenCommand import (
    RefreshTokenCommand, 
    RefreshToken, 
)
from ORM.models import (
    LoginHistory,
    EmployeeMaster,
    EmployeeRoleMapping,
    RoleMaster,
    ReqRecEmployeeDetails,
    ReqRecEmployeeFinDetails,
    GeneralConfiguration,
    EmployeeAttributeDetails,
    AttributeTypeUnitMaster,
    AttributeTypeMaster
)
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from DAL.dal import DAL
from sqlalchemy import and_, or_, func
from sqlalchemy import text
from datetime import datetime, timedelta
import jwt
import os
import logging
from typing import Optional, Any, Dict

class JwtSettings:
    """Settings for JWT token generation and validation"""
    def __init__(self):
        self.secret = os.getenv("JWT_SECRET", "oS36PX-H4FqySdWlWkFRZ94DvurZTOHh3o4o76pIgNg")
        self.token_lifetime = int(os.getenv("TOKEN_LIFETIME", "900"))
        self.issuer = "zinghr_auth"
        self.audience = "zinghr_api"

class RefreshTokenHandler():
    """Handler for processing refresh token command"""
    
    def __init__(self, _connection: DAL):
        self.db_connection = _connection
        self.jwt_settings = JwtSettings()
        self.logger = logging.getLogger(__name__)
        
    def safe_str(self, value: Any) -> str:
        """Safely convert any value to string"""
        if value is None:
            return ""
        try:
            if isinstance(value, (int, float)):
                return str(value)
            if isinstance(value, datetime):
                return value.isoformat()
            return str(value)
        except Exception as e:
            self.logger.error(f"Error converting value to string: {e}")
            return ""
        
        
    async def handle(self, request: RefreshTokenCommand) -> ResponseModel:
        try: 
            engine = await self.db_connection.get_connection(request.subscription_name)
            session = Session(bind=engine)
            
            try:              
                
                login_history = (
                    session.query(LoginHistory)
                    .filter(
                        LoginHistory.token == request.auth_token,
                        LoginHistory.subscription == request.subscription_name,
                        LoginHistory.errordesc != "Log Out"
                    )
                    .order_by(LoginHistory.login.desc())
                    .first()
                )
                
                if not login_history:
                    return ResponseModel(code=0, message="Invalid or expired token")
                
                employee = (
                    session.query(EmployeeMaster)
                    .options(
                        joinedload(EmployeeMaster.roles).joinedload(EmployeeRoleMapping.role),
                        joinedload(EmployeeMaster.personal_details),
                        joinedload(EmployeeMaster.personal_contact),
                        joinedload(EmployeeMaster.req_rec_details)
                    )
                    .filter(EmployeeMaster.employeecode == login_history.userid)
                    .first()
                )

                if not employee:
                    return ResponseModel(code=0, message="Employee not found")

                # Get reporting manager details
                reporting_manager = None
                if employee.req_rec_details:
                    fin_details = (
                        session.query(ReqRecEmployeeFinDetails)
                        .filter(ReqRecEmployeeFinDetails.efd_ed_empid == employee.req_rec_details.ed_empid)
                        .first()
                    )
                    if fin_details and fin_details.efd_reporting_manager:
                        reporting_manager = (
                            session.query(ReqRecEmployeeDetails)
                            .filter(ReqRecEmployeeDetails.ed_empcode == fin_details.efd_reporting_manager)
                            .first()
                        )

                # Get role information
                roles = (
                    session.query(RoleMaster)
                    .join(EmployeeRoleMapping)
                    .filter(
                        EmployeeRoleMapping.employee_code == employee.employeecode,
                        EmployeeRoleMapping.applicable == True,
                        RoleMaster.applicable == True
                    )
                    .all()
                )
                
                employee_attributes = (
                    session.query(
                        AttributeTypeMaster.attribute_type_code,
                        AttributeTypeUnitMaster.attribute_type_unit_description
                    )
                    .join(EmployeeAttributeDetails, 
                          EmployeeAttributeDetails.attribute_type_id == AttributeTypeMaster.attribute_type_id)
                    .join(AttributeTypeUnitMaster, 
                          EmployeeAttributeDetails.attribute_type_unit_id == AttributeTypeUnitMaster.attribute_type_unit_id)
                    .filter(
                        EmployeeAttributeDetails.employee_code == employee.employeecode,
                        EmployeeAttributeDetails.to_date.is_(None),
                        AttributeTypeUnitMaster.applicable == True,
                        AttributeTypeMaster.applicable == True
                    )
                    .all()
                )

                # Convert attributes to dictionary
                attributes_dict = {
                    self.safe_str(attr.attribute_type_code): self.safe_str(attr.attribute_type_unit_description)
                    for attr in employee_attributes
                }
                

                # Generate claims for JWT token
                claims = {
                   "sub": self.safe_str(employee.employeecode),
                    "signup_id": self.safe_str(employee.signupid),
                    "subscription": self.safe_str(request.subscription_name),
                    "auth_token": self.safe_str(login_history.token),
                    "first_name": self.safe_str(employee.req_rec_details.ed_first_name if employee.req_rec_details else ""),
                    "middle_name": self.safe_str(employee.req_rec_details.ed_middle_name if employee.req_rec_details else ""),
                    "last_name": self.safe_str(employee.req_rec_details.ed_last_name if employee.req_rec_details else ""),
                    "salutation": self.safe_str(employee.req_rec_details.ed_salutation if employee.req_rec_details else ""),
                    "email": self.safe_str(employee.req_rec_details.ed_email if employee.req_rec_details else ""),
                    "employee_photo": self.safe_str(employee.req_rec_details.ed_employee_photo if employee.req_rec_details else ""),
                    "role_description": "|".join([r.role_description for r in roles]) if roles else "",
                    "role_code": "|".join([str(r.role_id) for r in roles]) if roles else "",
                    "employee_id": self.safe_str(employee.employeeid),
                    "session_id": self.safe_str(login_history.sessionid),
                    "ip_address": self.safe_str(login_history.ipaddress),
                    "latitude": self.safe_str(login_history.latitude),
                    "longitude": self.safe_str(login_history.longitude),
                    "source": self.safe_str(login_history.source),
                    "app_version": self.safe_str(login_history.appversion),
                    "device_id": self.safe_str(login_history.deviceid),
                    "mac_address": self.safe_str(login_history.macaddress),
                    # Additional employee details from ReqRecEmployeeDetails
                    "gender": self.safe_str(employee.req_rec_details.ed_sex if employee.req_rec_details else ""),
                    "mobile": self.safe_str(employee.req_rec_details.ed_mobile if employee.req_rec_details else ""),
                    "landline": self.safe_str(employee.req_rec_details.ed_working_telephone if employee.req_rec_details else ""),
                    "address": self.safe_str(employee.req_rec_details.ed_present_address if employee.req_rec_details else ""),
                    "dob": self.safe_str(employee.req_rec_details.ed_dob if employee.req_rec_details else ""),
                    "doj": self.safe_str(employee.req_rec_details.ed_doj if employee.req_rec_details else ""),
                    # Reporting manager details
                    "reporting_manager_code": self.safe_str(fin_details.efd_reporting_manager if fin_details else ""),
                    "reporting_manager_name": self.safe_str(f"{reporting_manager.ed_first_name} {reporting_manager.ed_last_name}" if reporting_manager else ""),
                    "reporting_manager_email": self.safe_str(reporting_manager.ed_email if reporting_manager else ""),
                    "reporting_manager_mobile": self.safe_str(reporting_manager.ed_mobile if reporting_manager else ""),
                    "reporting_manager_photo": self.safe_str(reporting_manager.ed_employee_photo if reporting_manager else ""),
                    # Standard JWT claims
                    "attributes": attributes_dict,                    
                }

                # Sign the JWT token
                jwt_token = jwt.encode(
                    claims,
                    os.getenv("JWT_SECRET"),
                    algorithm="HS256"
                )

                return ResponseModel(
                    code=1,
                    message="Token refreshed successfully",
                    data=RefreshToken(token=jwt_token)
                )

            finally:
                session.close()
                engine.dispose()
                
        except Exception as e:
            self.logger.error(f"Refresh token error: {str(e)}")
            session.rollback()
            return ResponseModel(
                code=-1,
                message=f"An error occurred during token refresh: {str(e)}"
            )
