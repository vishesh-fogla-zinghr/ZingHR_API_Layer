from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import requests
import os
from datetime import datetime
from Common.Models import ResponseModel


# Define the request model
class PunchInOutEventRequest(BaseModel):
    SignUpID: int
    SubscriptionName: str
    employeeCode: str
    swipeDateTime: str
    inOutFlag: int


# Initialize FastAPI Router
router = APIRouter()

@router.post("/punch-in-out-event", response_model=ResponseModel)
def punch_in_out_event(request: PunchInOutEventRequest):
    try:
        # Convert swipeDateTime to datetime object
        swipe_dt = datetime.strptime(request.swipeDateTime, "%Y-%m-%d %H:%M:%S")
        
        # Construct API URL from environment variables
        api_url = os.getenv("IntegrationMservices", "") + "/api/v1/TNA/PunchInOutevent"
        
        # Prepare the request payload
        payload = {
            "signupId": request.SignUpID,
            "subscriptionName": request.SubscriptionName,
            "employeeCode": request.employeeCode,
            "swipeDateTime": swipe_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "inOutFlag": request.inOutFlag
        }
        
        # Set headers
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        
        # Send the request
        response = requests.post(api_url, json=payload, headers=headers)
        
        # Read response content
        response_content = response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return ResponseModel(Code=0, Message="success")
