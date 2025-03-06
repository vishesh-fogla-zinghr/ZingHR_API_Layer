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
    
    sd_userid = Column('SD_UserID', String(50), primary_key=True)
    sd_timestamp = Column('SD_TimeStamp', DateTime)
    sd_pwd1 = Column('SD_Pwd1', String(100))
    sd_pwd2 = Column('SD_Pwd2', String(100), nullable=True)
    sd_pwd3 = Column('SD_Pwd3', String(100), nullable=True)
    sd_pwd4 = Column('SD_Pwd4', String(100), nullable=True)
    sd_pwd5 = Column('SD_Pwd5', String(100), nullable=True)
    sd_init = Column('SD_Init', Integer)
    sd_failcount = Column('SD_FailCount', Integer, default=0)
    sd_sm_statusid = Column('SD_SM_StatusID', Integer)
    sd_activation = Column('SD_Activation', String(100), nullable=True)
    external_userid = Column('ExternalUserID', String(100), nullable=True)
    sd_verify_key = Column('SD_VerifyKey', String(100), nullable=True)
    sd_otp_mobile = Column('Sd_OtpMobile', String(10), nullable=True)
    sd_otp_email = Column('Sd_OtpEmail', String(100), nullable=True)
    azure_userid = Column('AzureUserID', String(100), nullable=True)
    gmail_userid = Column('GmailUserID', String(100), nullable=True)
    adfs_name = Column('ADFSName', String(100), nullable=True)
    ip_check_enabled = Column('IPCheckEnabled', Boolean, nullable=True)
    location_check_enabled = Column('LocationCheckEnabled', Boolean, nullable=True)
    ip_check_enabled_on_mobile = Column('IPCheckEnabledOnMobile', Boolean, nullable=True)
    reset_password_token = Column('ResetPasswordToken', String(100), nullable=True)
    is_sso_enabled = Column('IsSsoEnabled', Boolean, nullable=True)
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
    
    employeeid = Column('EmployeeID', Integer, primary_key=True)
    employeecode = Column('EmployeeCode', String(50), unique=True)
    signupid = Column('SignUpID', Integer)
    usertype = Column('UserType', String(1), default='E')
    employee_photo = Column('EmployeePhoto', String(500), nullable=True)
    salutation = Column('Salutation', String(10), nullable=True)
    first_name = Column('FirstName', String(100))
    middle_name = Column('MiddleName', String(100), nullable=True)
    last_name = Column('LastName', String(100))
    xero_emp_id = Column('XeroEmpId', String(50), nullable=True)
    keypay_empid = Column('KeypayEmpid', String(50), nullable=True)
    is_machine_learning = Column('IsMachineLearning', Boolean, nullable=True)
    party_id = Column('PartyId', Integer, nullable=True)
    is_policy = Column('ISPolicy', Boolean, nullable=True)
    ranking = Column('Ranking', Integer, nullable=True)
    created_date = Column('EMCreatedDate', DateTime, nullable=True)
    created_by = Column('EMCreatedBy', String(50), nullable=True)
    created_source = Column('CreatedSource', String(50), nullable=True)
    updated_date = Column('EMUpdatedDate', DateTime, nullable=True)
    updated_by = Column('EMUpdatedBy', String(50), nullable=True)
    updated_source = Column('UpdatedSource', String(50), nullable=True)
    session_id = Column('SessionId', String(38), nullable=True)
    token = Column('Token', String(38), nullable=True)
    ip_address = Column('IPAddress', String(50), nullable=True)
    latitude = Column('Latitude', DECIMAL(9,6), nullable=True)
    longitude = Column('Longitude', DECIMAL(9,6), nullable=True)
    updated_on = Column('UpdatedOn', DateTime, nullable=True)
    mac_address = Column('MacAddress', String(50), nullable=True)
    source = Column('Source', String(50), nullable=True)
    app_version = Column('AppVersion', String(50), nullable=True)
    device_id = Column('DeviceID', String(200), nullable=True)
    bank_joining_photo = Column('BankJoiningPhoto', String(500), nullable=True)
    
    roles = relationship('EmployeeRoleMapping', primaryjoin='EmployeeMaster.employeecode == foreign(EmployeeRoleMapping.employee_code)', backref='employee')
    personal_details = relationship('PersonalDetails', primaryjoin='EmployeeMaster.employeecode == foreign(PersonalDetails.employee_code)', uselist=False)
    personal_contact = relationship('PersonalContactDetails', primaryjoin='EmployeeMaster.employeecode == foreign(PersonalContactDetails.employee_code)', uselist=False)
    req_rec_details = relationship('ReqRecEmployeeDetails', primaryjoin='EmployeeMaster.employeecode == foreign(ReqRecEmployeeDetails.ed_empcode)', uselist=False)



