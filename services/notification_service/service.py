from sqlmodel import select
from fastapi import HTTPException
from typing import Optional

from services.notification_service.models import (
    Notification,
    RecipientType,
    NotificationChannel,
    NotificationType
)

async def get_notifications(
    recipient_id: int,
    recipient_type: RecipientType,
    session,
    unread_only: bool = False
) -> list[Notification]:

    query = select(Notification).where(
        Notification.recipient_id == recipient_id,
        Notification.recipient_type == recipient_type
    )

    if unread_only:
        query = query.where(Notification.is_read == False)

    query = query.order_by(Notification.created_at.desc()) #type: ignore

    result = await session.execute(query)

    return result.scalars().all()

async def mark_as_read(
    notification_id: int,
    session
) -> Optional[Notification]:
    notification: Optional[Notification] = await session.get(
        Notification,
        notification_id
    )

    if not notification:
        return None

    notification.is_read = True
    session.add(notification)
    await session.commit()
    await session.refresh(notification)

    return notification

async def mark_all_as_read(
    recipient_id: int,
    recipient_type: RecipientType,
    session,
    unread_only: bool = False
):
    notifications = await get_notifications(
        recipient_id,
        recipient_type,
        session,
        unread_only
    )

    for notification in notifications:
        notification.is_read = True
        session.add(notification)
    
    await session.commit()

    return len(notifications)

async def get_unread_count(
    recipient_id: int,
    recipient_type: RecipientType,
    session
):
    notifications = await get_notifications(
        recipient_id,
        recipient_type,
        session,
        unread_only=True
    )

    return len(notifications)

async def send_notification(
    session,
    recipient_id: int,
    recipient_type: RecipientType,
    title: str,
    message: str,
    type: NotificationType = NotificationType.INFO,
    channel: NotificationChannel = NotificationChannel.PUSH,
    ride_id: Optional[int] = None
):
    notification = Notification(
        recipient_id = recipient_id,
        recipient_type=recipient_type,
        title=title,
        message=message,
        type=type,
        channel=channel,
        ride_id=ride_id
    )

    session.add(notification)
    await session.commit()
    await session.refresh(notification)

    # log it
    print(
        f"🔔 Notification sent → "
        f"{recipient_type} {recipient_id}: "
        f"{title}"
    )

    return notification