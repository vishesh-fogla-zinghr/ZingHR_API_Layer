from fastapi import FastAPI
from MicroServices.ZingAuth.API.Controllers.v2.AuthController import router
from Containers.container.AppContainer import mediator
from dotenv import load_dotenv
import os


load_dotenv()

app = FastAPI(title="Multi-DB FastAPI Application")

app.include_router(router, prefix="/auth", tags=["Authentication"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Multi-DB FastAPI Application"}
