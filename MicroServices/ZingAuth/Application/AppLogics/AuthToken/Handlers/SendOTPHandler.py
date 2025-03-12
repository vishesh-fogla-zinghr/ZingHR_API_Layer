from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.SendOTPCommand import SendOTPCommand
from MicroServices.ZingAuth.Application.Integration.Models.WorkFlowGroupDetails import ResponseModel
from DAL.dal import DAL
import httpx
from ORM.models import TestOTP, OTPVerification
import httpx
import os
import random

class SendOTPHandler():
    """Handler for processing send OTP command"""
    
    def __init__(self, _connection: DAL):
        self.db_connection = _connection

    async def handle(self, request: SendOTPCommand) -> ResponseModel:
        try:
            # Get database engine
            engine = await self.db_connection.get_connection(request.subscription_name)
            session = Session(bind=engine)

            try:
                
                db_phone_number = request.phone_number.replace("+91", "")
                
                # Check if phone number exists in TestOTP table
                employee = session.query(TestOTP).filter(
                    TestOTP.ED_Mobile == db_phone_number,
                    TestOTP.IsActive == True
                ).first()

                if not employee:
                    return ResponseModel(
                        code=0,
                        message="Phone number not registered in the system."
                    )

                # Generate OTP and reference ID
                otp = ''.join(random.choices('0123456789', k=6))
                reference_id = str(uuid4())
                expiry_minutes = int(os.getenv("MSG91_OTP_EXPIRY", "5"))

                #Create OTP verification record
                otp_verification = OTPVerification(
                    ED_EMPCode=employee.ED_EMPCode,
                    OTP=otp,
                    ReferenceID=reference_id,
                    ExpiresAt=datetime.utcnow() + timedelta(minutes=expiry_minutes),
                    IsVerified=False,
                    AttemptCount=0
                )

                session.add(otp_verification)
                
                # Call MSG91 API to send OTP
                msg91_url = os.getenv("MSG91_API_URL")
                params = {
                    "template_id": os.getenv("MSG91_TEMPLATE_ID"),
                    "mobile": request.phone_number,
                    "authkey": os.getenv("MSG91_AUTH_KEY"),
                    "otp_expiry": str(expiry_minutes),
                    "otp": otp,
                    "realTimeResponse": "true"
                }

                async with httpx.AsyncClient() as client:
                    response = await client.get(msg91_url, params=params)
                    msg91_response = response.json()

                if msg91_response.get("type") != "success":
                    return ResponseModel(
                        code=0,
                        message=f"Failed to send OTP: {msg91_response.get('message', 'Unknown error')}"
                    )

                # Commit the transaction
                session.commit()

                return ResponseModel(   
                    code=1,
                    message="OTP sent successfully",
                    data={
                        "request_id": msg91_response.get("request_id"),
                        "type": msg91_response.get("type"),
                        "reference_id": reference_id
                    }
                )

            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
                engine.dispose()

        except Exception as e:
            return ResponseModel(
                code=-1,
                message=f"Failed to process request: {str(e)}"
            ) 