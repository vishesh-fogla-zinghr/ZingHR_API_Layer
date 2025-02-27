from abc import ABC, abstractmethod
from typing import List, Optional
from .IdentityModel import IdentityModel, OBIdentityModel, ApplicantPortalIdentityModel
from jose import jwt  # For token handling (optional, if using JWT)
from dataclasses import dataclass


class IIdentityService(ABC):

    @abstractmethod
    def get_identity(self, jwt_token: Optional[str] = None) -> IdentityModel:
        """Retrieve the identity of the current user, optionally using a JWT token."""
        pass

    @abstractmethod
    def get_ob_identity(self) -> OBIdentityModel:
        """Retrieve the OB (Onboarding) identity of the current user."""
        pass

    @abstractmethod
    def generate_token(
        self,
        employee_code: str,
        name: str,
        signup_id: int,
        subscription_name: str,
        employee_photo: str,
        role_description: str,
        first_name: str,
        last_name: str,
        email: str,
        employee_id: int = 0,
        token_expiration_time: float = 0
    ) -> str:
        """Generate an authentication token for a user."""
        pass

    @abstractmethod
    def generate_simple_token(self, subscription_name: str, user_id: str, role_description: str) -> str:
        """Generate a simplified authentication token."""
        pass

    @abstractmethod
    def get_token(self) -> str:
        """Retrieve the current authentication token."""
        pass

    @abstractmethod
    def is_user_in_role(self, role_code: str, token: Optional[str] = None) -> bool:
        """Check if the user has a specific role, optionally using a token."""
        pass

    @abstractmethod
    def get_roles(self) -> List[str]:
        """Retrieve a list of roles assigned to the user."""
        pass

    @abstractmethod
    def get_applicant_portal_identity(self) -> ApplicantPortalIdentityModel:
        """Retrieve identity information for the applicant portal."""
        pass

    @abstractmethod
    def generate_applicant_portal_token(self, identity_model: ApplicantPortalIdentityModel) -> str:
        """Generate a token for the applicant portal."""
        pass
