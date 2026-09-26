from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime, timedelta
from typing import List, TypeVar, Optional, Generic

T = TypeVar("T")


class SecretSchema(BaseModel):
    id: int
    username: str
    password : str | None = None
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

class EntraVaultAssociationSchema(BaseModel):
    id: int
    vault_id: int
    entra_id: int

    model_config = ConfigDict(from_attributes=True)

class EntraCredentialSchema(BaseModel):
    id : int
    secret_id : str
    object_id : str
    client_id : str
    display_name : str
    start_date : datetime
    end_date : datetime
    vault_associations: list[EntraVaultAssociationSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
    