# zinghr_backend/app/Common/Persistence/dalv2.py
from typing import Optional
from DAL.dbconnection import DBConnection
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from typing import Optional, TypeVar, Type
from sqlalchemy.orm import Session

T = TypeVar('T')

class DAL:
    """Data Access Layer for retrieving SQL connections asynchronously."""
    
    def __init__(self, connection: DBConnection):
        """Initialize with DBConnection and IdentityService dependencies."""
        self._connection = connection
        # self._identity = identity


    async def get_connection(self, subscription_name: Optional[str] = None, connection_type: str = "") -> Engine:
        
        """
        Get a SQLAlchemy engine for the specified subscription.
        
        Args:
            subscription_name: Optional subscription name
            connection_type: Type of connection (e.g., "pms")
            
        Returns:
            SQLAlchemy Engine instance
        """
        
        
        print("Getting Connection ............")
        # Normalize subscription_name to lowercase or None
        subscription_name = subscription_name.lower() if subscription_name else None

        # Get the connection string from DBConnection
        if subscription_name is None:
            conn_string = self._connection.get_connection()  # Default connection without subscription
        else:
            conn_string = self._connection.get_connection(subscription_name, connection_type)

        # Create and open the connection asynchronously
        engine = create_engine(conn_string)
        return engine
        
        # Change database if no connection_type is specified (mimics C# behavior)
        # if not connection_type:
        #     db_name = self._connection_string(subscription_name, connection_type)
        #     await conn.execute(f"USE {db_name}")
        
        # return conn

    def _connection_string(self, subscription_name: Optional[str], connection_type: str) -> str:
        """
        Helper method to determine the database name (similar to ConnectionString in C#).
        
        Args:
            subscription_name: The subscription name.
            connection_type: The connection type.
        
        Returns:
            The database name to use.
        """
        # Logic to mimic C# ConnectionString behavior
        if subscription_name:
            if connection_type == "pms":
                return self._connection.pms_connection_string_with_subscription(subscription_name)
            elif subscription_name == "pms":
                return self._connection.pms_connection_string()
            else:
                return f"elcm_{subscription_name}"  # Default ELCM database naming
        return self._connection.base_connection_string("default")  # Fallback default
    
    async def get_data(self, 
                      query: str, 
                      model_class: Type[T], 
                      subscription_name: str = "", 
                      parameters: dict = None, 
                      timeout: int = 60, 
                      connection_type: str = "") -> Optional[T]:
        """
        Execute a query and return the first result mapped to the specified model.
        
        Args:
            query: The query or stored procedure name
            model_class: The Pydantic model class to map results to
            subscription_name: Optional subscription name
            parameters: Optional parameters for the query
            timeout: Query timeout in seconds
            connection_type: Type of connection
            
        Returns:
            Instance of model_class or None if no results
        """
        engine = await self.get_connection(subscription_name, connection_type)
        
        try:
            with Session(engine) as session:
                # Execute the query with parameters
                result = session.execute(
                    text(query),
                    parameters or {},
                    execution_options={"timeout": timeout}
                ).first()

                if result:
                    # Convert SQLAlchemy row to dict and create model instance
                    row_dict = dict(result._mapping)
                    return model_class(**row_dict)
                return None
                
        finally:
            engine.dispose()