class GeneralConfiguration(Base):
    __tablename__ = 'ess_genralconfiguration'
    
    keyname = Column(String(100), primary_key=True)
    value = Column(String(500)) 
    
class SysDatabase(Base):
    __tablename__ = 'sysdatabases'
    __table_args__ = {'schema': 'master.dbo'}
    
    name = Column('Name', String(128), primary_key=True) 
    
    
class EmployeeRoleMapping(Base):
    __tablename__ = 'EmployeeRoleMapping'
    __table_args__ = {'schema': 'SETUP'}

    id = Column(Integer, primary_key=True)
    employee_code = Column('EmployeeCode', String(50))
    role_id = Column('RoleID', Integer, ForeignKey('SETUP.RoleMaster.RoleID'))
    applicable = Column('Applicable', Boolean, default=True)
    
    role = relationship('RoleMaster', foreign_keys=[role_id])

class RoleMaster(Base):
    __tablename__ = 'RoleMaster'
    __table_args__ = {'schema': 'SETUP'}

    role_id = Column('RoleID', Integer, primary_key=True)
    role_description = Column('RoleDescription', String(100))
    applicable = Column('Applicable', Boolean, default=True)
    is_proxy = Column('IsProxy', Boolean, default=False)

class ReqRecEmployeeDetails(Base):
    __tablename__ = 'reqrec_employeedetails'
    __table_args__ = {'schema': 'dbo'}

    ed_empid = Column('ED_EMPID', Integer, primary_key=True)
    ed_empcode = Column('ED_EMPCode', String(50))
    ed_employee_photo = Column('ED_EmployeePhoto', String(500))
    ed_salutation = Column('ED_Salutation', String(10))
    ed_first_name = Column('ED_FirstName', String(100))
    ed_middle_name = Column('ED_MiddleName', String(100))
    ed_last_name = Column('ED_LastName', String(100))
    ed_sex = Column('ED_Sex', String(1))
    ed_email = Column('ED_Email', String(100))
    ed_mobile = Column('ED_Mobile', String(20))
    ed_working_telephone = Column('ED_WorkingTelephone', String(20))
    ed_present_address = Column('ED_PresentAddress', String(500))
    ed_dob = Column('ED_DOB', DateTime)
    ed_doj = Column('ED_DOJ', DateTime)

class ReqRecEmployeeFinDetails(Base):
    __tablename__ = 'ReqRec_EmployeeFinDetails'
    __table_args__ = {'schema': 'dbo'}

    efd_ed_empid = Column('EFD_ED_EmpID', Integer, 
                         ForeignKey('dbo.reqrec_employeedetails.ED_EMPID'),
                         primary_key=True)
    efd_reporting_manager = Column('EFD_ReportingManager', String(50))
    efd_date_of_marriage = Column('EFD_DateofMarriage', DateTime)

    employee = relationship('ReqRecEmployeeDetails', foreign_keys=[efd_ed_empid])

class PersonalDetails(Base):
    __tablename__ = 'PersonalDetails'
    __table_args__ = {'schema': 'ED'}

    id = Column(Integer, primary_key=True)
    employee_code = Column('EmployeeCode', String(50))
    blood_group_id = Column('BloodGroupID', Integer)
    cover_pic = Column('CoverPic', String(500))
    user_status = Column('UserStatus', String(50))

class PersonalContactDetails(Base):
    __tablename__ = 'PersonalContactDetails'
    __table_args__ = {'schema': 'ED'}

    id = Column(Integer, primary_key=True)
    employee_code = Column('EmployeeCode', String(50))
    personal_email = Column('PersonalEmail', String(100))
    alternate_mobile_no = Column('AlternateMobileNo', String(20))

class BloodGroupMaster(Base):
    __tablename__ = 'BloodGroupMaster'
    __table_args__ = {'schema': 'Common'}

    blood_group_id = Column('BloodGroupID', Integer, primary_key=True)
    code = Column('Code', String(10))