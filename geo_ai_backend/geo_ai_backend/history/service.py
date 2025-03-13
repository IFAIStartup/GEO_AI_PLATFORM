import math
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from geo_ai_backend.history.models import (
    ActionHistory,
    ObjectsHistory,
    ErrorHistory,
)
from geo_ai_backend.history.schemas import (
    CreateActionHistorySchemas,
    ActionHistorySchemas,
    ActionHistoriesSchemas,
    CreateObjectHistorySchemas,
    ObjectHistorySchemas,
    ObjectHistoriesSchemas,
    ErrorHistorySchemas,
    CreateErrorHistorySchemas,
    ErrorHistoriesSchemas,
)
from geo_ai_backend.project.service import check_projects_service


def get_action_history_by_id_service(id: int, db: Session) -> ActionHistory:
    return db.query(ActionHistory).filter(ActionHistory.id == id).first()


def get_object_history_by_id_service(id: int, db: Session) -> ObjectsHistory:
    return db.query(ObjectsHistory).filter(ObjectsHistory.id == id).first()


def get_error_history_by_id_service(id: int, db: Session) -> ErrorHistory:
    return db.query(ErrorHistory).filter(ErrorHistory.id == id).first()


def delete_action_history_by_id_service(id: int, db: Session) -> ActionHistorySchemas:
    db_action_history = db.query(ActionHistory).filter(ActionHistory.id == id).first()
    db.delete(db_action_history)
    db.commit()
    return ActionHistorySchemas(
        id=db_action_history.id,
        date=db_action_history.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        user_action=db_action_history.user_action,
        username=db_action_history.username,
        project=db_action_history.project,
        description=db_action_history.description,
        project_id=db_action_history.project_id,
        owner_id=db_action_history.owner_id,
        project_type=db_action_history.project_type,
    )


def delete_object_history_by_id_service(id: int, db: Session) -> ObjectHistorySchemas:
    db_object_history = db.query(ObjectsHistory).filter(ObjectsHistory.id == id).first()
    db.delete(db_object_history)
    db.commit()
    return ObjectHistorySchemas(
        id=db_object_history.id,
        object_name=db_object_history.object_name,
        action=db_object_history.action,
        username=db_object_history.username,
        project=db_object_history.project,
        description=db_object_history.description,
    )


def delete_error_history_by_id_service(id: int, db: Session) -> ErrorHistorySchemas:
    db_error_history = db.query(ErrorHistory).filter(ErrorHistory.id == id).first()
    db.delete(db_error_history)
    db.commit()
    return ErrorHistorySchemas(
        id=db_error_history.id,
        date=db_error_history.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        user_action=db_error_history.user_action,
        username=db_error_history.username,
        project=db_error_history.project,
        description=db_error_history.description,
        code=db_error_history.code,
        project_id=db_error_history.project_id,
        owner_id=db_error_history.owner_id,
        project_type=db_error_history.project_type,
    )


def clear_all_action_history(db: Session) -> None:
    db.query(ActionHistory).delete()
    db.commit()


def clear_all_object_history(db: Session) -> None:
    db.query(ObjectsHistory).delete()
    db.commit()


def clear_all_error_history(db: Session) -> None:
    db.query(ErrorHistory).delete()
    db.commit()


def create_action_history_service(
    action_history: CreateActionHistorySchemas, owner_id: int, db: Session
) -> ActionHistorySchemas:
    db_action_history = ActionHistory(
        user_action=action_history.user_action,
        username=action_history.username,
        project=action_history.project,
        description=action_history.description,
        project_id=action_history.project_id,
        owner_id=owner_id,
        project_type=action_history.project_type,
    )
    db.add(db_action_history)
    db.commit()
    db.refresh(db_action_history)
    return ActionHistorySchemas(
        id=db_action_history.id,
        date=db_action_history.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        user_action=db_action_history.user_action,
        username=db_action_history.username,
        project=db_action_history.project,
        description=db_action_history.description,
        project_id=db_action_history.project_id,
        owner_id=db_action_history.owner_id,
        project_type=db_action_history.project_type,
    )


