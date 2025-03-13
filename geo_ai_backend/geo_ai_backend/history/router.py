from typing import Dict, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from geo_ai_backend.history.service import (
    clear_all_error_history,
    create_action_history_service,
    create_error_history_service,
    create_object_history_service,
    delete_error_history_by_id_service,
    get_all_action_history_service,
    get_all_error_history_service,
    get_all_object_history_service,
    get_action_history_by_id_service,
    get_error_history_by_id_service,
    get_object_history_by_id_service,
    delete_action_history_by_id_service,
    delete_object_history_by_id_service,
    clear_all_action_history,
    clear_all_object_history,
)
from geo_ai_backend.history.schemas import (
    CreateActionHistorySchemas,
    CreateObjectHistorySchemas,
    ActionHistorySchemas,
    ObjectHistorySchemas,
    ActionHistoriesSchemas,
    ObjectHistoriesSchemas,
    ErrorHistorySchemas,
    ErrorHistoriesSchemas,
    CreateErrorHistorySchemas,
)
from geo_ai_backend.auth.permissions import get_current_user_from_access
from geo_ai_backend.auth.schemas import UserServiceSchemas
from geo_ai_backend.database import get_db


router = APIRouter(
    prefix="/history",
    tags=["history"],
)


@router.post(
    "/create-action-history",
    response_model=ActionHistorySchemas,
)
async def create_action_history(
    params: CreateActionHistorySchemas,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> ActionHistorySchemas:
    return create_action_history_service(
        action_history=params, owner_id=current_user.id, db=db
    )


@router.post(
    "/create-object-history",
    response_model=ObjectHistorySchemas,
)
async def create_object_history(
    params: CreateObjectHistorySchemas,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> ObjectHistorySchemas:
    return create_object_history_service(object_history=params, db=db)


@router.post(
    "/create-error-history",
    response_model=ActionHistorySchemas,
)
async def create_error_history(
    params: CreateErrorHistorySchemas,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> ErrorHistorySchemas:
    return create_error_history_service(
        error_history=params, owner_id=current_user.id, db=db
    )


@router.post("/delete-action-history", response_model=ActionHistorySchemas)
async def delete_action_history_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> ActionHistorySchemas:
    db_action_history = get_action_history_by_id_service(id=id, db=db)
    if not db_action_history:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="History is not exists",
        )
    if (
        db_action_history.owner_id != current_user.owner_id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Permission denied", "code": "PERMISSION_DENIED"},
        )
    return delete_action_history_by_id_service(id=id, db=db)


@router.post("/delete-object-history", response_model=ObjectHistorySchemas)
async def delete_object_history_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> ObjectHistorySchemas:
    db_object_history = get_object_history_by_id_service(id=id, db=db)
    if not db_object_history:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="History is not exists",
        )
    return delete_object_history_by_id_service(id=id, db=db)


@router.post("/delete-error-history", response_model=ErrorHistorySchemas)
async def delete_error_history_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> ErrorHistorySchemas:
    db_error_history = get_error_history_by_id_service(id=id, db=db)
    if not db_error_history:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="History is not exists",
        )
    if (
        db_error_history.owner_id != current_user.owner_id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Permission denied", "code": "PERMISSION_DENIED"},
        )
    return delete_error_history_by_id_service(id=id, db=db)


@router.post("/clear-action-history")
async def clear_action_history(
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> Dict[str, str]:
    clear_all_action_history(db=db)
    return {"status": "ok"}


@router.post("/clear-object-history")
async def clear_object_history(
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> Dict[str, str]:
    clear_all_object_history(db=db)
    return {"status": "ok"}


@router.post("/clear-error-history")
async def clear_error_history(
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> Dict[str, str]:
    clear_all_error_history(db=db)
    return {"status": "ok"}


@router.get("/get-action-history", response_model=ActionHistorySchemas)
async def get_action_history(
    id: int,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> ActionHistorySchemas:
    db_action_history = get_action_history_by_id_service(id=id, db=db)
    if not db_action_history:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="History is not exists",
        )
    if (
        db_action_history.owner_id != current_user.owner_id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Permission denied", "code": "PERMISSION_DENIED"},
        )
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


@router.get("/get-object-history", response_model=ObjectHistorySchemas)
async def get_object_history(
    id: int,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> ObjectHistorySchemas:
    db_object_history = get_object_history_by_id_service(id=id, db=db)
    if not db_object_history:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="History is not exists",
        )
    return ObjectHistorySchemas(
        id=db_object_history.id,
        date=db_object_history.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        object_name=db_object_history.object_name,
        action=db_object_history.action,
        username=db_object_history.username,
        project=db_object_history.project,
        description=db_object_history.description,
    )


@router.get("/get-error-history", response_model=ErrorHistorySchemas)
async def get_error_history(
    id: int,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> ErrorHistorySchemas:
    db_error_history = get_error_history_by_id_service(id=id, db=db)
    if not db_error_history:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="History is not exists",
        )
    if (
        db_error_history.owner_id != current_user.owner_id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Permission denied", "code": "PERMISSION_DENIED"},
        )
    return ErrorHistorySchemas(
        id=db_error_history.id,
        date=db_error_history.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        user_action=db_error_history.user_action,
        username=db_error_history.username,
        project=db_error_history.project,
        description=db_error_history.description,
        code=db_error_history.code,
        error_stack=db_error_history.error_stack,
        owner_id=db_error_history.owner_id,
        project_id=db_error_history.project_id,
        project_type=db_error_history.project_type,
    )


@router.get("/get-all-action-history", response_model=ActionHistoriesSchemas)
async def get_all_action_history(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    search: str = "",
    reverse: bool = False,
    page: int = 1,
    limit: int = Query(default=10, lte=10),
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> ActionHistoriesSchemas:
    db_action_history = get_all_action_history_service(
        from_date=from_date,
        to_date=to_date,
        search=search,
        reverse=reverse,
        page=page,
        limit=limit,
        owner_id=current_user.id,
        owner_role=current_user.role,
        db=db,
    )
    return db_action_history


@router.get("/get-all-object-history", response_model=ObjectHistoriesSchemas)
async def get_all_object_history(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    search: str = "",
    reverse: bool = False,
    page: int = 1,
    limit: int = Query(default=10, lte=10),
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> ObjectHistoriesSchemas:
    db_object_history = get_all_object_history_service(
        from_date=from_date,
        to_date=to_date,
        search=search,
        reverse=reverse,
        page=page,
        limit=limit,
        db=db,
    )
    return db_object_history


@router.get("/get-all-error-history", response_model=ErrorHistoriesSchemas)
async def get_all_error_history(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    search: str = "",
    reverse: bool = False,
    page: int = 1,
    limit: int = Query(default=10, lte=10),
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> ErrorHistoriesSchemas:
    db_error_history = get_all_error_history_service(
        from_date=from_date,
        to_date=to_date,
        search=search,
        reverse=reverse,
        page=page,
        limit=limit,
        owner_id=current_user.id,
        owner_role=current_user.role,
        db=db,
    )
    return db_error_history
