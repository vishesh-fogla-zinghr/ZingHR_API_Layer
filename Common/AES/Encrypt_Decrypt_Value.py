from abc import ABC, abstractmethod
from typing import Optional

class Encrypt_Decrypt_Value(ABC):
    """Interface defining database connection methods."""
    
    @abstractmethod
    def encrypt_js_value(self, ciphertext: str) -> str:
        pass
