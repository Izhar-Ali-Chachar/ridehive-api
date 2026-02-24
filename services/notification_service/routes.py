from fastapi import APIRouter, HTTPException


from services.notification_service.models import (
    NotificationResponse,
    UnreadCountResponse,
    RecipientType
)

from services.notification_service.service import (
    get_notifications,
    mark_as_read,
    mark_all_as_read,
    get_unread_count
)

from database.session import sessionDep

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)

@router.get(
    "/rider/{rider_id}",
    response_model=list[NotificationResponse]
)
async def get_rider_notifications(
    session: sessionDep,
    rider_id: int,
    unread_only: bool = False,
):
    return await get_notifications(
        recipient_id = rider_id,
        recipient_type = RecipientType.RIDER,
        session = session,
        unread_only = unread_only
    )

@router.get(
    "/driver/{driver_id}",
    response_model=list[NotificationResponse]
)
async def get_driver_notifications(
    session: sessionDep,
    driver_id: int,
    unread_only: bool = False,
):
    return await get_notifications(
        recipient_id = driver_id,
        recipient_type = RecipientType.DRIVER,
        session = session,
        unread_only = unread_only
    )

@router.patch("/{notification_id}/read")
async def read_notification(
    notification_id: int,
    session: sessionDep
):
  notification = await mark_as_read(notification_id, session)

  if not notification:
    raise HTTPException(
        status_code=404,
        detail="Notification not found"
    )
  return {"message": "Marked as read", "id": notification_id}

@router.patch("/rider/{rider_id}/read-all")
async def read_all_rider(
    rider_id: int,
    session: sessionDep
):
    count = await mark_all_as_read(
        recipient_id=rider_id,
        recipient_type=RecipientType.RIDER,
        session=session
    )

    return {"message": f"{count} notifications marked as read"}

@router.patch("/driver/{driver_id}/read-all")
async def read_all_driver(
    driver_id: int,
    session: sessionDep
):
    count = await mark_all_as_read(
        recipient_id=driver_id,
        recipient_type=RecipientType.DRIVER,
        session=session
    )

    return {"message": f"{count} notifications marked as read"}

@router.get(
    "/rider/{rider_id}/unread",
    response_model=UnreadCountResponse
)
async def rider_unread_count(
    rider_id: int,
    session: sessionDep
):
   count = await get_unread_count(
      rider_id,
      RecipientType.RIDER,
      session
   )

   return UnreadCountResponse(
      recipient_id=rider_id,
      unread_count=count
   )

@router.get(
    "/driver/{driver_id}/unread",
    response_model=UnreadCountResponse
)
def driver_unread_count(
    driver_id: int,
    session: sessionDep
):
    count = get_unread_count(
        recipient_id=driver_id,
        recipient_type=RecipientType.DRIVER,
        session=session
    )
    return UnreadCountResponse(
        recipient_id=driver_id,
        unread_count=count
    )