from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class DbDetails(Base):
    __tablename__ = 'Info.DbDetails'
    
    id = Column(Integer, primary_key=True)
    subscription_name = Column(String(2000))
    server_address = Column(String(500))
    username = Column(String(100))
    password = Column(String(100))
    historical_server_address = Column(String(500))
    historical_username = Column(String(100))
    historical_password = Column(String(100))
    pms_db_id = Column(Integer, ForeignKey('Info.PMSDbDetails.id'))
    pms_details = relationship("PMSDbDetails")

class PMSDbDetails(Base):
    __tablename__ = 'Info.PMSDbDetails'
    
    id = Column(Integer, primary_key=True)
    server_address = Column(String(500))
    db_name = Column(String(100))
    username = Column(String(100))
    password = Column(String(100))

class AuthSoxDetails(Base):
    __tablename__ = 'AUTH_SOXDETAILS'
    
    sd_userid = Column(String(50), primary_key=True)
    sd_pwd1 = Column(String(100))
    sd_sm_statusid = Column(Integer)
    sd_failcount = Column(Integer, default=0)
    sd_timestamp = Column(DateTime)
    sd_init = Column(Integer)
    employee_master = relationship(
        "EmployeeMaster",
        primaryjoin="AuthSoxDetails.sd_userid == foreign(EmployeeMaster.employeecode)",
        uselist=False
    )

class LoginHistory(Base):
    __tablename__ = 'LoginHistory'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sessionid = Column(String(38))
    subscription = Column(String(20))
    userid = Column(String(50))
    login = Column(DateTime, default=datetime.utcnow)
    logout = Column(DateTime, nullable=True)
    type = Column(Integer)
    errordesc = Column(String(500))
    token = Column(String(38))
    ipaddress = Column(String(20))
    computername = Column(String(100))
    macaddress = Column(String(100))
    latitude = Column(DECIMAL(9,6), nullable=True)
    longitude = Column(DECIMAL(9,6), nullable=True)
    location = Column(String(250), nullable=True)
    signupid = Column(Integer)
    source = Column(String(20))
    appversion = Column(String(50))
    deviceid = Column(String(200))

class EmployeeScreenMapping(Base):
    __tablename__ = 'Authentication.EmployeeScreenMapping'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    employeecode = Column(String(50))
    pagename = Column(String(500))
    applicable = Column(Boolean, default=True)
    createdby = Column(String(50))
    createddate = Column(DateTime, default=datetime.utcnow)
    updatedby = Column(String(50), nullable=True)
    updateddate = Column(DateTime, nullable=True)
    isnewdirectory = Column(Boolean)
    alertmessage = Column(String(250))
    fromdate = Column(DateTime)
    todate = Column(DateTime)


class EmployeeMaster(Base):
    __tablename__ = 'EMPLOYEEMASTER'
    __table_args__ = {'schema': 'ED'}
    
    employeeid = Column(Integer, primary_key=True)
    employeecode = Column(String(50), unique=True)
    signupid = Column(Integer)
    usertype = Column(String(1), default='E')


class GeneralConfiguration(Base):
    __tablename__ = 'ess_genralconfiguration'
    
    keyname = Column(String(100), primary_key=True)
    value = Column(String(500)) 
    
class SysDatabase(Base):
    __tablename__ = 'sysdatabases'
    __table_args__ = {'schema': 'master.dbo'}
    
    name = Column('Name', String(128), primary_key=True) 