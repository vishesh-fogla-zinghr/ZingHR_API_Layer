import math
import ipaddress
import json
from datetime import datetime, timedelta
import asyncio

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, field_validator
from typing import Optional, Any, Dict, List, Tuple
import logging
import uvicorn
from urllib.parse import quote_plus
import urllib

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.engine import Engine
#from ZingHR_API_Layer.punchin.models import FlatTable,SwipeData,PunchInLocation,Base
# ---------------------------------------------------------
# ORM Models
# ---------------------------------------------------------
Base = declarative_base()

class FlatTable(Base):
    __tablename__ = "FlatTable"
    EmpCode = Column(String(50), primary_key=True)
    ShiftDetails = Column(Text, nullable=True)      # JSON string with shift details
    LocationDetails = Column(Text, nullable=True)     # JSON string with location records
    IPRange = Column(Text, nullable=True)             # JSON string with allowed IP ranges
    IPCheckEnabled = Column(String(5), nullable=True)   # e.g., 'true'/'false'

class SwipeData(Base):
    __tablename__ = "SwipeData"
    id = Column(Integer, primary_key=True, autoincrement=True)
    AttMode = Column(String(10), nullable=True)
    EmpIdentification = Column(String(50), nullable=True)
    TermNo = Column(String(20), nullable=True)
    SwipeDate = Column(DateTime, nullable=True)
    TimeZone = Column(Integer, nullable=True)
    Createdon = Column(DateTime, nullable=True)
    CreatedBy = Column(String(50), nullable=True)
    UpdatedOn = Column(DateTime, nullable=True)
    UpdatedBy = Column(String(50), nullable=True)
    IpAddress = Column(String(50), nullable=True)
    Source = Column(String(50), nullable=True)

class PunchInLocation(Base):
    __tablename__ = "PunchInLocation"
    id = Column(Integer, primary_key=True, autoincrement=True)
    EMPIDENTIFICATION = Column(String(50), nullable=True)
    SWIPEDATE = Column(DateTime, nullable=True)
    IPADDRESS = Column(String(50), nullable=True)
    PUNCHINOUTACTION = Column(String(20), nullable=True)
    USERID = Column(String(50), nullable=True)
    Latitude = Column(Float, nullable=True)
    Longitude = Column(Float, nullable=True)
    Source = Column(String(50), nullable=True)

# ---------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------
logger = logging.getLogger("PunchInAPI")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# ---------------------------------------------------------
# Database Configuration and ORM Setup
# ---------------------------------------------------------
encoded_password = urllib.parse.quote_plus("Cner@321")
DATABASE_URL = f"mssql+pyodbc://testadmin:{encoded_password}@172.16.68.4/ELCM_ZINGQADB?driver=ODBC+Driver+17+for+SQL+Server"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------
# Pydantic Models for Request/Response
# ---------------------------------------------------------
class ValidateEmployeePunchCommand(BaseModel):
    EmpCode: str
    PunchDateTime: Optional[datetime] = None
    Latitude: float
    Longitude: float
    ClientIPAddress: Optional[str] = None
    Source: str = "Mobile"
    AttMode: int = 1
    Type: str  # "PUNCHIN" or "PUNCHOUT"

    @field_validator("Type")
    def validate_type(cls, v):
        if v.upper() not in ["PUNCHIN", "PUNCHOUT"]:
            raise ValueError("Type must be 'PUNCHIN' or 'PUNCHOUT'")
        return v.upper()

class ValidateGeoFencingCommand(BaseModel):
    USERID: str
    LATITUDE: float
    LONGITUDE: float
    IPADDRESS: Optional[str] = None
    PUNCHIN: bool
    PUNCHOUT: bool
    LOGIN: bool = False

class ResponseModel(BaseModel):
    Code: int
    Message: str
    Data: Optional[Any] = None

# ---------------------------------------------------------
# Hard-coded Config for Geo & IP Validation (fallback defaults)
# ---------------------------------------------------------
ALLOWED_CENTER_LAT = 19.533572
ALLOWED_CENTER_LON = 78.877306
ALLOWED_RADIUS_METERS = 1000.0  # Fallback value (if no flat record available)

DEFAULT_IP_RANGES: List[Tuple[str, str]] = [
    ("192.168.1.1", "192.168.1.255"),
]

# ---------------------------------------------------------
# Helper Functions for Timezone, Employee & Shift Details
# ---------------------------------------------------------
def get_timezone_offset(emp_code: str) -> int:
    return 0

def get_country_code(emp_code: str) -> str:
    return "IN"

