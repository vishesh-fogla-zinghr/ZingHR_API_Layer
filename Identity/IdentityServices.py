import os
import jwt
import datetime
import logging
from typing import List, Optional
from fastapi import Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)



class JwtSettings(BaseModel):
    secret: str


class IdentityModel(BaseModel):
    EmployeeCode: Optional[str] = ""
    Name: Optional[str] = ""
    SubscriptionId: int = 0
    SubscriptionName: Optional[str] = ""
    IsAdmin: bool = False
    IsManager: bool = False
    Photo: Optional[str] = ""
    EmployeeId: int = 0
    Email: Optional[str] = ""

class OBIdentityModel(BaseModel):
    SubscriptionName: str = ""
    UserID: str = ""
    RoleDescription: str = ""

class ApplicantPortalIdentityModel(BaseModel):
    SubscriptionName: str = ""
    UserId: str = ""
    RoleDescription: str = ""

# IdentityService implementation
class IdentityService:
    def __init__(self, request: Request, configuration: dict, jwt_settings: JwtSettings):
        """
        request: FastAPI Request (to access headers)
        configuration: a dictionary of configuration values (if needed)
        jwt_settings: an instance of JwtSettings containing secret and other JWT config.
        """
        self.request = request
        self.configuration = configuration
        self.jwt_settings = jwt_settings

    def token_descriptor(self, jwt_token: str) -> IdentityModel:
        try:
            
            decoded = jwt.decode(jwt_token, self.jwt_settings.secret, algorithms=["HS256"], options={"verify_aud": False})
        except Exception as e:
            logger.error(f"Error decoding token: {e}")
            return IdentityModel()
        
        subscription_id = decoded.get("signupId")
        subscription_name = decoded.get("SubscriptionName", "").lower()
        employee_code = decoded.get("EmployeeCode", "")
        
        role_claim = decoded.get("role")
        
        if role_claim is None:
            roles = []
        elif isinstance(role_claim, list):
            roles = role_claim
        else:
            roles = [role_claim]
        is_admin = any(r.lower().strip() == "admin" for r in roles)
        is_manager = any(r.lower().strip() == "manager" for r in roles)
        employee_id = decoded.get("EmployeeId", 0)
        
        return IdentityModel(
            EmployeeCode=employee_code,
            Name="",
            SubscriptionId=int(subscription_id) if subscription_id is not None else 0,
            SubscriptionName=subscription_name,
            IsAdmin=is_admin,
            IsManager=is_manager,
            Photo="",
            EmployeeId=int(employee_id) if employee_id else 0,
            Email=""
        )

    def OB_token_descriptor(self, jwt_token: str) -> OBIdentityModel:
        try:
            decoded = jwt.decode(jwt_token, self.jwt_settings.secret, algorithms=["HS256"], options={"verify_aud": False})
        except Exception as e:
            logger.error(f"Error decoding token: {e}")
            return OBIdentityModel()
        subscription_name = decoded.get("SubscriptionName", "")
        user_id = decoded.get("UserId", "")
        role_description = decoded.get("RoleDescription", "")
        return OBIdentityModel(
            SubscriptionName=subscription_name,
            UserID=user_id,
            RoleDescription=role_description
        )

    def get_identity(self, jwt_token: Optional[str] = None) -> IdentityModel:
        if jwt_token:
            return self.token_descriptor(jwt_token)
        authorization = self.request.headers.get("Authorization")
        if authorization:
            parts = authorization.split(" ")
            if len(parts) >= 2:
                token = parts[1]
                return self.token_descriptor(token)
        return IdentityModel()

    def get_token(self) -> str:
        authorization = self.request.headers.get("Authorization")
        if authorization:
            parts = authorization.split(" ")
            if len(parts) >= 2:
                return parts[1]
        return ""

    def get_OB_identity(self) -> OBIdentityModel:
        authorization = self.request.headers.get("Authorization")
        if authorization:
            parts = authorization.split(" ")
            if len(parts) >= 2:
                token = parts[1]
                return self.OB_token_descriptor(token)
        return OBIdentityModel()

    def generate_token(self, employeeCode: str, Name: str, signupId: int, subscriptionName: str, employeePhoto: str,
                       roleDescription: str, firstName: str, lastName: str, email: str, employeeId: int = 0, 
                       tokenExpirationTime: float = 0) -> str:
        if roleDescription:
            roleDescription = roleDescription.lower().strip()
        
        expirationTime = float(os.getenv("TokenLifetime", 900))
        if tokenExpirationTime != 0:
            expirationTime = tokenExpirationTime
        now = datetime.datetime.utcnow()
        exp = now + datetime.timedelta(seconds=expirationTime)
        payload = {
            "signupId": str(signupId),
            "SubscriptionName": subscriptionName,
            "EmployeeCode": employeeCode or "",
            "FirstName": "",
            "LastName": "",
            "Email": "",
            "Name": "",
            "Photo": "",
            "EmployeeId": str(employeeId),
            "iat": now,
            "exp": exp
        }
        if roleDescription:
            roles = [r.strip().lower() for r in roleDescription.split("|") if r.strip()]
            payload["role"] = roles
        token = jwt.encode(payload, self.jwt_settings.secret, algorithm="HS256")
        
        return token

    def generate_token_simple(self, subscriptionName: str, userId: str, roleDescription: str) -> str:
        expirationTime = float(os.getenv("TokenLifetime", 900))
        now = datetime.datetime.utcnow()
        exp = now + datetime.timedelta(seconds=expirationTime)
        payload = {
            "SubscriptionName": subscriptionName,
            "UserId": userId or "",
            "RoleDescription": roleDescription or "",
            "iat": now,
            "exp": exp
        }
        token = jwt.encode(payload, self.jwt_settings.secret, algorithm="HS256")
        return token

    def is_user_in_role(self, roleCode: str, token: Optional[str] = None) -> bool:
        if token is None:
            token = self.get_token()
        try:
            decoded = jwt.decode(token, self.jwt_settings.secret, algorithms=["HS256"], options={"verify_aud": False})
        except Exception as e:
            logger.error(f"Error decoding token: {e}")
            return False
        roles = decoded.get("role", [])
        if isinstance(roles, str):
            roles = [roles]
        return any(r.lower().strip() == roleCode.lower().strip() for r in roles)

    def get_roles(self) -> List[str]:
        token = self.get_token()
        try:
            decoded = jwt.decode(token, self.jwt_settings.secret, algorithms=["HS256"], options={"verify_aud": False})
        except Exception as e:
            logger.error(f"Error decoding token: {e}")
            return []
        roles = decoded.get("role", [])
        if isinstance(roles, str):
            roles = [roles]
        return roles

    # Methods for ApplicantPortal
    def get_applicant_portal_identity(self) -> ApplicantPortalIdentityModel:
        authorization = self.request.headers.get("Authorization")
        if authorization:
            parts = authorization.split(" ")
            if len(parts) >= 2:
                token = parts[1]
                return self.applicant_portal_token_descriptor(token)
        return ApplicantPortalIdentityModel(
            SubscriptionName="",
            UserId="",
            RoleDescription=""
        )

    def applicant_portal_token_descriptor(self, jwt_token: str) -> ApplicantPortalIdentityModel:
        try:
            decoded = jwt.decode(jwt_token, self.jwt_settings.secret, algorithms=["HS256"], options={"verify_aud": False})
        except Exception as e:
            logger.error(f"Error decoding applicant portal token: {e}")
            return ApplicantPortalIdentityModel()
        subscriptionName = decoded.get("SubscriptionName", "")
        userId = decoded.get("UserId", "")
        roleDescription = decoded.get("RoleDescription", "")
        return ApplicantPortalIdentityModel(
            SubscriptionName=subscriptionName,
            UserId=userId,
            RoleDescription=roleDescription
        )

    def generate_applicant_portal_token(self, identityModel: ApplicantPortalIdentityModel) -> str:
        expirationTime = float(os.getenv("TokenLifetime", 900))
        now = datetime.datetime.utcnow()
        exp = now + datetime.timedelta(seconds=expirationTime)
        payload = {
            "UserId": str(identityModel.UserId) if identityModel.UserId else "",
            "RoleDescription": identityModel.RoleDescription or "",
            "SubscriptionName": identityModel.SubscriptionName or "",
            "iat": now,
            "exp": exp
        }
        token = jwt.encode(payload, self.jwt_settings.secret, algorithm="HS256")
        return token
