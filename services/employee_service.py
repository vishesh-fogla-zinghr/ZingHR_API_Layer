# app/services/employee_service.py
from sqlalchemy.orm import Session
from app.repositories import employee_repository
from app.schemas.employee_schema import EmployeeCreate, EmployeeUpdate

def get_employee_service(db: Session, employee_id: int):
    return employee_repository.get_employee_by_id(db, employee_id)



def list_employees_service(db: Session, skip: int = 0, limit: int = 100):
    return employee_repository.get_employees(db)

def create_employee_service(db: Session, employee: EmployeeCreate):
    return employee_repository.create_employee(db, employee)

def update_employee_service(db: Session, employee_id: int, employee_update: EmployeeUpdate):
    db_employee = employee_repository.get_employee_by_id(db, employee_id)
    if not db_employee:
        raise Exception("Employee not found")
    return employee_repository.update_employee(db, db_employee, employee_update)

def delete_employee_service(db: Session, employee_id: int):
    db_employee = employee_repository.get_employee_by_id(db, employee_id)
    if not db_employee:
        raise Exception("Employee not found")
    employee_repository.delete_employee(db, db_employee)