def get_employee_identification(emp_code: str, db: Session) -> Optional[str]:
    flat = db.query(FlatTable).filter(FlatTable.EmpCode == emp_code).first()
    if flat:
        return flat.EmpCode
    return None

def get_flat_shift_details(emp_code: str, db: Session) -> dict:
    flat = db.query(FlatTable).filter(FlatTable.EmpCode == emp_code).first()
    if not flat or not flat.ShiftDetails:
        raise ValueError("No shift details found in FlatTable.")
    try:
        data = json.loads(flat.ShiftDetails)
    except Exception as e:
        raise ValueError(f"Error parsing ShiftDetails JSON: {e}")
    if not isinstance(data, list) or len(data) == 0:
        raise ValueError("ShiftDetails JSON is empty or not a list.")
    record = data[0]
    if "ShiftDetails" not in record:
        raise KeyError("Missing 'ShiftDetails' key in ShiftDetails JSON")
    details = record["ShiftDetails"]
    required_keys = ["InTime", "OutTime", "PreTime", "PostTime", "ShiftRanges"]
    for key in required_keys:
        if key not in details:
            raise KeyError(f"Missing '{key}' key in ShiftDetails JSON")
    if not isinstance(details["ShiftRanges"], list) or len(details["ShiftRanges"]) == 0:
        raise ValueError("No shift ranges found in ShiftDetails JSON")
    range0 = details["ShiftRanges"][0]
    if "RangeStart" not in range0 or "RangeEnd" not in range0:
        raise KeyError("Missing 'RangeStart' or 'RangeEnd' in ShiftRanges")
    return {
        "InTime": details["InTime"],
        "OutTime": details["OutTime"],
        "PreTime": int(details["PreTime"]),
        "PostTime": int(details["PostTime"]),
        "RangeStart": range0["RangeStart"],
        "RangeEnd": range0["RangeEnd"]
    }

def get_flat_location_details(emp_code: str, db: Session) -> Optional[Dict[str, Any]]:
    flat = db.query(FlatTable).filter(FlatTable.EmpCode == emp_code).first()
    if not flat or not flat.LocationDetails:
        return None
    try:
        data = json.loads(flat.LocationDetails)
    except Exception as e:
        logger.error(f"Error parsing LocationDetails JSON for {emp_code}: {e}")
        return None
    if not isinstance(data, list) or len(data) == 0:
        return None
    now = datetime.now()
    for rec in data:
        try:
            from_date = datetime.fromisoformat(rec.get("FromDate"))
            to_date = datetime.fromisoformat(rec.get("ToDate"))
            if from_date <= now <= to_date:
                return rec
        except Exception as e:
            logger.error(f"Error processing location record for {emp_code}: {e}")
    return None

def get_allowed_ip_ranges(emp_code: str, db: Session) -> List[Tuple[str, str]]:
    allowed = []
    flat = db.query(FlatTable).filter(FlatTable.EmpCode == emp_code).first()
    if flat and flat.IPRange:
        try:
            ip_data = json.loads(flat.IPRange)
            if isinstance(ip_data, list):
                for rec in ip_data:
                    ip_from = rec.get("IPFrom")
                    ip_to = rec.get("IPTo")
                    if ip_from and ip_to:
                        allowed.append((ip_from.strip(), ip_to.strip()))
        except Exception as e:
            logger.error(f"Error parsing IPRange from FlatTable for {emp_code}: {e}")
    if not allowed:
        allowed = DEFAULT_IP_RANGES
    return allowed

# ---------------------------------------------------------
# Utility Functions for Distance and IP Validation
# ---------------------------------------------------------
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def validate_location_from_flat(lat: float, lon: float, location_details: Dict[str, Any]) -> (bool, str):
    try:
        allowed_lat = float(location_details.get("Latitude"))
        allowed_lon = float(location_details.get("Longitude"))
        georange = float(location_details.get("georange"))
        rangeinkm = int(location_details.get("rangeinkm"))
        allowed_range = georange * (1000 if rangeinkm == 1 else 1)
    except Exception as e:
        return False, f"Error parsing location details: {e}"
    dist = haversine_distance(lat, lon, allowed_lat, allowed_lon)
    if dist <= allowed_range:
        return True, f"Within allowed distance ({dist:.2f} m <= {allowed_range} m)."
    return False, f"Out of allowed distance ({dist:.2f} m > {allowed_range} m)."

