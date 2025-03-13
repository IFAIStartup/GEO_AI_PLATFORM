from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from geo_ai_backend.database import get_db
from geo_ai_backend.notification.schemas import (
    CreateNotificationSchemas,
    NotificationSchemas,
    NotificationsSchemas,
)
from geo_ai_backend.notification.service import (
    create_notification_service,
    delete_notification_service,
    get_notification_by_id_service,
    get_notifications_service,
    read_notification_service,
)

router = APIRouter(
    prefix="/notification",
    tags=["notification"],
)


@router.post(
    "/create-notification",
    response_model=NotificationSchemas,
)
def create_notification(
    params: CreateNotificationSchemas, db: Session = Depends(get_db)
) -> NotificationSchemas:
    return create_notification_service(params=params, db=db)


@router.post(
    "/read-notification",
    response_model=NotificationSchemas,
)
async def read_notification(
    id: int, db: Session = Depends(get_db)
) -> NotificationSchemas:
    db_notification = get_notification_by_id_service(id=id, db=db)
    if not db_notification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The notification does not exist",
        )
    return read_notification_service(id=id, db=db)


@router.post(
    "/delete-notification",
    response_model=NotificationSchemas,
)
async def delete_notification(
    id: int, db: Session = Depends(get_db)
) -> NotificationSchemas:
    db_notification = get_notification_by_id_service(id=id, db=db)
    if not db_notification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The notification does not exist",
        )
    return delete_notification_service(id=id, db=db)


@router.get(
    "/get-notifications",
    response_model=NotificationsSchemas,
)
async def get_notifications(
    page: int = 1,
    limit: int = Query(default=10, lte=10),
    db: Session = Depends(get_db),
) -> NotificationsSchemas:
    return get_notifications_service(
        page=page,
        limit=limit,
        db=db,
    )
