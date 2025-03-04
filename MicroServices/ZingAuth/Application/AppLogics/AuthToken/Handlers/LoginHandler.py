import uuid
from pydantic import BaseModel
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.LoginCommand import LoginCommand
from MicroServices.ZingAuth.Application.Integration.Models.WorkFlowGroupDetails import ResponseModel
from DAL.dal import DAL
from Common.AES.EncryptDecryptValue import EncryptDecryptValue
from fastapi import Depends

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
        print("reached here - finding database")
        try: 
            # Get the connection
            connection = await self.db_connection.get_connection(request.subscription_name)
            print("Connection established")
            
            # Generate a unique token for this session
            token = str(uuid.uuid4())
            print(token)
            
            # Encrypt the password
            encrypted_password = self.encryptor.encrypt_js_value(str(request.password))
            
            print("Password: ", encrypted_password)
            
            # Create a cursor and execute the stored procedure
            async with connection.cursor() as cursor:
                # Set the database context
                db_name = f"elcm_{request.subscription_name.lower()}"
                await cursor.execute(f"USE {db_name}")
                
                params = QueryParameters(DatabaseName=request.subscription_name, EmpCode=request.emp_code, Password=encrypted_password, Token=token)
                
                # Execute the stored procedure
                query = """EXEC [Authentication].[Login] @SubscriptionName=?, @Empcode=?, @Password=?, @Guid=?"""
                
                print("Query for authentication...............................................")
                print(query, (params.DatabaseName, params.EmpCode, params.Password, params.Token))
                
                await cursor.execute(query, (params.DatabaseName, params.EmpCode, params.Password, params.Token))
                
                # Fetch the result
                result = await cursor.fetchone()
                
                # Check if login was successful
                if result and result.Status.lower() == "success":
                    return ResponseModel(
                        code=1,
                        message="Login successful",
                        data={
                            "AuthToken": token,
                            "UserInfo": {
                                "EmpCode": request.emp_code,
                                "SubscriptionName": request.subscription_name
                            }
                        }
                    )
                
                # Return failure response
                return ResponseModel(
                    code=0, 
                    message="Login failed. Invalid credentials or user not found."
                )
                
        except Exception as e:
            print(f"Login error: {e}")
            return ResponseModel(
                code=-1,
                message=f"An error occurred during login: {str(e)}"
            )