def validate_ip(client_ip: str, allowed_ranges: List[Tuple[str, str]]) -> (bool, str):
    try:
        ip_addr = ipaddress.ip_address(client_ip)
    except ValueError:
        return False, "Invalid IP format."
    for start_ip, end_ip in allowed_ranges:
        if ipaddress.ip_address(start_ip) <= ip_addr <= ipaddress.ip_address(end_ip):
            return True, f"IP {client_ip} is within allowed range."
    return False, f"IP {client_ip} is not within allowed ranges."

# ---------------------------------------------------------
# DAL: Stored Procedure Caller via SQLAlchemy (if needed)
# ---------------------------------------------------------
class DAL:
    def __init__(self, engine: Engine):
        self.engine = engine

    async def get_data(self, sp_name: str, parameters: Dict[str, Any],
                       commandType: str, subscriptionName: str = "") -> Optional[Dict[str, Any]]:
        new_params = {
            (key[1:] if key.startswith("@") else key): (int(value) if isinstance(value, bool) else value)
            for key, value in parameters.items()
        }
        named_params = ", ".join([f"@{key}=:{key}" for key in new_params.keys()])
        sql = f"EXEC {sp_name} {named_params}"
        logger.info(f"Executing SP: {sql} with parameters: {new_params}")

        def execute_sp():
            try:
                with self.engine.connect() as connection:
                    stmt = text(sql)
                    result = connection.execute(stmt, new_params)
                    row = result.fetchone()
                    if row is None:
                        return None
                    keys = result.keys()
                    return dict(zip(keys, row))
            except Exception as e:
                logger.error(f"Database connection error: {e}")
                raise

        try:
            return await asyncio.to_thread(execute_sp)
        except Exception as e:
            logger.error(f"DAL.get_data error: {e}")
            return None

dal = DAL(engine)

# ---------------------------------------------------------
# (Optional) Mediator Function for Geo Validation using SP
# ---------------------------------------------------------
async def send_validate_geofencing_command(command: ValidateGeoFencingCommand) -> ResponseModel:
    if not command.IPADDRESS:
        command.IPADDRESS = "127.0.0.1"
    query_params = {
        "@USERID": command.USERID,
        "@LATITUDE": command.LATITUDE,
        "@LONGITUDE": command.LONGITUDE,
        "@IPADDRESS": command.IPADDRESS,
        "@PUNCHIN": command.PUNCHIN,
        "@PUNCHOUT": command.PUNCHOUT,
        "@LOGIN": command.LOGIN
    }
    response = await dal.get_data("[Authentication].[VerifyGeoLocation]", query_params, "StoredProcedure", "")
    if response is None:
        return ResponseModel(Code=0, Message="Database connection error during geo validation.")
    return ResponseModel(
        Code=int(response.get("Code", 0)),
        Message=response.get("MSG", "No message returned"),
        Data=response
    )

