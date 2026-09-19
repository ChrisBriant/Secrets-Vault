from pydantic import BaseModel, ConfigDict, computed_field
from typing import Optional
from datetime import datetime, timedelta
from typing import List, TypeVar, Optional, Generic

T = TypeVar("T")


class SecretSchema(BaseModel):
    id: int
    username: str
    password : str
    path : str
    last_updated : datetime
    created : datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    next_page: Optional[str]
    prev_page: Optional[str]
    total: int
    total_pages: int
    page: int
    page_size: int
