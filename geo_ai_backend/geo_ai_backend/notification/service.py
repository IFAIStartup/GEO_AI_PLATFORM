import math

from sqlalchemy.orm import Session

from geo_ai_backend.notification.models import Notification
from geo_ai_backend.notification.schemas import (
    CreateNotificationSchemas,
    NotificationSchemas,
    NotificationsSchemas,
)


def get_notification_by_id_service(id: int, db: Session) -> Notification:
    db_notification = db.query(Notification).filter(Notification.id == id).first()
    return db_notification


def get_new_notification_service(db: Session) -> NotificationSchemas:
    db_notification = db.query(Notification).order_by(Notification.id.desc()).first()
    return NotificationSchemas(
        id=db_notification.id,
        data=db_notification.data,
        created_at=db_notification.created_at,
        read=db_notification.read,
    )


def create_notification_service(
    params: CreateNotificationSchemas, db: Session
) -> NotificationSchemas:
    db_notification = Notification(data=params.data)
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return NotificationSchemas(
        id=db_notification.id,
        data=db_notification.data,
        created_at=db_notification.created_at,
        read=db_notification.read,
    )


def read_notification_service(id: int, db: Session) -> NotificationSchemas:
    db_notification = db.query(Notification).filter(Notification.id == id).first()
    db_notification.read = True
    db.commit()
    db.refresh(db_notification)
    return NotificationSchemas(
        id=db_notification.id,
        data=db_notification.data,
        created_at=db_notification.created_at,
        read=db_notification.read,
    )


def delete_notification_service(id: int, db: Session) -> NotificationSchemas:
    db_notification = db.query(Notification).filter(Notification.id == id).first()
    db.delete(db_notification)
    db.commit()
    return NotificationSchemas(
        id=db_notification.id,
        data=db_notification.data,
        created_at=db_notification.created_at,
        read=db_notification.read,
    )


def get_notifications_service(
    page: int,
    limit: int,
    db: Session,
) -> NotificationsSchemas:
    notification_table = db.query(Notification)

    total = len(notification_table.all())
    offset = (page - 1) * limit
    pages = math.ceil(total / limit) if total else 0
    notification_table = notification_table.offset(offset).limit(limit).all()

    if not notification_table:
        return NotificationsSchemas(
            notifications=[], page=page, pages=pages, total=total, limit=limit
        )

    notifications_list = [
        {
            "id": i.id,
            "data": i.data,
            "created_at": i.created_at,
            "read": i.read,
        }
        for i in notification_table
    ]

    notifications = [NotificationSchemas(**i) for i in notifications_list]
    return NotificationsSchemas(
        notifications=notifications,
        page=page,
        pages=pages,
        total=total,
        limit=limit,
    )
