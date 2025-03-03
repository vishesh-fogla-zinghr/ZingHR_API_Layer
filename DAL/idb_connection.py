from abc import ABC, abstractmethod
from typing import Optional
import pyodbc

class IDBConnection(ABC):
    """Interface defining database connection methods."""
    
    @abstractmethod
    async def delete_hash_connection(self, subscription_name: str) -> None:
        pass
    
    @abstractmethod
    async def dispose_connection(self, con: pyodbc.Connection) -> None:
        pass
    
    # @abstractmethod
    # def get_connection(self) -> str:
    #     pass
    
    # @abstractmethod
    # def get_connection(self, subscription_name: str, connectionType: str="") -> str:
    #     pass
    
    @abstractmethod
    def is_db_encrypted(self, subscription_name: str) -> bool:
        pass
