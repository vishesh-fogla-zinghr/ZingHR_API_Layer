from abc import ABC, abstractmethod
from typing import Optional

class Encrypt_Decrypt_Value(ABC):
    """Interface defining database connection methods."""
    
    @abstractmethod
    def EncryptJSValue(self, ciphertext: str, EncryptionKey: str) -> str:
        pass
