from datetime import datetime
from sqlalchemy.orm import Session
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.VerifyOTPCommand import VerifyOTPCommand
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.LoginCommand import LoginCommand
from MicroServices.ZingAuth.Application.Integration.Models.WorkFlowGroupDetails import ResponseModel
from DAL.dal import DAL
from ORM.models import TestOTP, OTPVerification
from Containers.mediator import mediator
import httpx
import os

class VerifyOTPHandler():
    """Handler for verifying OTP and processing login"""
    
    def __init__(self, _connection: DAL):
        self.db_connection = _connection
        self.mediator = mediator

    async def handle(self, request: VerifyOTPCommand) -> ResponseModel:
        try:
            # Get database engine
            engine = await self.db_connection.get_connection(request.subscription_name)
            session = Session(bind=engine)

            try:
                # Get OTP verification record - just to check attempts and prevent reuse
                otp_verification = session.query(OTPVerification).filter(
                    OTPVerification.ReferenceID == request.reference_id,
                    OTPVerification.IsVerified == False
                ).first()

                if not otp_verification:
                    return ResponseModel(
                        code=0,
                        message="Invalid or already used reference ID"
                    )

                if otp_verification.AttemptCount >= 3:
                    return ResponseModel(
                        code=0,
                        message="Maximum verification attempts exceeded"
                    )

                # Increment attempt count
                otp_verification.AttemptCount += 1
                session.commit()

                # Call MSG91 verify API for actual OTP verification
                verify_url = "https://control.msg91.com/api/v5/otp/verify"
                params = {
                    "otp": request.otp,
                    "mobile": request.phone_number
                }
                headers = {
                    "authkey": os.getenv("MSG91_AUTH_KEY")
                }

                async with httpx.AsyncClient() as client:
                    response = await client.get(verify_url, params=params, headers=headers)
                    msg91_response = response.json()

                if msg91_response.get("type") != "success":
                    return ResponseModel(
                        code=0,
                        message=msg91_response.get("message", "OTP verification failed")
                    )

                # Get user details from TestOTP table
                db_phone_number = request.phone_number.replace("+91", "")
                
                #db_phone_number = "9902899100"
                employee = session.query(TestOTP).filter(
                    TestOTP.ED_Mobile == db_phone_number,
                    TestOTP.IsActive == True
                ).first()

                if not employee:
                    return ResponseModel(
                        code=0,
                        message="User not found"
                    )

                # Mark reference as verified
                otp_verification.IsVerified = True
                otp_verification.VerifiedAt = datetime.utcnow()
                session.commit()

                # Process login
                login_command = LoginCommand(
                    subscription_name=request.subscription_name,
                    emp_code=employee.ED_EMPCode,  # Using employee code as username
                    is_otp_login=True
                )

                # Call login command through mediator
                login_response = await self.mediator.send(login_command)
                return login_response

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