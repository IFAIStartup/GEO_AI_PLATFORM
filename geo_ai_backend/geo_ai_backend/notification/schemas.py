import datetime
from typing import Any, Dict, List

from pydantic import BaseModel


class CreateNotificationSchemas(BaseModel):
    data: Dict[str, Any]


class NotificationSchemas(BaseModel):
    id: int
    data: Dict[str, Any]
    created_at: datetime.datetime
    read: bool


class NotificationsSchemas(BaseModel):
    notifications: List[NotificationSchemas]
    page: int
    pages: int
    total: int
    limit: int
