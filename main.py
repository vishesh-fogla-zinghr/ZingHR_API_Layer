from fastapi import FastAPI
from app.database.mysql_connector import engine as mysql_engine, Base as MySQLBase
from app.database.cockroach_connector import cockroach_engine, CockroachBase
from app.database.mssql_connector import engine as mssql_engine, Base as MSSQLBase
from app.models import claims_model, recruitment_model, employee_model
from app.routers import claims_router, recruitment_router, employee_router

# Create MySQL tables (for claims)
MySQLBase.metadata.create_all(bind=mysql_engine)

# Create CockroachDB tables (for recruitment)
CockroachBase.metadata.create_all(bind=cockroach_engine)

# Create MSSQL tables (for employee data)
MSSQLBase.metadata.create_all(bind=mssql_engine)

app = FastAPI(title="Multi-DB FastAPI Application")

app.include_router(claims_router.router, prefix="/claims", tags=["Claims"])
app.include_router(recruitment_router.router, prefix="/recruitments", tags=["Recruitment"])
app.include_router(employee_router.router, prefix="/employees", tags=["Employees"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Multi-DB FastAPI Application"}
