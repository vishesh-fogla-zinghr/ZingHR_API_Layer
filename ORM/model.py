from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, DECIMAL, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

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

class EmployeeMaster(Base):
    __tablename__ = 'EMPLOYEEMASTER'
    __table_args__ = {'schema': 'ED'}
    
    employeeid = Column(Integer, primary_key=True)
    employeecode = Column(String(50), unique=True)
    signupid = Column(BigInteger)
    usertype = Column(String(1), default='E')

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
    signupid = Column(BigInteger)
    source = Column(String(20))
    appversion = Column(String(50))
    deviceid = Column(String(200))

class EmployeeScreenMapping(Base):
    __tablename__ = 'EmployeeScreenMapping'
    __table_args__ = {'schema': 'Authentication'}
    
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

class GeneralConfiguration(Base):
    __tablename__ = 'ess_genralconfiguration'
    
    keyname = Column(String(100), primary_key=True)
    value = Column(String(500))

# ORM/model.py (partial update)

class ReqRecEmployeeDetails(Base):
    __tablename__ = 'reqrec_employeedetails'
    
    ed_empid = Column(Integer, primary_key=True)
    ed_empcode = Column(String(50), unique=True)
    ed_employee_photo = Column("ED_EmployeePhoto", String(500))  # Match DB column name
    ed_salutation = Column("ED_Salutation", String(50))
    ed_firstname = Column("ED_FirstName", String(100))
    ed_middlename = Column("ED_MiddleName", String(100))
    ed_lastname = Column("ED_LastName", String(100))
    ed_sex = Column("ED_Sex", String(50))
    ed_email = Column("ED_Email", String(100))
    ed_mobile = Column("ED_Mobile", String(50))
    ed_workingtelephone = Column("ED_WorkingTelephone", String(50))
    ed_presentaddress = Column("ED_PresentAddress", Text)
    ed_dob = Column("ED_DOB", DateTime)
    ed_doj = Column("ED_DOJ", DateTime)
    ed_dol = Column("ED_DOL", DateTime)
    ed_status = Column("ED_Status", String(50))

class ReqRecEmployeeFinDetails(Base):
    __tablename__ = 'reqrec_employeefindetails'
    
    efd_ed_empid = Column("EFD_ED_EmpID", Integer, ForeignKey('reqrec_employeedetails.ed_empid'), primary_key=True)  # Match DB, no efd_id
    efd_dateofmarriage = Column("EFD_DateofMarriage", DateTime)
    efd_reportingmanager = Column("EFD_ReportingManager", String(50))
    employee_details = relationship("ReqRecEmployeeDetails", backref="fin_details")

class PersonalDetails(Base):
    __tablename__ = 'PersonalDetails'
    __table_args__ = {'schema': 'ED'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    employeecode = Column(String(50), ForeignKey('ED.EMPLOYEEMASTER.employeecode'))
    bloodgroupid = Column(Integer)
    coverpic = Column(String(500))
    userstatus = Column(String(50))

class PersonalContactDetails(Base):
    __tablename__ = 'PersonalContactDetails'
    __table_args__ = {'schema': 'ED'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    employeecode = Column(String(50), ForeignKey('ED.EMPLOYEEMASTER.employeecode'))
    personalemail = Column(String(100))
    alternatemobileno = Column(String(50))

class RoleMaster(Base):
    __tablename__ = 'RoleMaster'
    __table_args__ = {'schema': 'SETUP'}
    
    roleid = Column(BigInteger, primary_key=True)
    rolecode = Column(String(50))
    roledescription = Column(String(500))
    isproxy = Column(Boolean)
    applicable = Column(Boolean, default=True)

class EmployeeRoleMapping(Base):
    __tablename__ = 'EmployeeRoleMapping'
    __table_args__ = {'schema': 'SETUP'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    signupid = Column(BigInteger)
    roleid = Column(BigInteger, ForeignKey('SETUP.RoleMaster.roleid'))
    employeecode = Column(String(50), ForeignKey('ED.EMPLOYEEMASTER.employeecode'))
    createddate = Column(DateTime, default=datetime.utcnow)
    createdby = Column(String(50))
    applicable = Column(Boolean, default=True)
    role = relationship("RoleMaster")
    employee = relationship("EmployeeMaster")

class LastSuccessfulLogin(Base):
    __tablename__ = 'LastSuccessfulLogin'
    __table_args__ = {'schema': 'Authentication'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(String(50), ForeignKey('ED.EMPLOYEEMASTER.employeecode'))
    logintime = Column(DateTime, default=datetime.utcnow)
    employee = relationship("EmployeeMaster")

class BloodGroupMaster(Base):
    __tablename__ = 'BloodGroupMaster'
    __table_args__ = {'schema': 'Common'}
    
    bloodgroupid = Column(Integer, primary_key=True)
    code = Column(String(50))

class ClientTNaConfig(Base):
    __tablename__ = 'ClientTNaConfig'
    __table_args__ = {'schema': 'TNA'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50))
    title = Column(String(100))
    value = Column(String(50))

class LoginDisabled(Base):
    __tablename__ = 'LoginDisabled'
    __table_args__ = {'schema': 'Authentication'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    empcode = Column(String(50), ForeignKey('ED.EMPLOYEEMASTER.employeecode'))
    lastlogindisableddate = Column(DateTime)
    employee = relationship("EmployeeMaster")

class EmploymentDetails(Base):
    __tablename__ = 'EmploymentDetails'
    __table_args__ = {'schema': 'ED'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    employeecode = Column(String(50), ForeignKey('ED.EMPLOYEEMASTER.employeecode'))
    reportingmanagercode = Column(String(50))
    employeestatus = Column(Integer)
    employee = relationship("EmployeeMaster")