# ---------------------------------------------------------
# Business Logic: Punch Processing Using FlatTable Data
# ---------------------------------------------------------
async def process_punch(db: Session, cmd: ValidateEmployeePunchCommand) -> dict:
    punch_type = cmd.Type.upper()
    if punch_type not in ["PUNCHIN", "PUNCHOUT"]:
        return {"IsValidPunch": 0, "Message": "Invalid punch type."}

    tz_offset = get_timezone_offset(cmd.EmpCode)
    country_code = get_country_code(cmd.EmpCode)
    punch_dt = (cmd.PunchDateTime or datetime.now()) + timedelta(minutes=tz_offset)

    emp_id = get_employee_identification(cmd.EmpCode, db)
    if not emp_id:
        return {"IsValidPunch": 0, "Message": f"Employee {cmd.EmpCode} not found in FlatTable."}

    try:
        shift_data = get_flat_shift_details(cmd.EmpCode, db)
    except Exception as e:
        return {"IsValidPunch": 0, "Message": f"Error parsing shift details: {e}"}

    try:
        in_time_str = shift_data.get("InTime")
        out_time_str = shift_data.get("OutTime")
        pre_time = int(shift_data.get("PreTime", 0))
        post_time = int(shift_data.get("PostTime", 0))
        if not in_time_str or not out_time_str:
            return {"IsValidPunch": 0, "Message": "Shift timings missing in FlatTable."}
        in_time = datetime.fromisoformat(in_time_str).time()
        out_time = datetime.fromisoformat(out_time_str).time()
    except Exception as e:
        return {"IsValidPunch": 0, "Message": f"Error parsing shift time details: {e}"}

    shift_date = punch_dt.date()
    shift_in = datetime.combine(shift_date, in_time) - timedelta(minutes=pre_time)
    shift_out = datetime.combine(shift_date, out_time) + timedelta(minutes=post_time)
    term_no = "Punch IN" if punch_type == "PUNCHIN" else "Punch Out"

    if not (shift_in <= punch_dt <= shift_out):
        return {"IsValidPunch": 0, "Message": f"{punch_type} not allowed outside shift window: {shift_in} to {shift_out}."}

    if punch_type == "PUNCHIN":
        existing = db.query(SwipeData).filter(
            SwipeData.EmpIdentification == emp_id,
            SwipeData.TermNo == "Punch IN",
            SwipeData.SwipeDate.between(shift_in, shift_out)
        ).first()
        if existing:
            return {"IsValidPunch": 0, "Message": "Punch-IN already recorded in this shift window."}
    else:
        existing_in = db.query(SwipeData).filter(
            SwipeData.EmpIdentification == emp_id,
            SwipeData.TermNo == "Punch IN",
            SwipeData.SwipeDate.between(shift_in, shift_out)
        ).first()
        if not existing_in:
            return {"IsValidPunch": 0, "Message": "Cannot punch-out without a punch-in in this shift window."}

    is_valid_punch = 1

    # Retrieve allowed location details from FlatTable (LocationDetails JSON)
    loc_record = get_flat_location_details(cmd.EmpCode, db)
    if loc_record:
        try:
            loc_ok, loc_msg = validate_location_from_flat(cmd.Latitude, cmd.Longitude, loc_record)
        except Exception as e:
            loc_ok = False
            loc_msg = f"Error validating location from flat data: {e}"
    else:
        return {"IsValidPunch": 0, "Message": "No valid location configuration found in FlatTable."}

    if not loc_ok:
        return {"IsValidPunch": 0, "Message": f"Geolocation validation failed: {loc_msg}"}
    is_valid_location = 1

    # Retrieve allowed IP ranges from FlatTable (IPRange JSON)
    try:
        allowed_ip_ranges = get_allowed_ip_ranges(cmd.EmpCode, db)
    except Exception as e:
        logger.error(f"Error retrieving IP ranges: {e}")
        allowed_ip_ranges = DEFAULT_IP_RANGES

    client_ip = cmd.ClientIPAddress or "127.0.0.1"
    ip_ok, ip_msg = validate_ip(client_ip, allowed_ip_ranges)
    if not ip_ok:
        return {"IsValidPunch": 0, "Message": f"IP validation failed: {ip_msg}"}
    is_valid_ip = 1

  
    try:
        swipe = SwipeData(
            AttMode=str(cmd.AttMode),
            EmpIdentification=emp_id,
            TermNo=term_no,
            SwipeDate=punch_dt,
            TimeZone=tz_offset,
            Createdon=datetime.now(),
            CreatedBy=cmd.EmpCode,
            UpdatedOn=datetime.now(),
            UpdatedBy=(term_no + "-" + country_code) if country_code else term_no,
            IpAddress=client_ip,
            Source=cmd.Source
        )
        db.add(swipe)
        punch_loc = PunchInLocation(
            EMPIDENTIFICATION=emp_id,
            SWIPEDATE=punch_dt,
            IPADDRESS=client_ip,
            PUNCHINOUTACTION=term_no.upper(),
            USERID=cmd.EmpCode,
            Latitude=cmd.Latitude,
            Longitude=cmd.Longitude,
            Source=cmd.Source
        )
        db.add(punch_loc)
        db.commit()
        db.refresh(swipe)
        db.refresh(punch_loc)
        message = f"{term_no} successful at {punch_dt}. {ip_msg} {loc_msg}"
    except Exception as e:
        db.rollback()
        return {"IsValidPunch": 0, "Message": f"Error inserting punch record: {e}"}

    return {
        "IsValidPunch": is_valid_punch,
        "IsValidLocation": is_valid_location,
        "IsValidIP": is_valid_ip,
        "Message": message
    }

# ---------------------------------------------------------
# FastAPI Application & Endpoint
# ---------------------------------------------------------
app = FastAPI(title="Punch-In/Out API using FlatTable Data")

@app.post("/punchin", response_model=ResponseModel)
async def punchin_endpoint(cmd: ValidateEmployeePunchCommand, db: Session = Depends(get_db)):
    if not cmd.PunchDateTime:
        cmd.PunchDateTime = datetime.now()
    if not cmd.ClientIPAddress:
        cmd.ClientIPAddress = "127.0.0.1"
    result = await process_punch(db, cmd)
    code = 1 if result.get("IsValidPunch") == 1 else 0
    return ResponseModel(Code=code, Message=result["Message"], Data=result)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8060, reload=True)
