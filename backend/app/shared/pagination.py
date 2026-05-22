from pydantic import BaseModel


class PaginationParams(BaseModel):
    page: int = 1
    size: int = 10


class PaginatedResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list