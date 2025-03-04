# zinghr_backend/app/Common/Persistence/dalv2.py
from typing import Optional
import aioodbc
from DAL.dbconnection import DBConnection

class DAL:
    """Data Access Layer for retrieving SQL connections asynchronously."""
    
    def __init__(self, connection: DBConnection):
        """Initialize with DBConnection and IdentityService dependencies."""
        self._connection = connection
        # self._identity = identity

    async def get_connection(self, subscription_name: Optional[str] = None, connection_type: str = "") -> aioodbc.Connection:
        
        print("Getting Connection ............")
        # Normalize subscription_name to lowercase or None
        subscription_name = subscription_name.lower() if subscription_name else None

        # Get the connection string from DBConnection
        if subscription_name is None:
            conn_string = self._connection.get_connection()  # Default connection without subscription
        else:
            conn_string = self._connection.get_connection(subscription_name, connection_type)

        # Create and open the connection asynchronously
        conn = await aioodbc.connect(dsn=conn_string)
        
        # Change database if no connection_type is specified (mimics C# behavior)
        # if not connection_type:
        #     db_name = self._connection_string(subscription_name, connection_type)
        #     await conn.execute(f"USE {db_name}")
        
        return conn

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