def create_object_history_service(
    object_history: CreateObjectHistorySchemas, db: Session
) -> ObjectHistorySchemas:
    db_object_history = ObjectsHistory(
        user_action=object_history.user_action,
        username=object_history.username,
        project=object_history.project,
        description=object_history.description,
    )
    db.add(db_object_history)
    db.commit()
    db.refresh(db_object_history)
    return ObjectHistorySchemas(
        id=db_object_history.id,
        object_name=db_object_history.object_name,
        action=db_object_history.action,
        username=db_object_history.username,
        project=db_object_history.project,
        description=db_object_history.description,
    )


def create_error_history_service(
    error_history: CreateErrorHistorySchemas, owner_id: int, db: Session
) -> ErrorHistorySchemas:
    db_error_history = ErrorHistory(
        user_action=error_history.user_action,
        username=error_history.username,
        project=error_history.project,
        description=error_history.description,
        code=error_history.code,
        project_id=error_history.project_id,
        owner_id=owner_id,
        project_type=error_history.project_type,
    )
    db.add(db_error_history)
    db.commit()
    db.refresh(db_error_history)
    return ErrorHistorySchemas(
        id=db_error_history.id,
        date=db_error_history.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        user_action=db_error_history.user_action,
        username=db_error_history.username,
        project=db_error_history.project,
        description=db_error_history.description,
        code=db_error_history.code,
        project_id=db_error_history.project_id,
        owner_id=db_error_history.owner_id,
        project_type=db_error_history.project_type,
    )


def get_all_action_history_service(
    from_date: datetime,
    to_date: datetime,
    search: str,
    reverse: bool,
    page: int,
    limit: int,
    owner_id: int,
    owner_role: str,
    db: Session,
) -> ActionHistoriesSchemas:
    action_history_table = db.query(ActionHistory)
    if owner_role != "admin":
        action_history_table = action_history_table.filter(
            ActionHistory.owner_id == owner_id
        )

    if from_date and to_date:
        action_history_table = action_history_table.filter(
            ActionHistory.created_at.between(from_date, to_date)
        )
    elif from_date and not to_date:
        action_history_table = action_history_table.filter(
            ActionHistory.created_at >= f"{from_date}"
        )
    elif not from_date and to_date:
        action_history_table = action_history_table.filter(
            ActionHistory.created_at <= f"{to_date}"
        )

    if search:
        action_history_table = action_history_table.filter(
            or_(
                ActionHistory.project.like(f"%{search}%"),
                ActionHistory.user_action.like(f"%{search}%"),
            )
        )

    total = len(action_history_table.all())
    offset = (page - 1) * limit
    pages = math.ceil(total / limit) if total else 0

    if not reverse:
        action_history_table = action_history_table.order_by(
            desc(ActionHistory.created_at)
        )
    else:
        action_history_table = action_history_table.order_by(
            asc(ActionHistory.created_at)
        )

    db_action_history = action_history_table.offset(offset).limit(limit).all()

    if not db_action_history:
        return ActionHistoriesSchemas(
            histories=[], page=page, pages=pages, total=total, limit=limit
        )

    action_history_list = [
        {
            "id": i.id,
            "date": i.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "user_action": i.user_action,
            "username": i.username,
            "project": i.project,
            "description": i.description,
            "project_id": check_projects_service(id=i.project_id, db=db),
            "owner_id": i.owner_id,
            "project_type": i.project_type,
        }
        for i in db_action_history
    ]

    action_histories = [ActionHistorySchemas(**i) for i in action_history_list]

    return ActionHistoriesSchemas(
        histories=action_histories,
        page=page,
        pages=pages,
        total=total,
        limit=limit,
    )


