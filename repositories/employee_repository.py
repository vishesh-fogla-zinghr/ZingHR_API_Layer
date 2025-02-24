from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.employee_model import Employee
from app.schemas.employee_schema import EmployeeCreate, EmployeeUpdate

def get_employees(db: Session) -> List[Employee]:
    return db.query(Employee).order_by(Employee.id).all()

def get_employee_by_id(db: Session, employee_id: int) -> Optional[Employee]:
    return db.query(Employee).filter(Employee.id == employee_id).first()

def create_employee(db: Session, employee: EmployeeCreate) -> Employee:
    db_employee = Employee(
        name=employee.name,
        email=employee.email,
        department=employee.department,
        position=employee.position
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

def update_employee(db: Session, db_employee: Employee, employee_update: EmployeeUpdate) -> Employee:
    for field, value in employee_update.dict(exclude_unset=True).items():
        setattr(db_employee, field, value)
    db.commit()
    db.refresh(db_employee)
    return db_employee

def delete_employee(db: Session, db_employee: Employee) -> None:
    db.delete(db_employee)
    db.commit()
