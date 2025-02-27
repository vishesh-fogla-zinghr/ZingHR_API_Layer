import uuid
from pydiator_core.interfaces import BaseHandler
from zinghr_backend.app.MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.LoginCommand import LoginCommand
from zinghr_backend.app.MicroServices.ZingAuth.Application.Integration.Models.WorkFlowGroupDetails import ResponseModel
from zinghr_backend.app.DAL.idb_connection import IDBConnection
from zinghr_backend.app.Common.AES.Encrypt_Decrypt_Value import Encrypt_Decrypt_Value
from pydiator_core.mediatr import pydiator
from fastapi import Depends
from typing import Optional
import asyncio
import json

class LoginHandler(BaseHandler):
    """Handler for processing login command"""
    
    def __init__(self, _connection: IDBConnection, encryptor: Encrypt_Decrypt_Value):
        self.db_connection = _connection
        self.encryptor = encryptor
        self.mediator = pydiator

    async def handle(self, request: LoginCommand):
        connection = self.db_connection.get_connection(request.subscription_name)
        
        async with connection.acquire() as conn:
            async with conn.cursor() as cursor:
                await conn.execute(f"USE elcm_{request.subscription_name}")
                
                token = str(uuid.uuid4())
                
                encrypted_password = self.encryptor.EncryptJSValue(str(request.password))

                query_params = {
                    "SubscriptionName": request.subscription_name,
                    "EmpCode": request.emp_code,
                    "Password": encrypted_password,
                    "IpAddress": "192.168.1.1",  # Placeholder for request IP
                    "ComputerName": "localhost",  # Placeholder for hostname
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