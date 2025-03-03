import uuid
from zinghr_backend.app.MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.LoginCommand import LoginCommand
from zinghr_backend.app.MicroServices.ZingAuth.Application.Integration.Models.WorkFlowGroupDetails import ResponseModel
from zinghr_backend.app.DAL.dal import DAL
from zinghr_backend.app.Common.AES.EncryptDecryptValue import EncryptDecryptValue
from fastapi import Depends
from diator.requests import RequestHandler 

import asyncio
import json

class LoginHandler(RequestHandler[LoginCommand, ResponseModel]):
    """Handler for processing login command"""
    
    def __init__(self, _connection: DAL, encryptor: EncryptDecryptValue):
        self.db_connection = _connection
        self.encryptor = encryptor
        
      
    async def handle(self, request: LoginCommand):
        print("reached here - finding database")
        try: 
            connection = await self.db_connection.get_connection(request.subscription_name)
            print(connection)
        except Exception as e:
            print(e)        
       
        async with connection.acquire() as conn:
            async with conn.cursor() as cursor:
                await conn.execute(f"USE elcm_{request.subscription_name}")
                
                token = str(uuid.uuid4())
                
                encrypted_password = self.encryptor.encrypt_js_value(str(request.password))

                query_params = {
                    "SubscriptionName": request.subscription_name,
                    "EmpCode": request.emp_code,
                    "Password": encrypted_password,
                    "IpAddress": "172.16.28.4",  # Placeholder for request IP
                    "ComputerName": "172.16.28.4",  # Placeholder for hostname
                    "MacAddress": request.mac_address if request.mac_address else "NOMAC",
                    "SessionId": request.session_id,
                    "Guid": token,
                    "Latitude": request.latitude,
                    "Longitude": request.longitude,
                    "Source": request.source,
                    "UserType": request.user_type,
                    "DeviceId": "Mozilla/5.0",  # Placeholder for user-agent
                    "AppVersion": request.application_version or "1.0.0",
                    "Location": request.formatted_address,
                }
                
                query = """EXEC [Authentication].[Login] ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?"""
                        
                await cursor.execute(query, query_params)
                result = await cursor.fetchone()
                
                if result and result["Status"].lower() == "success":
                    return ResponseModel(
                        code=1,
                        data={
                                "AuthToken": token,
                            }
                        )

                return ResponseModel(code=0, message="Login failed")