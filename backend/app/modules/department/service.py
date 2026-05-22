from sqlalchemy.orm import Session

from app.modules.department.models import Department
from app.modules.department.schemas import DepartmentCreate


def create_department(
    db: Session,
    payload: DepartmentCreate
):
    department = Department(
        department_code=payload.department_code,
        department_name=payload.department_name,
        description=payload.description
    )

    db.add(department)

    db.commit()

    db.refresh(department)

    return department


def get_departments(db: Session):
    return db.query(Department).all()
