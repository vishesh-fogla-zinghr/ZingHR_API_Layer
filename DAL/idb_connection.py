from abc import ABC, abstractmethod
from typing import Optional
import pyodbc

class IDBConnection(ABC):
    """Interface defining database connection methods."""

    @abstractmethod
    def base_connection_string(self, subscription_name: str) -> str:
        pass
    
    @abstractmethod
    def add_subscription_to_hash_table(self, subscription_name: str):
        pass
    
    @abstractmethod
    def delete_hash_connection(self, subscription_name: str):
        pass
    
    @abstractmethod
    def dispose_connection(self, con: pyodbc.Connection):
        pass
    
    @abstractmethod
    def get_connection(self) -> str:
        pass
    
    @abstractmethod
    def get_connection(self, subscription_name: str, connectionType: str="") -> str:
        pass
    
    @abstractmethod
    def is_db_encrypted(self, subscription_name: str) -> bool:
        pass
