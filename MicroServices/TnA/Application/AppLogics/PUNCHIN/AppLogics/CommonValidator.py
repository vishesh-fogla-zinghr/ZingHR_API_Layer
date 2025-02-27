from typing import Optional, List

class CommonSchema:
    SyncValues: List[str] = []

    @staticmethod
    def check_lat_long(value: Optional[float]) -> bool:
        if value is None:
            return False
        l = str(abs(value))
        
        if l and ("." in l and l.index(".") > 3):
            return False
        
        return True

    @staticmethod
    def is_sync_val_exists(sync_val: str) -> bool:
        if len(CommonSchema.SyncValues) > 10000:
            CommonSchema.SyncValues.clear()
        
        if any(sync_val in x for x in CommonSchema.SyncValues):
            return True
        
        CommonSchema.SyncValues.append(sync_val)
        return False
