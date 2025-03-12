import uuid
from pydantic import BaseModel
from typing import Optional, Dict
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.LoginCommand import LoginCommand
from MicroServices.ZingAuth.Application.Integration.Models.WorkFlowGroupDetails import ResponseModel
from DAL.dal import DAL
from Common.AES.EncryptDecryptValue import EncryptDecryptValue
from fastapi import Depends, Response
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.RefreshTokenCommand import RefreshTokenCommand, RefreshToken
from Containers.mediator import mediator
from Common.Redis.redis_service import RedisService
from datetime import datetime, timedelta
from sqlalchemy import text, and_, or_
from sqlalchemy.orm import Session, joinedload
from ORM.models import (
    AuthSoxDetails, 
    LoginHistory, 
    EmployeeScreenMapping, 
    GeneralConfiguration,
    EmployeeMaster
)
import jwt
import os
    
class LoginResponse(BaseModel):
    """Model for login response"""
    auth_token: str
    jwt_token: str
    session_id: str


class LoginHandler():
    """Handler for processing login command"""
    
    def __init__(self, _connection: DAL, encryptor: EncryptDecryptValue, redis_service: RedisService):
        self.db_connection = _connection
        self.encryptor = encryptor
        self.redis_service = redis_service
        
      
    async def handle(self, request: LoginCommand):
        
        try:
            # Get database engine
            engine = await self.db_connection.get_connection(request.subscription_name)
            session = Session(bind=engine)
            
            print("Connected to DB ---------------------------------------------------------------")

            try:
                # Set transaction isolation level
                session.execute(text("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED"))

                # Generate token
                token = str(uuid.uuid4())

                # # Encrypt password
                # encrypted_password = self.encryptor.encrypt_js_value(str(request.password))

                # Query user details using ORM
                auth_details = (
                    session.query(AuthSoxDetails)
                    .options(
                        joinedload(AuthSoxDetails.employee_master)
                    )
                    .filter(AuthSoxDetails.sd_userid == request.emp_code)
                    .first()
                )

                # Get configuration values using ORM
                config_values = (
                    session.query(GeneralConfiguration)
                    .filter(
                        GeneralConfiguration.keyname.in_([
                            'PASSWORDEXPIRYINDAYS',
                            'MultipleLoginEnableToUser',
                            'DefaultAfterLoginPage'
                        ])
                    )
                    .all()
                )

                # Convert config values to dict for easy access
                config_dict = {config.keyname: config.value for config in config_values}

                if not auth_details:
                    # Create failed login history using ORM
                    login_history = LoginHistory(
                        sessionid=token,
                        subscription=request.subscription_name,
                        userid=request.emp_code,
                        type=0,
                        errordesc="Invalid credentials",
                        token=token,
                        login=datetime.utcnow()
                    )
                    session.add(login_history)
                    session.commit()
                    return ResponseModel(code=0, message="Login failed. Invalid credentials.")

                if not request.is_otp_login:
                    # Encrypt password
                    encrypted_password = self.encryptor.encrypt_js_value(str(request.password))

                    # Validate password
                    if auth_details.sd_pwd1 != encrypted_password:
                        # Update fail count using ORM
                        auth_details.sd_failcount = (auth_details.sd_failcount or 0) + 1
                        if auth_details.sd_failcount >= 5:
                            auth_details.sd_sm_statusid = 2

                        # Create failed login history using ORM
                        login_history = LoginHistory(
                            sessionid=token,
                            subscription=request.subscription_name,
                            userid=request.emp_code,
                            type=0,
                            errordesc="Invalid credentials",
                            token=token,
                            login=datetime.utcnow()
                        )
                        session.add(login_history)
                        session.commit()
                        return ResponseModel(code=0, message="Login failed. Invalid credentials.")

                    # Check password expiry
                    if config_dict.get('PASSWORDEXPIRYINDAYS') and auth_details.sd_timestamp:
                        days_since_pwd_change = (datetime.utcnow() - auth_details.sd_timestamp).days
                        if days_since_pwd_change >= int(config_dict['PASSWORDEXPIRYINDAYS']):
                            return ResponseModel(code=0, message="Password Expired")

                multiple_login_enabled = config_dict.get('MultipleLoginEnableToUser') == '1'
                existing_sessions = self.redis_service.get_user_sessions(request.emp_code)

                if existing_sessions and not multiple_login_enabled:
                    # Invalidate existing sessions if kill_previous_session is True
                    if request.kill_previous_session:
                        for session_data in existing_sessions:
                            self.redis_service.invalidate_session(session_data.get('session_id'))
                    else:
                        return ResponseModel(
                            code=0,
                            message="This user is already logged in from another system",
                            data={"already_logged_in_user": True}
                        )

                # Reset fail count and create successful login history using ORM
                auth_details.sd_failcount = 0
                
                login_history = LoginHistory(
                    sessionid=token,
                    subscription=request.subscription_name,
                    userid=request.emp_code,
                    type=1,
                    errordesc="SUCCESS",
                    token=token,
                    login=datetime.utcnow(),
                    signupid=auth_details.employee_master.signupid if auth_details.employee_master else None
                )
                session.add(login_history)
                session.commit()
                
                
                if auth_details.employee_master:
                    auth_details.employee_master.session_id = token
                    auth_details.employee_master.token = token
                
                user_data = {
                    "emp_code": request.emp_code,
                    "subscription": request.subscription_name,
                    "session_id": token,
                    "user_type": auth_details.employee_master.usertype if auth_details.employee_master else 'E',
                 
                }
                
                SESSION_EXPIRY = 900
                
                # Store session in Redis with 15-minute expiration
                self.redis_service.create_session(token, user_data, expiry=SESSION_EXPIRY)
                
                refresh_token_cmd = RefreshTokenCommand(
                    auth_token=token,
                    subscription_name=request.subscription_name
                )
                # Use mediator to send the refresh token command
                refresh_token_result = await mediator.send(refresh_token_cmd)

                if refresh_token_result.code == 1:
                    
                    self.redis_service.link_token_to_session(
                        refresh_token_result.data.token,
                        token
                    )
                    
                    jwt_payload = jwt.decode(
                        refresh_token_result.data.token,
                        os.getenv("JWT_SECRET"),
                        algorithms=["HS256"],
                        options={
                            "verify_aud": False,  # Skip audience validation
                            "verify_exp": False,  # Skip expiration validation for immediate decoding
                            "verify_iss": False,  # Skip issuer validation
                            "verify_nbf": False   # Skip "not before" validation
                        }
                    )
                    
                    session.commit()
                    
                    session_expiry = (datetime.utcnow() + timedelta(seconds=SESSION_EXPIRY)).replace(microsecond=0)

                    response = Response()
                    response.set_cookie(
                        key="session_id",
                        value=token,
                        max_age=session_expiry,
                        httponly=True,
                        secure=True,
                        samesite="lax"
                    )
                    response.set_cookie(
                        key="jwt_token",
                        value=refresh_token_result.data.token,
                        max_age=session_expiry,
                        httponly=True,
                        secure=True,
                        samesite="lax"
                    )
                    response.set_cookie(
                        key="user_id",
                        value=request.emp_code,
                        max_age=session_expiry,
                        httponly=True,
                        secure=True,
                        samesite="lax"
                    )

                    return ResponseModel(
                        code=1,
                        message="Login successful",
                        data={
                            **jwt_payload,  # Include all JWT payload fields in the response
                            "response": response
                        }
                    )
                else:
                    return refresh_token_result

            finally:
                session.close()
                engine.dispose()

        except Exception as e:
            print(f"Login error: {e}")
            return ResponseModel(
                code=-1,
                message=f"An error occurred during login: {str(e)}"
            )