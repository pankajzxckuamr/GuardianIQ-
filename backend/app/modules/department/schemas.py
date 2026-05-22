from typing import Optional

from pydantic import BaseModel


class DepartmentCreate(BaseModel):
    department_code: str
    department_name: str
    description: Optional[str] = None


class DepartmentResponse(BaseModel):
    id: int
    department_code: str
    department_name: str
    description: Optional[str]

    class Config:
        from_attributes = True
        