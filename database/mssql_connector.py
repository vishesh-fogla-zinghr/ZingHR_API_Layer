import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from zinghr_backend.app.config import settings
from zinghr_backend.app.DAL.dal import DAL
from zinghr_backend.app.DAL.dbconnection import DBConnection
import asyncio

import os
import pyodbc

async def initialize_database(subscription_name: str):
    """Initialize the database connection for a given subscription name."""
    
    db_connection = DBConnection()
    db = DAL(db_connection)

    # Fetch connection string for the given subscription name
    conn_str = await db.get_connection(subscription_name)   
    
    params = urllib.parse.quote_plus(conn_str)
    
    conn_str = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus('DRIVER={ODBC Driver 17 for SQL Server};' + params)}"
       

    if not conn_str:
        raise ValueError("Failed to retrieve a valid connection string.")
    
    # Create the SQLAlchemy engine
    engine = create_engine(conn_str, echo=True)

    try:
        with engine.connect() as connection:
            print(f"Database connection successful for {subscription_name}!")
    except Exception as e:
        print(f"Database connection failed for {subscription_name}: {e}")
        return None

    # Create session and base
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

    return engine, SessionLocal, Base


# Example usage:
subscription_name = "qadb"
engine, SessionLocal, Base = asyncio.run(initialize_database(subscription_name))