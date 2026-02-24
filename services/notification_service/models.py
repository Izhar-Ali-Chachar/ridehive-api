from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class NotificationChannel(str, Enum):
    PUSH = "push"
    SMS = "sms"
    EMAIL = "email"


class RecipientType(str, Enum):
    RIDER = "rider"
    DRIVER = "driver"

class Notification(SQLModel, table=True):
    """
    Stores all notifications sent
    in the system
    """
    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )
    recipient_id: int             
    recipient_type: RecipientType
    title: str
    message: str
    type: NotificationType
    channel: NotificationChannel
    is_read: bool = Field(default=False)
    ride_id: Optional[int] = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now()
    )

class NotificationResponse(SQLModel):
    id: int
    recipient_id: int
    recipient_type: RecipientType
    title: str
    message: str
    type: NotificationType
    is_read: bool
    created_at: datetime


class UnreadCountResponse(SQLModel):
    recipient_id: int
    unread_count: int