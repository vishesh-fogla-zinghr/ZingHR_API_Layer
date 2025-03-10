from fastapi import FastAPI
from MicroServices.ZingAuth.API.Controllers.v2.AuthController import router
from Containers.container.AppContainer import mediator
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from datetime import datetime
import os


load_dotenv()

API_BASE_PATH = os.getenv("API_BASE_PATH").rstrip('/')

app = FastAPI(
    title="Multi-DB FastAPI Application",
    docs_url=f"{API_BASE_PATH}/docs",  # Swagger UI
    openapi_url=f"{API_BASE_PATH}/openapi.json"  # OpenAPI schema
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(router, prefix=f"{API_BASE_PATH}/auth", tags=["Authentication"])

@app.get(API_BASE_PATH)
def read_root():
    return {"message": "Welcome to the Multi-DB FastAPI Application"}

@app.get(f"{API_BASE_PATH}/health")
def health_check():
    return {"status": "healthy", "timestamp": str(datetime.utcnow())}
