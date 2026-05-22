from typing import Optional

from pydantic import BaseModel


class BaseFilter(BaseModel):
    search: Optional[str] = None

    status: Optional[str] = None
