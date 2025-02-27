from datetime import datetime
from typing import Optional, Any

class CachedDetail:
    def __init__(self):
        self.last_cached_at: Optional[datetime] = None
        self.cached_till: Optional[datetime] = None

class ResponseModel(CachedDetail):
    def __init__(self, code: int = 0, data: Any = None, message: str = "Success"):
        super().__init__()  
        self.code: int = code
        self.data: Any = data
        self.message: str = message