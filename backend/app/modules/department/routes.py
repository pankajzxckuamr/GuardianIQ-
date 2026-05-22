from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.db.session import get_db

from app.modules.department.schemas import (
    DepartmentCreate,
    DepartmentResponse
)

from app.modules.department.service import (
    create_department,
    get_departments
)

router = APIRouter(
    prefix="/api/departments",
    tags=["Departments"]
)


@router.post(
    "",
    response_model=DepartmentResponse
)
def create_department_api(
    payload: DepartmentCreate,
    db: Session = Depends(get_db)
):
    return create_department(db, payload)


@router.get(
    "",
    response_model=list[DepartmentResponse]
)
def get_departments_api(
    db: Session = Depends(get_db)
):
    return get_departments(db)
