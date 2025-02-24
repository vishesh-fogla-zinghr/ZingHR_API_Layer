# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

class Settings:
    # Existing settings...
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "1234")
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_DB: str = os.getenv("MYSQL_DB", "claims_db")
    
    COCKROACH_USER: str = os.getenv("COCKROACH_USER", "root")
    COCKROACH_PASSWORD: str = os.getenv("COCKROACH_PASSWORD", "1234")
    COCKROACH_HOST: str = os.getenv("COCKROACH_HOST", "localhost")
    COCKROACH_PORT: str = os.getenv("COCKROACH_PORT", "26257")
    COCKROACH_DB: str = os.getenv("COCKROACH_DB", "recruitment_db")
    
    # New MSSQL settings
    MSSQL_USER: str = os.getenv("MSSQL_USER", "sa")
    MSSQL_PASSWORD: str = os.getenv("MSSQL_PASSWORD", '1234')
    MSSQL_HOST: str = os.getenv("MSSQL_HOST", "DVH\\SQLEXPRESS")
    MSSQL_PORT: int = int(os.getenv("MSSQL_PORT", 1433))
    MSSQL_DB: str = os.getenv("MSSQL_DB", "employeee_db")
    MSSQL_DRIVER: str = os.getenv("MSSQL_DRIVER", "ODBC+Driver+17+for+SQL+Server")

settings = Settings()