def get_all_object_history_service(
    from_date: datetime,
    to_date: datetime,
    search: str,
    reverse: bool,
    page: int,
    limit: int,
    db: Session,
) -> ObjectHistoriesSchemas:
    object_history_table = db.query(ObjectsHistory)

    if from_date and to_date:
        object_history_table = object_history_table.filter(
            ObjectsHistory.created_at.between(from_date, to_date)
        )
    elif from_date and not to_date:
        object_history_table = object_history_table.filter(
            ObjectsHistory.created_at >= f"{from_date}"
        )
    elif not from_date and to_date:
        object_history_table = object_history_table.filter(
            ObjectsHistory.created_at <= f"{to_date}"
        )

    if search:
        object_history_table = object_history_table.filter(
            or_(
                ObjectsHistory.project.like(f"%{search}%"),
                ObjectsHistory.user_action.like(f"%{search}%"),
            )
        )

    total = len(object_history_table.all())
    offset = (page - 1) * limit
    pages = math.ceil(total / limit) if total else 0

    if not reverse:
        object_history_table = object_history_table.order_by(
            desc(ObjectsHistory.created_at)
        )
    else:
        object_history_table = object_history_table.order_by(
            asc(ObjectsHistory.created_at)
        )

    db_object_history = object_history_table.offset(offset).limit(limit).all()

    if not db_object_history:
        return ObjectHistoriesSchemas(
            histories=[], page=page, pages=pages, total=total, limit=limit
        )
    object_history_list = [
        {
            "id": i.id,
            "date": i.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "object_name": i.object_name,
            "action": i.action,
            "username": i.username,
            "project": i.project,
            "description": i.description,
        }
        for i in db_object_history
    ]

    object_histories = [ObjectHistorySchemas(**i) for i in object_history_list]

    return ObjectHistoriesSchemas(
        histories=object_histories,
        page=page,
        pages=pages,
        total=total,
        limit=limit,
    )


def get_all_error_history_service(
    from_date: datetime,
    to_date: datetime,
    search: str,
    reverse: bool,
    page: int,
    limit: int,
    owner_id: int,
    owner_role: str,
    db: Session,
) -> ErrorHistoriesSchemas:
    error_history_table = db.query(ErrorHistory)
    if owner_role != "admin":
        error_history_table = error_history_table.filter(
            ErrorHistory.owner_id == owner_id
        )

    if from_date and to_date:
        error_history_table = error_history_table.filter(
            ErrorHistory.created_at.between(from_date, to_date)
        )
    elif from_date and not to_date:
        error_history_table = error_history_table.filter(
            ErrorHistory.created_at >= f"{from_date}"
        )
    elif not from_date and to_date:
        error_history_table = error_history_table.filter(
            ErrorHistory.created_at <= f"{to_date}"
        )

    if search:
        error_history_table = error_history_table.filter(
            or_(
                ErrorHistory.project.like(f"%{search}%"),
                ErrorHistory.user_action.like(f"%{search}%"),
            )
        )

    total = len(error_history_table.all())
    offset = (page - 1) * limit
    pages = math.ceil(total / limit) if total else 0

    if not reverse:
        error_history_table = error_history_table.order_by(
            desc(ErrorHistory.created_at)
        )
    else:
        error_history_table = error_history_table.order_by(asc(ErrorHistory.created_at))

    db_error_history = error_history_table.offset(offset).limit(limit).all()

    if not db_error_history:
        return ErrorHistoriesSchemas(
            histories=[], page=page, pages=pages, total=total, limit=limit
        )

    error_history_list = [
        {
            "id": i.id,
            "date": i.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "user_action": i.user_action,
            "username": i.username,
            "project": i.project,
            "description": i.description,
            "code": i.code,
            "project_id": check_projects_service(id=i.project_id, db=db),
            "owner_id": i.owner_id,
            "project_type": i.project_type,
        }
        for i in db_error_history
    ]

    error_histories = [ErrorHistorySchemas(**i) for i in error_history_list]

    return ErrorHistoriesSchemas(
        histories=error_histories,
        page=page,
        pages=pages,
        total=total,
        limit=limit,
    )
