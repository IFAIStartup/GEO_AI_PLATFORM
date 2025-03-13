from fastapi import Depends, HTTPException, Request, status
from jose import jwt
from sqlalchemy.orm import Session

from geo_ai_backend.auth.constants import JWT_REFRESH_SECRET_KEY, JWT_SECRET_KEY
from geo_ai_backend.auth.schemas import UserRolesEnum, UserServiceSchemas
from geo_ai_backend.auth.service import get_user_by_id_service
from geo_ai_backend.auth.utils import check_token_lifetime, decode_token
from geo_ai_backend.database import get_db


def get_current_user_from_access(
    request: Request, db: Session = Depends(get_db)
) -> UserServiceSchemas:
    token = request.headers.get("Authorization", "")
    return get_current_user_from_token(token=token, token_type="access_token", db=db)


def get_current_user_from_refresh(
    request: Request, db: Session = Depends(get_db)
) -> UserServiceSchemas:
    token = request.cookies.get("refresh_token")
    return get_current_user_from_token(token=token, token_type="refresh_token", db=db)


def get_current_user_from_token(
    token: str, token_type: str, db: Session
) -> UserServiceSchemas:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Could not validate credentials", "code": "INVALID_TOKEN"},
            headers={"Authenticate": "Bearer"},
        )
    try:
        token = (
            token.split("Bearer")[1].replace(" ", "")
            if token_type == "access_token"
            else token
        )
        secret = (
            JWT_SECRET_KEY if token_type == "access_token" else JWT_REFRESH_SECRET_KEY
        )
        payload = decode_token(token=token, key=secret)
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Could not validate credentials", "code": "INVALID_TOKEN"},
            headers={"Authenticate": "Bearer"},
        )
    if not check_token_lifetime(exp=payload.get("exp", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"Authenticate": "Bearer"},
        )
    user = get_user_by_id_service(id=int(payload["sub"]), db=db)
    return UserServiceSchemas(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role,
        created_at=user.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        is_active=user.is_active,
        external_user=user.external_user,
    )


def admin_permission(request: Request, db: Session = Depends(get_db)) -> None:
    user = get_current_user_from_token(
        token=request.headers.get("Authorization", ""),
        token_type="access_token",
        db=db,
    )
    if user.role != UserRolesEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Admin role required", "code": "ADMIN_REQUIRED"},
        )
