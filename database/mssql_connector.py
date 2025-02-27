import urllib.parse
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from zinghr_backend.config import settings
from zinghr_backend.DAL.dbconnection import DBConnection
import asyncio

import os
import pyodbc

async def initialize_database(subscription_name: str):
    """Initialize the database connection for a given subscription name."""
    db = DBConnection()

    # Fetch connection string for the given subscription name
    conn_str = await db.get_connection_string_from_db(subscription_name)    
    
    params = urllib.parse.quote_plus(conn_str)
    
    conn_str = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus('DRIVER={ODBC Driver 17 for SQL Server};' + params)}"
       

    if not conn_str:
        raise ValueError("Failed to retrieve a valid connection string.")
    
    # Create the SQLAlchemy engine
    engine = create_engine(conn_str, echo=True)

    try:
        with engine.connect() as connection:
            
            print(f"Database connection successful for {subscription_name}!")
            
            
            transaction = connection.begin()
            
            try:
                
                query = text("EXEC [Common].[GetEmployeeGeneralInfo] @EmployeeCode=:employee_code")
                result = connection.execute(query, {"employee_code": 'DH02'})
                rows = result.fetchall()
                
                print(rows)

                # transaction.commit()  # Explicitly commit transaction
                # for row in rows:
                #     #column_names = result.keys()  # Get column names
                    
                #     column_names = [desc[0] for desc in result.cursor.description]
                #     if isinstance(row, tuple):  # Check if row is a tuple
                #         for col_name, value in zip(column_names, row):
                #             print(f"{col_name}: {value}")  # Print column-value pairs
                # else:
                #     print("Unexpected row format:", row)  # Print each column on a new line
                    
            except Exception as e:
                transaction.rollback()  # Rollback on error
                print("Error:", e)
            
            # query = text("EXEC [Common].[GetEmployeeGeneralInfo] @EmployeeCode=:employee_code")

            # # Execute stored procedure with parameter values
            # result = connection.execute(query, {"employee_code": 194355})
            
            # rows = result.fetchall()
            
            # for row in rows:
            #     print(row)
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