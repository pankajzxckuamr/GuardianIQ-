from typing import Optional
from pydantic import BaseModel
from app.shared.enums.source_type import SourceType


class DataSourceCreate(BaseModel):
    source_name: str

    source_type: SourceType

    description: Optional[str] = None

    status: str

    owner_department_id: int


class DataSourceResponse(BaseModel):
    id: int

    source_name: str

    source_type: str

    description: Optional[str]

    status: str

    owner_department_id: int

    class Config:
        from_attributes = True
