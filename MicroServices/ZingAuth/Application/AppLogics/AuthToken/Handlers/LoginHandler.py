import uuid
from pydantic import BaseModel
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.LoginCommand import LoginCommand
from MicroServices.ZingAuth.Application.Integration.Models.WorkFlowGroupDetails import ResponseModel
from DAL.dal import DAL
from Common.AES.EncryptDecryptValue import EncryptDecryptValue
from fastapi import Depends


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



import asyncio
import json

class QueryParameters(BaseModel):
    DatabaseName: str
    EmpCode: str
    Password: str
    Token: str


class LoginHandler():
    """Handler for processing login command"""
    
    def __init__(self, _connection: DAL, encryptor: EncryptDecryptValue):
        self.db_connection = _connection
        self.encryptor = encryptor
        
      
    async def handle(self, request: LoginCommand):
        
        try:
            # Get database engine
            engine = await self.db_connection.get_connection(request.subscription_name)
            session = Session(bind=engine)

            try:
                # Set transaction isolation level
                session.execute(text("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED"))

                # Generate token
                token = str(uuid.uuid4())

                # Encrypt password
                encrypted_password = self.encryptor.encrypt_js_value(str(request.password))

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
                        token=token
                    )
                    session.add(login_history)
                    session.commit()
                    return ResponseModel(code=0, message="Login failed. Invalid credentials.")

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
                        token=token
                    )
                    session.add(login_history)
                    session.commit()
                    return ResponseModel(code=0, message="Login failed. Invalid credentials.")

                # Check password expiry
                if config_dict.get('PASSWORDEXPIRYINDAYS') and auth_details.sd_timestamp:
                    days_since_pwd_change = (datetime.utcnow() - auth_details.sd_timestamp).days
                    if days_since_pwd_change >= int(config_dict['PASSWORDEXPIRYINDAYS']):
                        return ResponseModel(code=0, message="Password Expired")

                # Reset fail count and create successful login history using ORM
                auth_details.sd_failcount = 0
                
                login_history = LoginHistory(
                    sessionid=token,
                    subscription=request.subscription_name,
                    userid=request.emp_code,
                    type=1,
                    errordesc="SUCCESS",
                    token=token
                )
                session.add(login_history)
                session.commit()

                return ResponseModel(
                    code=1,
                    message="Login successful",
                    data={
                        "AuthToken": token,
                        "UserInfo": {
                            "EmpCode": request.emp_code,
                            "SubscriptionName": request.subscription_name,
                            "LandingPage": config_dict.get('DefaultAfterLoginPage'),
                            "LastLogin": datetime.utcnow().isoformat(),
                            "EmployeeId": auth_details.employee_master.employeeid if auth_details.employee_master else None
                        }
                    }
                )

            finally:
                session.close()
                engine.dispose()

        except Exception as e:
            print(f"Login error: {e}")
            return ResponseModel(
                code=-1,
                message=f"An error occurred during login: {str(e)}"
            )
        
        # print("reached here - finding database")
        # try: 
        #     # Get the connection
        #     connection = await self.db_connection.get_connection(request.subscription_name)
        #     # print("Connection established")
            
        #     # # Generate a unique token for this session
        #     # token = str(uuid.uuid4())
        #     # print(token)
            
        #     # # Encrypt the password
        #     # encrypted_password = self.encryptor.encrypt_js_value(str(request.password))
            
        #     # print("Password: ", encrypted_password)
            
        #     # # Create a cursor and execute the stored procedure
        #     # async with connection.cursor() as cursor:
        #     #     # Set the database context
        #     #     db_name = f"elcm_{request.subscription_name.lower()}"
        #     #     await cursor.execute(f"USE {db_name}")
                
        #     #     params = QueryParameters(DatabaseName=request.subscription_name, EmpCode=request.emp_code, Password=encrypted_password, Token=token)
                
        #     #     # Execute the stored procedure
        #     #     query = """EXEC [Authentication].[Login] @SubscriptionName=?, @Empcode=?, @Password=?, @Guid=?"""
                
        #     #     print("Query for authentication...............................................")
        #     #     print(query, (params.DatabaseName, params.EmpCode, params.Password, params.Token))
                
        #     #     await cursor.execute(query, (params.DatabaseName, params.EmpCode, params.Password, params.Token))
                
        #     #     # Fetch the result
        #     #     result = await cursor.fetchone()
                
        #     #     # Check if login was successful
        #     #     if result and result.Status.lower() == "success":
        #     #         return ResponseModel(
        #     #             code=1,
        #     #             message="Login successful",
        #     #             data={
        #     #                 "AuthToken": token,
        #     #                 "UserInfo": {
        #     #                     "EmpCode": request.emp_code,
        #     #                     "SubscriptionName": request.subscription_name
        #     #                 }
        #     #             }
        #     #         )
                
        #     #     # Return failure response
        #     #     return ResponseModel(
        #     #         code=0, 
        #     #         message="Login failed. Invalid credentials or user not found."
        #     #     )
            
            
            
        #     session = Session(bind=connection)

        #     try:
        #         # Set transaction isolation level
        #         session.execute(text("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED"))

        #         # Generate token
        #         token = str(uuid.uuid4())

        #         # Encrypt password
        #         encrypted_password = self.encryptor.encrypt_js_value(str(request.password))

        #         # Get all required data in a single query
        #         result = session.execute(
        #             text("""
        #             SELECT 
        #                 a.sd_userid, a.sd_pwd1, a.sd_sm_statusid, a.sd_failcount, 
        #                 a.sd_timestamp, a.sd_init,
        #                 e.employeeid, e.signupid, e.usertype,
        #                 gc1.value as pwd_expiry_days,
        #                 gc2.value as multiple_login_enabled,
        #                 gc3.value as default_landing_page
        #             FROM AUTH_SOXDETAILS a
        #             LEFT JOIN ED.EMPLOYEEMASTER e ON e.employeecode = a.sd_userid
        #             LEFT JOIN ess_genralconfiguration gc1 ON gc1.keyname = 'PASSWORDEXPIRYINDAYS'
        #             LEFT JOIN ess_genralconfiguration gc2 ON gc2.keyname = 'MultipleLoginEnableToUser'
        #             LEFT JOIN ess_genralconfiguration gc3 ON gc3.keyname = 'DefaultAfterLoginPage'
        #             WHERE a.sd_userid = :emp_code
        #             """),
        #             {"emp_code": request.emp_code}
        #         ).first()

        #         if not result:
        #             # Create failed login history for non-existent user
        #             login_entry = LoginHistory(
        #                 sessionid=token,
        #                 subscription=request.subscription_name,
        #                 userid=request.emp_code,
        #                 type=0,
        #                 errordesc="Invalid credentials",
        #                 token=token,
        #                 ipaddress=request.ip_address,
        #                 computername=request.computer_name,
        #                 macaddress=request.mac_address,
        #                 latitude=request.latitude,
        #                 longitude=request.longitude,
        #                 location=request.location,
        #                 source=request.source,
        #                 appversion=request.app_version,
        #                 deviceid=request.device_id
        #             )
        #             session.add(login_entry)
        #             session.commit()
        #             return ResponseModel(code=0, message="Login failed. Invalid credentials.")

        #         # Validate password
        #         if result.sd_pwd1 != encrypted_password:
        #             # Update fail count in a single query
        #             new_fail_count = (result.sd_failcount or 0) + 1
        #             new_status = 2 if new_fail_count >= 5 else result.sd_sm_statusid

        #             session.execute(
        #                 text("""
        #                 UPDATE AUTH_SOXDETAILS 
        #                 SET sd_failcount = :fail_count, sd_sm_statusid = :status
        #                 WHERE sd_userid = :emp_code
        #                 """),
        #                 {
        #                     "fail_count": new_fail_count,
        #                     "status": new_status,
        #                     "emp_code": request.emp_code
        #                 }
        #             )

        #             # Create failed login history
        #             login_entry = LoginHistory(
        #                 sessionid=token,
        #                 subscription=request.subscription_name,
        #                 userid=request.emp_code,
        #                 type=0,
        #                 errordesc="Invalid credentials",
        #                 token=token,
        #                 ipaddress=request.ip_address,
        #                 computername=request.computer_name,
        #                 macaddress=request.mac_address,
        #                 latitude=request.latitude,
        #                 longitude=request.longitude,
        #                 location=request.location,
        #                 signupid=result.signupid,
        #                 source=request.source,
        #                 appversion=request.app_version,
        #                 deviceid=request.device_id
        #             )
        #             session.add(login_entry)
        #             session.commit()
        #             return ResponseModel(code=0, message="Login failed. Invalid credentials.")

        #         # Check password expiry
        #         if result.pwd_expiry_days and result.sd_timestamp:
        #             days_since_pwd_change = (datetime.utcnow() - result.sd_timestamp).days
        #             if days_since_pwd_change >= int(result.pwd_expiry_days):
        #                 return ResponseModel(code=0, message="Password Expired")

        #         # Check multiple login in a single query
        #         if not result.multiple_login_enabled or result.multiple_login_enabled != '1':
        #             active_session = session.execute(
        #                 text("""
        #                 SELECT TOP 1 id, sessionid, token 
        #                 FROM LoginHistory 
        #                 WHERE userid = :emp_code 
        #                 AND errordesc = 'SUCCESS' 
        #                 AND logout IS NULL 
        #                 AND login > :cutoff_time
        #                 """),
        #                 {
        #                     "emp_code": request.emp_code,
        #                     "cutoff_time": datetime.utcnow() - timedelta(minutes=30)
        #                 }
        #             ).first()

        #             if active_session and not request.kill_previous_session:
        #                 return ResponseModel(code=0, message="This user is already logged in from another system")
        #             elif active_session:
        #                 # Log out previous session
        #                 session.execute(
        #                     text("""
        #                     UPDATE LoginHistory 
        #                     SET logout = :logout_time, errordesc = 'Log Out'
        #                     WHERE id = :session_id
        #                     """),
        #                     {
        #                         "logout_time": datetime.utcnow(),
        #                         "session_id": active_session.id
        #                     }
        #                 )

        #         # Get screen mapping in a single query
        #         screen_mapping = session.execute(
        #             text("""
        #             SELECT pagename, isnewdirectory, alertmessage
        #             FROM [Authentication].EmployeeScreenMapping
        #             WHERE employeecode = :emp_code
        #             AND applicable = 1
        #             AND fromdate <= :current_time
        #             AND todate >= :current_time
        #             """),
        #             {
        #                 "emp_code": request.emp_code,
        #                 "current_time": datetime.utcnow()
        #             }
        #         ).first()

        #         # Reset fail count and create successful login history in a single transaction
        #         session.execute(
        #             text("""
        #             UPDATE AUTH_SOXDETAILS SET sd_failcount = 0 WHERE sd_userid = :emp_code;
                    
        #             INSERT INTO LoginHistory (
        #                 sessionid, subscription, userid, type, errordesc, token,
        #                 ipaddress, computername, macaddress, latitude, longitude,
        #                 location, signupid, source, appversion, deviceid
        #             ) VALUES (
        #                 :sessionid, :subscription, :userid, 1, 'SUCCESS', :token,
        #                 :ipaddress, :computername, :macaddress, :latitude, :longitude,
        #                 :location, :signupid, :source, :appversion, :deviceid
        #             )
        #             """),
        #             {
        #                 "emp_code": request.emp_code,
        #                 "sessionid": token,
        #                 "subscription": request.subscription_name,
        #                 "userid": request.emp_code,
        #                 "token": token,
        #                 "ipaddress": request.ip_address,
        #                 "computername": request.computer_name,
        #                 "macaddress": request.mac_address,
        #                 "latitude": request.latitude,
        #                 "longitude": request.longitude,
        #                 "location": request.location,
        #                 "signupid": result.signupid,
        #                 "source": request.source,
        #                 "appversion": request.app_version,
        #                 "deviceid": request.device_id
        #             }
        #         )
        #         session.commit()

        #         return ResponseModel(
        #             code=1,
        #             message="Login successful",
        #             data={
        #                 "AuthToken": token,
        #                 "UserInfo": {
        #                     "EmpCode": request.emp_code,
        #                     "SubscriptionName": request.subscription_name,
        #                     "LandingPage": screen_mapping.pagename if screen_mapping else result.default_landing_page,
        #                     "IsNewDirectory": screen_mapping.isnewdirectory if screen_mapping else False,
        #                     "AlertMessage": screen_mapping.alertmessage if screen_mapping else None,
        #                     "LastLogin": datetime.utcnow().isoformat()
        #                 }
        #             }
        #         )

        #     finally:
        #         session.close()
                
        # except Exception as e:
        #     print(f"Login error: {e}")
        #     return ResponseModel(
        #         code=-1,
        #         message=f"An error occurred during login: {str(e)}"
        #     )