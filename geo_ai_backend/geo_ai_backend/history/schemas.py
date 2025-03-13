from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel


class SortKeyEnum(str, Enum):
    date = "date"
    default = "date"


class CreateActionHistorySchemas(BaseModel):
    user_action: str
    username: str
    project: str
    description: Optional[str]
    project_id: Optional[int]
    project_type: Optional[str]


class ActionHistorySchemas(BaseModel):
    id: str
    date: str
    user_action: str
    username: str
    project: str
    description: Optional[str]
    project_id: Optional[int]
    owner_id: Optional[int]
    project_type: Optional[str]


class ActionHistoriesSchemas(BaseModel):
    histories: List[ActionHistorySchemas]
    page: int
    pages: int
    total: int
    limit: int


class CreateObjectHistorySchemas(BaseModel):
    object_name: str
    action: str
    username: str
    project: str
    description: Optional[str]


class ObjectHistorySchemas(BaseModel):
    id: str
    date: str
    object_name: str
    action: str
    username: str
    project: str
    description: Optional[str]


class ObjectHistoriesSchemas(BaseModel):
    histories: List[ObjectHistorySchemas]
    page: int
    pages: int
    total: int
    limit: int


class ErrorHistorySchemas(BaseModel):
    id: str
    date: str
    user_action: str
    username: str
    project: str
    description: Optional[str]
    code: Optional[str]
    project_id: Optional[int]
    owner_id: Optional[int]
    project_type: Optional[str]


class CreateErrorHistorySchemas(BaseModel):
    user_action: str
    username: str
    project: str
    description: Optional[str]
    code: Optional[str]
    project_id: Optional[int]
    project_type: Optional[str]


class ErrorHistoriesSchemas(BaseModel):
    histories: List[ErrorHistorySchemas]
    page: int
    pages: int
    total: int
    limit: int
