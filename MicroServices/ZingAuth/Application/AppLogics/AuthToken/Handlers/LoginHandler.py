import uuid
from pydantic import BaseModel
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.LoginCommand import LoginCommand
from MicroServices.ZingAuth.Application.Integration.Models.WorkFlowGroupDetails import ResponseModel
from DAL.dal import DAL
from Common.AES.EncryptDecryptValue import EncryptDecryptValue
from fastapi import Depends
from datetime import datetime, timedelta
from sqlalchemy import text, and_, or_, func
from sqlalchemy.orm import Session, joinedload
from ORM.model import (
    AuthSoxDetails,
    LoginHistory,
    EmployeeScreenMapping,
    GeneralConfiguration,
    EmployeeMaster,
    ReqRecEmployeeDetails,
    ReqRecEmployeeFinDetails,
    PersonalDetails,
    PersonalContactDetails,
    RoleMaster,
    EmployeeRoleMapping,
    LastSuccessfulLogin,
    BloodGroupMaster,
    ClientTNaConfig,
    LoginDisabled,
    EmploymentDetails
)
import asyncio
import json

class QueryParameters(BaseModel):
    DatabaseName: str
    EmpCode: str
    Password: str
    Token: str

class LoginHandler:
    """Handler for processing login command replicating CombinedLoginAndEmployeeInfo SP"""
    
    def __init__(self, _connection: DAL, encryptor: EncryptDecryptValue):
        self.db_connection = _connection
        self.encryptor = encryptor

    async def handle(self, request: LoginCommand):
        try:
            engine = await self.db_connection.get_connection(request.subscription_name)
            if engine is None:
                return ResponseModel(code=-1, message="Database engine not initialized")
            session = Session(bind=engine)

            try:
                session.execute(text("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED"))

                token = str(uuid.uuid4())
                session_id = request.session_id or str(uuid.uuid4())
                encrypted_password = self.encryptor.encrypt_js_value(str(request.password))

                is_valid_case = False
                user_status = None
                fail_count = 0
                error_message = ""
                signup_id = request.signup_id
                previous_login_date = None
                pwd_exp_days = None
                pwd_expire = False
                landing_page = None
                is_new_directory = None
                alert_message = None

                config_values = (
                    session.query(GeneralConfiguration)
                    .filter(
                        GeneralConfiguration.keyname.in_([
                            'PASSWORDEXPIRYINDAYS', 'MultipleLoginEnableToUser',
                            'DefaultAfterLoginPage', 'ExitEmpLogin', 'LoginExpiryInDays',
                            'DefaultGuestLoginPage', 'SwitchUserSetting',
                            'IsOrganogramEmployeeApplicable', 'SetupNewUx'
                        ])
                    )
                    .all()
                )
                config_dict = {config.keyname: config.value for config in config_values}

                if signup_id is None:
                    signup_id_query = (
                        session.query(EmployeeMaster.signupid)
                        .order_by(EmployeeMaster.employeeid.asc())
                        .limit(1)
                    )
                    signup_id_result = signup_id_query.first()
                    signup_id = signup_id_result[0] if signup_id_result else None
                    if signup_id_query.count() > 1:
                        print(f"Warning: Multiple signup_ids found; using first one: {signup_id}")

                pwd_exp_days = int(config_dict.get('PASSWORDEXPIRYINDAYS', 0))
                exit_emp_login = int(config_dict.get('ExitEmpLogin', 0))

                auth_query = (
                    session.query(
                        AuthSoxDetails,
                        ReqRecEmployeeDetails.ed_dol.label("dol"),
                        ReqRecEmployeeDetails.ed_status.label("status"),
                        EmployeeMaster.employeeid.label("emp_id")
                    )
                    .select_from(AuthSoxDetails)
                    .join(
                        ReqRecEmployeeDetails,
                        AuthSoxDetails.sd_userid == ReqRecEmployeeDetails.ed_empcode
                    )
                    .join(
                        EmployeeMaster,
                        AuthSoxDetails.sd_userid == EmployeeMaster.employeecode
                    )
                    .filter(
                        AuthSoxDetails.sd_userid == request.emp_code,
                        EmployeeMaster.usertype == (request.user_type or 'E')
                    )
                )

                if request.proxy_creator or request.proxy_emp_code:
                    auth_query = auth_query.filter(
                        AuthSoxDetails.sd_userid == (
                            request.proxy_emp_code if request.proxy_creator else request.emp_code
                        )
                    )
                elif request.emp_code == 'ADMIN':
                    pass
                else:
                    auth_query = auth_query.filter(
                        or_(
                            request.source == 'SSO',
                            AuthSoxDetails.sd_sm_statusid == 1,
                            and_(AuthSoxDetails.sd_sm_statusid == 1, exit_emp_login == 1)
                        )
                    )

                auth_result = auth_query.limit(1).first()
                if auth_query.count() > 1:
                    print(f"Warning: Multiple auth rows for emp_code {request.emp_code}; using first one")

                if auth_result:
                    auth_details, dol, status, emp_id = auth_result
                    is_valid_case = auth_details.sd_pwd1 == encrypted_password
                    previous_cp_date = auth_details.sd_timestamp if auth_details.sd_timestamp else datetime.utcnow()

                    login_disabled_config = (
                        session.query(ClientTNaConfig.value)
                        .filter(
                            ClientTNaConfig.type == 'ELC',
                            ClientTNaConfig.title == 'LoginDisabledbasedonShift'
                        )
                        .scalar() or '0'
                    )
                    if login_disabled_config == '1':
                        dol_query = (
                            session.query(LoginDisabled.lastlogindisableddate)
                            .filter(LoginDisabled.empcode == request.emp_code)
                            .order_by(LoginDisabled.id.desc())
                            .limit(1)
                        )
                        dol = dol_query.scalar()
                        if dol_query.count() > 1:
                            print(f"Warning: Multiple LoginDisabled rows for emp_code {request.emp_code}")

                    if (
                        dol and dol > datetime(1900, 1, 1) and
                        datetime.utcnow().date() > dol.date() and
                        request.emp_code != 'C001' and
                        not request.proxy_emp_code and not request.proxy_creator
                    ):
                        if exit_emp_login == 0:
                            auth_details.sd_sm_statusid = 3
                            session.commit()
                            error_message = "Login expired for exit employee"
                        else:
                            auth_details.sd_sm_statusid = 1
                            is_exit_employee = True
                            exit_role = (
                                session.query(RoleMaster.roleid)
                                .filter(RoleMaster.rolecode == 'EXITEMP')
                                .scalar()
                            )
                            if not session.query(EmployeeRoleMapping).filter(
                                EmployeeRoleMapping.roleid == exit_role,
                                EmployeeRoleMapping.employeecode == request.emp_code
                            ).first():
                                session.query(EmployeeRoleMapping).filter(
                                    EmployeeRoleMapping.employeecode == request.emp_code
                                ).update({"applicable": False})
                                session.add(EmployeeRoleMapping(
                                    signupid=signup_id,
                                    roleid=exit_role,
                                    employeecode=request.emp_code,
                                    createdby="System",
                                    applicable=True
                                ))
                            session.commit()

                else:
                    auth_details = None

                if not is_valid_case:
                    fail_count = auth_details.sd_failcount or 0 if auth_result else 0
                    if fail_count >= 4:
                        if auth_details:
                            auth_details.sd_sm_statusid = 2
                            auth_details.sd_failcount = fail_count + 1
                        error_message = "Account locked due to multiple failed attempts"
                    else:
                        if auth_details:
                            auth_details.sd_failcount = fail_count + 1
                        error_message = (
                            "Login failed due to: Invalid credentials OR Invalid employee status OR "
                            "Login expired OR Login locked OR Login disabled. "
                            "For your safety, your access to ZingHR will be disabled after 5 consecutive wrong entries."
                        )
                    session.add(LoginHistory(
                        sessionid=session_id,
                        subscription=request.subscription_name,
                        userid=request.emp_code,
                        type=0,
                        errordesc=error_message,
                        token=token,
                        ipaddress=request.ip_address,
                        computername=request.computer_name,
                        macaddress=request.mac_address,
                        latitude=request.latitude,
                        longitude=request.longitude,
                        location=request.location,
                        signupid=signup_id,
                        source=request.source,
                        appversion=request.app_version,
                        deviceid=request.device_id
                    ))
                    session.commit()
                    return ResponseModel(code=0, message=error_message)

                last_login_query = (
                    session.query(LastSuccessfulLogin.logintime)
                    .filter(LastSuccessfulLogin.userid == request.emp_code)
                    .order_by(LastSuccessfulLogin.logintime.desc())
                    .limit(1)
                )
                last_login = last_login_query.scalar()
                if last_login_query.count() > 1:
                    print(f"Warning: Multiple LastSuccessfulLogin rows for emp_code {request.emp_code}")

                if not last_login:
                    previous_login_date_query = (
                        session.query(LoginHistory.login)
                        .filter(
                            LoginHistory.userid == request.emp_code,
                            LoginHistory.subscription == request.subscription_name,
                            LoginHistory.type == 1,
                            LoginHistory.errordesc == 'SUCCESS'
                        )
                        .order_by(LoginHistory.login.desc())
                        .limit(1)
                    )
                    previous_login_date = previous_login_date_query.scalar()
                    session.add(LastSuccessfulLogin(userid=request.emp_code, logintime=datetime.utcnow()))
                    if previous_login_date_query.count() > 1:
                        print(f"Warning: Multiple LoginHistory rows for emp_code {request.emp_code}")
                else:
                    previous_login_date = last_login

                days_since_login = (datetime.utcnow() - previous_login_date).days if previous_login_date else 0
                days_since_pwd_change = (datetime.utcnow() - previous_cp_date).days if previous_cp_date else 0

                if (
                    request.source != 'SSO' and
                    days_since_login > int(config_dict.get('LoginExpiryInDays', 0)) and
                    not request.proxy_emp_code and not request.proxy_creator
                ):
                    auth_details.sd_sm_statusid = 5
                    session.commit()
                    error_message = "Login expired"
                    return ResponseModel(code=0, message=error_message)

                if request.source != 'SSO' and days_since_pwd_change >= pwd_exp_days:
                    pwd_expire = True
                    error_message = "Password Expired"
                    return ResponseModel(code=0, message=error_message)

                screen_mapping_query = (
                    session.query(EmployeeScreenMapping)
                    .filter(
                        EmployeeScreenMapping.employeecode == request.emp_code,
                        EmployeeScreenMapping.applicable == True,
                        EmployeeScreenMapping.fromdate <= datetime.utcnow(),
                        EmployeeScreenMapping.todate >= datetime.utcnow()
                    )
                    .order_by(EmployeeScreenMapping.createddate.desc())
                    .limit(1)
                )
                screen_mapping = screen_mapping_query.first()
                if screen_mapping_query.count() > 1:
                    print(f"Warning: Multiple EmployeeScreenMapping rows for emp_code {request.emp_code}")

                if screen_mapping:
                    landing_page = screen_mapping.pagename
                    is_new_directory = screen_mapping.isnewdirectory
                    alert_message = screen_mapping.alertmessage
                elif request.user_type == 'G':
                    landing_page = config_dict.get('DefaultGuestLoginPage')
                if not landing_page:
                    landing_page = config_dict.get('DefaultAfterLoginPage')

                # Define the reporting manager alias outside the query selection
                reporting_manager_alias = ReqRecEmployeeDetails.__table__.alias("reporting_manager")

                emp_details_query = (
                    session.query(
                        ReqRecEmployeeDetails,
                        ReqRecEmployeeFinDetails,
                        PersonalDetails,
                        PersonalContactDetails
                    )
                    .outerjoin(
                        ReqRecEmployeeFinDetails,
                        ReqRecEmployeeDetails.ed_empid == ReqRecEmployeeFinDetails.efd_ed_empid
                    )
                    .outerjoin(
                        PersonalDetails,
                        ReqRecEmployeeDetails.ed_empcode == PersonalDetails.employeecode
                    )
                    .outerjoin(
                        PersonalContactDetails,
                        ReqRecEmployeeDetails.ed_empcode == PersonalContactDetails.employeecode
                    )
                    .outerjoin(
                        reporting_manager_alias,
                        ReqRecEmployeeFinDetails.efd_reportingmanager == reporting_manager_alias.c.ed_empcode
                    )
                    .filter(ReqRecEmployeeDetails.ed_empcode == request.emp_code)
                    .order_by(ReqRecEmployeeDetails.ed_empid.asc())
                    .limit(1)
                )
                emp_details = emp_details_query.first()
                if emp_details_query.count() > 1:
                    print(f"Warning: Multiple employee details rows for emp_code {request.emp_code}")

                if emp_details:
                    emp, fin, pers, cont = emp_details
                    # Fetch reporting manager details from the aliased table
                    reporting_manager_query = (
                        session.query(ReqRecEmployeeDetails)
                        .filter(ReqRecEmployeeDetails.ed_empcode == (fin.efd_reportingmanager if fin else None))
                        .limit(1)
                    )
                    reporting_manager = reporting_manager_query.first()

                    emp_code_min_length = (
                        session.query(func.min(func.len(EmployeeMaster.employeecode)))
                        .scalar() or 0
                    )

                    roles = (
                        session.query(RoleMaster, EmployeeRoleMapping)
                        .join(
                            EmployeeRoleMapping,
                            RoleMaster.roleid == EmployeeRoleMapping.roleid
                        )
                        .filter(
                            EmployeeRoleMapping.employeecode == request.emp_code,
                            EmployeeRoleMapping.applicable == True,
                            RoleMaster.applicable == True
                        )
                        .all()
                    )
                    role_ids = "|".join(str(r.RoleMaster.roleid) for r in roles)
                    role_descriptions = "|".join(r.RoleMaster.roledescription for r in roles)
                    proxy_role = next(
                        (r.RoleMaster.roledescription for r in roles if r.RoleMaster.isproxy and config_dict.get('SwitchUserSetting') == '1'),
                        None
                    )

                    proxy_emp_count = (
                        session.query(func.count())
                        .select_from(EmployeeRoleMapping)
                        .filter(EmployeeRoleMapping.employeecode == request.emp_code)
                        .scalar() or 0
                    )

                    blood_group = (
                        session.query(BloodGroupMaster.code)
                        .filter(BloodGroupMaster.bloodgroupid == (pers.bloodgroupid if pers else None))
                        .scalar() if pers and pers.bloodgroupid else None
                    )

                    if config_dict.get('IsOrganogramEmployeeApplicable') == '1':
                        team_count = 0
                    else:
                        team_count = (
                            session.query(func.count())
                            .select_from(EmployeeMaster)
                            .join(
                                EmploymentDetails,
                                EmployeeMaster.employeecode == EmploymentDetails.employeecode
                            )
                            .filter(
                                EmploymentDetails.reportingmanagercode == request.emp_code,
                                EmploymentDetails.employeestatus == 1
                            )
                            .scalar() or 0
                        )

                    is_new_home = 'true' if config_dict.get('SetupNewUx') == '1' else 'false'

                login_history = LoginHistory(
                    sessionid=session_id,
                    subscription=request.subscription_name,
                    userid=request.proxy_emp_code or request.emp_code,
                    type=1,
                    errordesc="SUCCESS",
                    token=token,
                    ipaddress=request.ip_address,
                    computername=request.computer_name,
                    macaddress=request.mac_address,
                    latitude=request.latitude,
                    longitude=request.longitude,
                    location=request.location,
                    signupid=signup_id,
                    source=request.source,
                    appversion=request.app_version,
                    deviceid=request.device_id
                )
                session.add(login_history)

                if auth_details:
                    auth_details.sd_failcount = 0
                last_login_entry_query = (
                    session.query(LastSuccessfulLogin)
                    .filter(LastSuccessfulLogin.userid == request.emp_code)
                    .order_by(LastSuccessfulLogin.logintime.desc())
                    .limit(1)
                )
                last_login_entry = last_login_entry_query.first()
                if last_login_entry_query.count() > 1:
                    print(f"Warning: Multiple LastSuccessfulLogin entries for emp_code {request.emp_code}")

                if last_login_entry:
                    last_login_entry.logintime = datetime.utcnow()
                else:
                    session.add(LastSuccessfulLogin(userid=request.emp_code))

                session.commit()

                response_data = {
                    "AuthToken": token,
                    "UserInfo": {
                        "EmpCode": request.emp_code,
                        "SubscriptionName": request.subscription_name,
                        "LandingPage": landing_page,
                        "LastLogin": previous_login_date.isoformat() if previous_login_date else None,
                        "EmployeeId": emp_id if auth_result else None,
                        "SignUpID": str(signup_id) if signup_id else None,
                        "AlertMessage": alert_message or "",
                        "personalDetails": {
                            "employeePhoto": emp.ed_employee_photo or "" if emp_details else "",
                            "salutation": emp.ed_salutation or "" if emp_details else "",
                            "firstName": emp.ed_firstname or "" if emp_details else "",
                            "middleName": emp.ed_middlename or "" if emp_details else "",
                            "lastName": emp.ed_lastname or "" if emp_details else "",
                            "xeroEmpId": "0",
                            "gender": emp.ed_sex or "" if emp_details else "",
                            "email": emp.ed_email or "" if emp_details else "",
                            "mobileNo": emp.ed_mobile or "" if emp_details else "",
                            "landlineNumber": emp.ed_workingtelephone or "" if emp_details else "",
                            "extension": emp.ed_workingtelephone or "" if emp_details else "",
                            "presentAddress": emp.ed_presentaddress or "" if emp_details else "",
                            "recordDateOfBirth": emp.ed_dob.isoformat() if emp_details and emp.ed_dob else None,
                            "dateOfMarriage": fin.efd_dateofmarriage.isoformat() if emp_details and fin and fin.efd_dateofmarriage else None
                        },
                        "orgDetails": {
                            "dateOfJoining": emp.ed_doj.isoformat() if emp_details and emp.ed_doj else None,
                            "reportingManagerCode": fin.efd_reportingmanager or "" if emp_details and fin else "",
                            "reportingManagerName": f"{reporting_manager.ed_firstname} {reporting_manager.ed_lastname}" 
                                                    if emp_details and reporting_manager else "",
                            "reportingManagerEmail": reporting_manager.ed_email or "" 
                                                    if emp_details and reporting_manager else "",
                            "reportingManagerMobile": reporting_manager.ed_mobile or "" 
                                                    if emp_details and reporting_manager else "",
                            "reportingManagerPhoto": reporting_manager.ed_employee_photo or "" 
                                                    if emp_details and reporting_manager else "",
                            "proxyEmpCount": proxy_emp_count if emp_details else 0,
                            "empCodeMinLength": min(emp_code_min_length, 3) if emp_details else 0
                        },
                        "roles": {
                            "roleIds": role_ids if emp_details else "",
                            "roleDescriptions": role_descriptions if emp_details else "",
                            "proxyRole": proxy_role if emp_details else None
                        }
                    }
                }

                return ResponseModel(
                    code=1,
                    message="Login successful",
                    data=response_data
                )

            finally:
                session.close()
                engine.dispose()

        except Exception as e:
            print(f"Login error: {e}")
            return ResponseModel(
                code=-1,
                message=f"An error occurred during login: {str(e)}"
            )