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
    PersonalDetails,
    PersonalContactDetails,
    BloodGroupMaster,
    GeneralConfiguration
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
        self.integration_key = os.getenv("JWT_INTEGRATION_KEY", "your-integration-key")
        self.token_lifetime = int(os.getenv("TOKEN_LIFETIME", "900"))
        self.issuer = "Integration"
        self.audience = "EndClient"

class RefreshTokenHandler():
    """Handler for processing refresh token command"""
    
    def __init__(self, _connection: DAL):
        self.db_connection = _connection
        self.jwt_settings = JwtSettings()
        self.logger = logging.getLogger(__name__)
        
        # self.dal = _connection
        # self.jwt_secret = os.getenv("JWT_SECRET", "your-256-bit-secret")  # Should be at least 32 bytes long
        # self.token_lifetime = int(os.getenv("TOKEN_LIFETIME", "900"))  # Default 15 minutes
        # self.logger = logging.getLogger(__name__)
        
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
                    "iss": "zinghr_auth",
                    "aud": "zinghr_api",
                    "exp": int(datetime.utcnow().timestamp() + 86400),  # 24 hours from now
                    "nbf": int(datetime.utcnow().timestamp()),
                    "iat": int(datetime.utcnow().timestamp())
                }

                # Sign the JWT token
                jwt_token = jwt.encode(
                    claims,
                    os.getenv("JWT_SECRET"),
                    algorithm="HS256"
                )
                
                print("Token generated --------------------------------")

                return ResponseModel(
                    code=1,
                    message="Token refreshed successfully",
                    data=RefreshToken(token=jwt_token)
                )

            finally:
                session.close()
                engine.dispose()
            
            # try:
                
            #     session.execute(text("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED"))

            #         # Query auth token with employee details
            #     auth_token = (
            #         session.query(AuthToken)
            #         .join(EmployeeMaster, EmployeeMaster.employeecode == AuthToken.employee_code)
            #         .options(
            #             joinedload(AuthToken.employee_master)
            #         )
            #         .filter(
            #             AuthToken.token == request.auth_token,
            #             AuthToken.subscription_name == request.subscription_name,
            #             AuthToken.is_active == True
            #         )
            #         .first()
            #     )
                
            #     if not auth_token:
            #         self.logger.warning(f"Token not found or inactive: {request.auth_token}")
            #         return ResponseModel(code=0, message="Invalid or expired token")

            #     if auth_token.expires_at < datetime.utcnow():
            #         auth_token.is_active = False
            #         session.commit()
            #         self.logger.warning(f"Token expired: {request.auth_token}")
            #         return ResponseModel(code=0, message="Token expired")
                
            #     employee = auth_token.employee_master
            
            #     # Generate JWT token with claims from employee info
            #     jwt_token = self.generate_token(employee, auth_token)
                
            #     return ResponseModel(
            #         code=1,
            #         message="Success",
            #         data=RefreshToken(token=jwt_token)
            #     )
            
            # finally:
            #     session.close()
            #     engine.dispose()
                
        except Exception as e:
            self.logger.error(f"Refresh token error: {str(e)}")
            session.rollback()
            return ResponseModel(
                code=-1,
                message=f"An error occurred during token refresh: {str(e)}"
            )

    def generate_token(self, employee: EmployeeMaster) -> str:
        try:
            expiration = datetime.utcnow() + timedelta(seconds=self.jwt_settings.token_lifetime)
            
            payload = {
                "exp": expiration,
                "iss": self.jwt_settings.issuer,
                "aud": self.jwt_settings.audience,
                "nbf": datetime.utcnow(),
                # Basic info
                "emp_code": employee.employeecode,
                "emp_name": f"{employee.first_name} {employee.last_name}",
                # Employee details
                "employee_id": employee.employeeid,
                "photo": employee.employee_photo,
                # Additional info
                "salutation": employee.salutation,
                "party_id": employee.party_id,
                "ranking": employee.ranking,
                "created_date": employee.created_date.isoformat() if employee.created_date else None,
                "updated_date": employee.updated_date.isoformat() if employee.updated_date else None,
                "source": employee.source,
                "app_version": employee.app_version,
                "device_id": employee.device_id
            }

            # Generate token using PyJWT with similar settings to C#
            token = jwt.encode(
                payload,
                self.jwt_settings.secret,
                algorithm="HS256"
            )

            return token

        except Exception as e:
            self.logger.error(f"Token generation error: {str(e)}")
            raise 