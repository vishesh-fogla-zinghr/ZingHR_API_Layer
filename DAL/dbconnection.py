import os
import threading
import pyodbc
from .idb_connection import IDBConnection
from pydantic import BaseModel
from typing import Optional
from .DBModel import DBModel
from .DBModel import DbConnectionString
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from ORM.models import DbDetails, PMSDbDetails, SysDatabase
from urllib.parse import quote_plus


class QueryParameters(BaseModel):
        DatabaseName: str
        TransType: str

class DBConnection(IDBConnection):

    _cnc_encrypted_dbs = {}
    _objcnc_dictionary_connection = {}
    _lock = threading.Lock() 
    
    
    def __init__(self):
        # Create base engine for ELCM_CommonCore
        try:
            conn_str = self.base_connection_string("default")
            print(f"Initializing base engine with connection string: {conn_str}")
            self.base_engine = create_engine(conn_str, echo=True)  # Enable SQL logging
            self.SessionLocal = sessionmaker(bind=self.base_engine)
            # Test the connection
            with self.SessionLocal() as session:
                session.execute(text("SELECT 1"))
                print("Successfully connected to ELCM_CommonCore")
        except Exception as e:
            print(f"Error initializing base engine: {str(e)}")
            raise  

    # def pms_connection_string(self, identity_service) -> str:
    #     """Retrieve the PMS connection string using the identity's subscription name."""
    #     subscription_name = get_identity_subscription_name(identity_service)
    #     return self.pms_connection_string_with_subscription(subscription_name)

    def pms_connection_string_with_subscription(self, subscription_name: str) -> str:
        """Handles fetching or retrieving the cached PMS connection string."""
        key = f"{subscription_name.lower()}-pms"

        with self._lock:  # Ensure thread-safe access
            if key not in self._objcnc_dictionary_connection:
                connection_string = self.get_connection_string_from_db(subscription_name, is_pms=True)
                self._objcnc_dictionary_connection[key] = connection_string
                self.add_subscription_to_hash_table(key)

        return self._objcnc_dictionary_connection.get(key, "")


    def base_connection_string(self, subscription_name: str) -> str:
        """Generate a SQLAlchemy compatible connection URL."""

        subscription_name = subscription_name.lower().strip()

        hostname = os.getenv("SQLSERVER_HOST")
        password = os.getenv("PASSWORD")
        database = os.getenv("DATABASE")
        user = os.getenv("SQLUSER")
        driver = os.getenv("MSSQL_DRIVER", "ODBC Driver 17 for SQL Server").strip()
        
        print(f"Environment variables:")
        print(f"SQLSERVER_HOST: {hostname}")
        print(f"DATABASE: {database}")
        print(f"SQLUSER: {user}")
        print(f"MSSQL_DRIVER: {driver}")
        print(f"PASSWORD: {'*' * len(password)}")

        # Check if any required values are missing
        if not all([hostname, password, database, user]):
            missing = []
            if not hostname: missing.append("SQLSERVER_HOST")
            if not password: missing.append("PASSWORD")
            if not database: missing.append("DATABASE")
            if not user: missing.append("SQLUSER")
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        # Format for SQLAlchemy with explicit port and quoted driver
        encoded_password = quote_plus(password)
        encoded_user = quote_plus(user)
        quoted_driver = quote_plus(driver)

        connection_string = (
            f"mssql+pyodbc://{encoded_user}:{encoded_password}@{hostname}/{database}?"
            f"driver={quoted_driver}&"
            f"TrustServerCertificate=yes&"
            f"Encrypt=yes&"
            f"Connection+Timeout=30"
        )
        
        # Print the connection string (mask password)
        masked_conn_string = connection_string.replace(encoded_password, "*" * len(encoded_password))
        print(f"Generated connection string: {masked_conn_string}")

        return connection_string

    def add_subscription_to_hash_table(self, subscription_name: str):
        """Adds a subscription to the hash table if not already present."""
        try:
            subscription_name = subscription_name.strip().lower()
                
            print("Database to add:", subscription_name)
                
            with self._lock:  # Ensure thread-safe dictionary access
                if subscription_name not in self._cnc_encrypted_dbs:
                    connection_string = self.get_connection(subscription_name)
                    
                    print("String to add: ", connection_string)
                    
                    with pyodbc.connect(connection_string) as conn:
                        cursor = conn.cursor()
                        cursor.execute("{CALL [API].[GetAadharValutFlag]}")
                        result = cursor.fetchone()
                        
                        print("Sp called aadhar:", result)

                        if result and result[0] == "1":
                            self._cnc_encrypted_dbs[subscription_name] = subscription_name  # Equivalent to TryAdd()
                            
                        print("Out of add function")

        except Exception as e:
            pass  # Silently handling exceptions, just like in C#
        
    def check_db(self, subscription_name: str) -> bool:
        """Checks the database for a given subscription name."""

        try:
            # Format the subscription name
            subname = subscription_name.lower().strip()
            if subname == "pushnotification" or subname == "pms":
                subname = subname
            else:
                subname = f"elcm_{subscription_name}"
                
            print(f"Checking database: {subname}")
            
             # Create a new session for this check
            session = self.SessionLocal()
            try:
                # First test if we can connect at all
                session.execute(text("SELECT 1")).first()
                print("Basic connection test successful")

                # Now try the actual database check
                db_count = (
                    session.query(SysDatabase)
                    .filter(
                        SysDatabase.name == subname,
                        SysDatabase.name != 'ELCM_KTKBANK'
                    )
                    .count()
                )

                print(f"CheckDB result for {subname}: {db_count}")
                if db_count > 0: 
                    return True
            
            except Exception as e:
                print(f"Error in check_db execution: {str(e)}")
                return False
            finally:
                session.close()
                
        except Exception as e:
            print(f"Error in check_db: {str(e)}")
            return False
        
    async def get_connection_string_from_db(self, subscription_name: str, is_pms: bool = False) -> str:
        """
        Fetches the connection string from the database for a given subscription name.

        :param subscription_name: The subscription name to fetch connection string for.
        :param is_pms: Flag indicating if the connection string is for PMS (default False).
        :return: The constructed connection string.
        """
        # Prepare query parameters
        query_parameters = {"@SubscriptionName": subscription_name}

        subname = subscription_name.lower().strip()
        if subname == "pushnotification" or subname == "commondatarepository":
            subname = subname
        else:
            subname = f"elcm_{subscription_name}"

        # Connect to the database using pyodbc
        connection_string = self.base_connection_string(subscription_name)
        
        # Establish connection
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            
            # Execute the stored procedure and fetch result
            cursor.execute("{CALL [Info].[GetDbInfo] (?)}", query_parameters["@SubscriptionName"])
            db = cursor.fetchone()

            # Check if db is None or empty
            if db is None:
                raise ValueError("No data returned from [Info].[GetDbInfo]")
            
            db_model = DBModel(
                server_address=db.ServerAddress,
                info=db.Info,
                pms_server_address=db.PMSServerAddress,
                pms_db=db.PMSDB,
                pms_info=db.PMSInfo
            )

            # Construct the connection string based on is_pms flag
            if is_pms:
                con_string = f"Server={db_model.pms_server_address};Initial Catalog={db_model.pms_db};{db_model.pms_info};"
            else:
                updated_info = db_model.info.replace("User ID=", "UID=").replace("Password=", "PWD=")
                con_string = f"Server={db_model.server_address};Initial Catalog={subname};{updated_info};"

            return con_string
       
        
    async def dispose_connection(self, con: pyodbc.Connection):
        print()
    
    async def delete_hash_connection(self, subscription_name: str) -> None:
        """Deletes a connection from the dictionary if it exists."""
        subsname = subscription_name.lower().strip()

        if subscription_name and subsname in self._objcnc_dictionary_connection:
            try:
                # Remove the entry from the dictionary
                self._objcnc_dictionary_connection.pop(subsname, None)

            except Exception as e:
                print(f"Error while removing connection: {e}")
                
    # def get_connection(self) -> str:
    #     """Fetches the connection string using the subscription name from the identity service."""
    #     subscription_name = self._identity_service.get_identity().subscription_name.lower()
    #     return self.connection_string(subscription_name)
    
    def get_connection(self, subscription_name: str, connection_type: str = "") -> str:
        """Returns the appropriate connection string based on the subscription name and connection type."""

        subscription_name = subscription_name.lower().strip()

        if connection_type == "pms":
            return self.pms_connection_string_with_subscription(subscription_name)
        elif subscription_name == "pms": 
            return self.pms_connection_string()
        else:
            print("Invoking Connection String --------------")
            return self.connection_string(subscription_name)

    def get_expiring_connections(self, key: str) -> str:
        """Returns an expiring connection string if it hasn't expired, otherwise removes it."""
        try:
            subsname = key.lower().strip()
            
            with self._lock:  # Ensuring thread safety
                if key not in self._objcnc_dictionary_connection:
                    return ""

                expire_time = self.get_prop_value(self._objcnc_dictionary_connection[key], "Expire")

                if isinstance(expire_time, datetime):
                    diff = (datetime.now() - expire_time).total_seconds()
                    print(diff)

                    if diff > 0:
                        self._objcnc_dictionary_connection.pop(key, None)
                        return ""

                return str(self.get_prop_value(self._objcnc_dictionary_connection[key], "Value"))

        except Exception as e:
            return ""

    def is_db_encrypted(self, subscription_name: str) -> bool:
        """Checks if the database for a given subscription name is encrypted."""
        return False
    
    def connection_string(self, subscription_name: str) -> str:
        """Retrieves or generates a connection string for the given subscription name."""
        subscription_name = subscription_name.lower().strip()
        
        # Check if the connection string is already stored in the dictionary
        if subscription_name in self._objcnc_dictionary_connection:
            
            conn_str = self._objcnc_dictionary_connection[subscription_name]
            print("string found for hashmap:", conn_str)
            
            return self._objcnc_dictionary_connection[subscription_name]
        
        # Check if the database exists
        if self.check_db(subscription_name):
            
            print("Changing DB name")
            if subscription_name in ["pushnotification", "pms"]:
                str_con = self.base_connection_string(subscription_name).replace("x", subscription_name)
            else:
                str_con = self.base_connection_string(subscription_name).replace("ELCM_CommonCore", f"ELCM_{subscription_name}")
                print("Final String:", str_con)

            # Ensure thread safety when updating the dictionary
            # with self._lock:
            #     if subscription_name not in self._objcnc_dictionary_connection:
            #         try:
                        
            #             print("Adding in Hashmap")
                        
            #             self._objcnc_dictionary_connection[subscription_name] = str_con
            #             self.add_subscription_to_hash_table(subscription_name)
                        
            #             print("Added in Hashmap")
            #         except Exception as ex:
            #             print(f"Error adding connection string to dictionary: {ex}")

            print("Final String:", str_con)
            return str_con

        else:
            # If database doesn't exist, fetch connection string from the DB
            connection_string = self.get_connection_string_from_db(subscription_name)

            with self._lock:
                try:
                    self._objcnc_dictionary_connection[subscription_name] = connection_string
                    # self.add_subscription_to_hash_table(subscription_name)
                except Exception as ex:
                    print(f"Error adding connection string from DB: {ex}")

            return connection_string





