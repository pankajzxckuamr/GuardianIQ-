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

from app.shared.response_utils import ResponseHelper
from app.shared.responses import StandardResponse

router = APIRouter(
    prefix="/api/departments",
    tags=["Departments"]
)


@router.post(
    "",
    response_model=StandardResponse[DepartmentResponse]
)
def create_department_api(
    payload: DepartmentCreate,
    db: Session = Depends(get_db)
):
    result = create_department(db, payload)
    return ResponseHelper.created(
        data=result,
        message="Department created successfully"
    )


@router.get(
    "",
    response_model=StandardResponse[list[DepartmentResponse]]
)
def get_departments_api(
    db: Session = Depends(get_db)
):
    result = get_departments(db)
    return ResponseHelper.list_response(
        items=result,
        message="Departments retrieved successfully"
    )
