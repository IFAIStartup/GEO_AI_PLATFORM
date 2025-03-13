from typing import Dict

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session

from geo_ai_backend.auth.exceptions import LoginExternalUserException
from geo_ai_backend.auth.permissions import (
    admin_permission,
    get_current_user_from_access,
    get_current_user_from_refresh,
)
from geo_ai_backend.auth.schemas import (
    AllUsersSchemas,
    ChangeStatusUserSchemas,
    ChangeUserDataSchemas,
    CreateUserSchemas,
    DeleteUserResponseSchemas,
    LoginResponseSchemas,
    LoginSchemas,
    RestoreAccess,
    RestoreAccessChangePasswordSchemas,
    SortKeyEnum,
    UserChangePasswordSchemas,
    UserRolesEnum,
    UserRolesFilterEnum,
    UserSchemas,
    UserServiceSchemas,
)
from geo_ai_backend.auth.service import (
    authenticate_ldap_user_service,
    authenticate_user_service,
    change_password_service,
    change_status_user_service,
    change_user_data_service,
    create_mlflow_user_service,
    create_user_service,
    delete_mlflow_user_service,
    delete_user_service,
    get_all_user_service,
    get_id_user_by_hash,
    get_status_hash_key_service,
    get_user_by_email_service,
    get_user_by_id_service,
    restore_access_service,
    delete_active_hash_by_id_service,
    delete_active_hash_by_user_id_service,
    update_mlflow_user_password_service,
)
from geo_ai_backend.auth.utils import (
    create_access_token,
    create_refresh_token,
    password_verification,
)
from geo_ai_backend.config import settings
from geo_ai_backend.database import get_db
from geo_ai_backend.email.service import send_email
from geo_ai_backend.email.templates import INVITE_USER_TEMPLATE, RESTORE_ACCESS_TEMPLATE

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/login",
    response_model=LoginResponseSchemas,
    responses={
        401: {
            "description": "Incorrect username or password",
            "content": {
                "application/json": {
                    "example": {"detail": "Incorrect username or password"}
                }
            },
        }
    },
)
async def login(
    params: LoginSchemas, response: Response, db: Session = Depends(get_db)
) -> LoginResponseSchemas:
    try:
        auth_status = authenticate_user_service(
            email=params.email, password=params.password, db=db
        )
    except LoginExternalUserException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid email address", "code": "INVALID_EMAIL"},
        )

    if settings.LDAP_ON:
        if not auth_status:
            auth_status = authenticate_ldap_user_service(
                username=params.email, password=params.password, db=db
            )
    if not auth_status:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Incorrect username or password",
                "code": "INVALID_LOGIN_PASSWORD",
            },
        )
    user = get_user_by_email_service(email=params.email, db=db)
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    response.set_cookie("refresh_token",
                        refresh_token,
                        httponly=True,
                        max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
                        secure=True,
                        samesite="none",
                        )
    return LoginResponseSchemas(
        access_token=access_token,
        user=UserServiceSchemas(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role,
            created_at=user.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            is_active=user.is_active,
            external_user=user.external_user,
        ),
    )


@router.get(
    "/refresh",
    response_model=LoginResponseSchemas,
    responses={
        401: {
            "description": "Token expired",
            "content": {"application/json": {"example": {"detail": "Token expired"}}},
        },
        403: {
            "description": "Could not validate credentials",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not validate credentials"}
                }
            },
        },
    },
)
async def refresh_token(
    request: Request,
    response: Response,
    current_user: UserServiceSchemas = Depends(get_current_user_from_refresh),
) -> LoginResponseSchemas:
    access_token = create_access_token(subject=current_user.id)
    return LoginResponseSchemas(
        access_token=access_token,
        user=UserServiceSchemas(
            id=current_user.id,
            email=current_user.email,
            username=current_user.username,
            role=current_user.role,
            created_at=current_user.created_at,
            is_active=current_user.is_active,
            external_user=current_user.external_user,
        ),
    )


@router.get(
    "/logout",
    responses={
        200: {
            "content": {"application/json": {"example": {"status": "ok"}}},
        },
    },
)
async def logout(
    response: Request,
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> Dict[str, str]:
    if "resfresh_token" in response.cookies:
        response.cookies.pop("refresh_token")
    return {"status": "ok"}


@router.post(
    "/create-user",
    response_model=UserSchemas,
    responses={
        400: {
            "description": "Email already registered",
            "content": {
                "application/json": {"example": {"detail": "Email already registered"}}
            },
        },
    },
)
async def create_user(
    params: CreateUserSchemas,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(admin_permission),
) -> UserSchemas:
    db_user = get_user_by_email_service(email=params.email, db=db)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Email already registered",
                "code": "EMAIL_ALREADY_REGISTERED",
            },
        )
    user = create_user_service(user=params, db=db)

    if settings.MLFLOW_ON and user.role != UserRolesEnum.user:
        create_mlflow_user_service(username=user.email, password=user.password)

    delete_active_hash_by_user_id_service(user_id=user.id, db=db)
    hash_key = restore_access_service(user=user, db=db)
    path = f"/restore-access/{hash_key}?isNew=true"
    secure = "s" if settings.HTTPS_ON else ""
    port_full = "" if settings.HTTPS_ON else f":{settings.PORT}"
    url = f"http{secure}://{settings.EXTERNAL_HOST}{port_full}{path}"
    template = INVITE_USER_TEMPLATE.format(
        title="Account is activated", name=user.email, link=url
    )
    background_tasks.add_task(
        send_email,
        receiver_email=user.email,
        subject="Account is activated",
        template=template,
    )
    return user


@router.post(
    "/delete-user",
    response_model=DeleteUserResponseSchemas,
    responses={
        400: {
            "description": "The user does not exist",
            "content": {
                "application/json": {"example": {"detail": "The user does not exist"}}
            },
        },
    },
)
async def delete_user(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(admin_permission),
) -> DeleteUserResponseSchemas:
    db_user = get_user_by_id_service(id=id, db=db)
    if not db_user or not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "The user does not exist", "code": "USER_NOT_FOUND"},
        )
    if not db_user.external_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Сannot delete internal user",
                "code": "INTERNAL_USER_CANNOT_DELETE",
            },
        )
    user = delete_user_service(id=id, db=db)

    if settings.MLFLOW_ON and user.role != UserRolesEnum.user:
        delete_mlflow_user_service(username=user.email)

    return DeleteUserResponseSchemas(status="ok", user=user)


@router.post(
    "/change-password",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "message": "Password has been successfully changed",
                    }
                }
            },
        },
        400: {
            "description": "Something went wrong",
            "content": {
                "application/json": {"example": {"detail": "Something went wrong"}}
            },
        },
        403: {
            "description": "Invalid password",
            "content": {
                "application/json": {"example": {"detail": "Invalid password"}}
            },
        },
    },
)
async def change_password(
    params: UserChangePasswordSchemas,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> Dict[str, str]:
    db_user = get_user_by_id_service(id=params.id, db=db)
    if not db_user or not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Something went wrong", "code": "USER_NOT_FOUND"},
        )
    if not db_user.external_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Сannot change password internal user",
                "code": "INTERNAL_USER_CANNOT_CHANGE_PASSWORD",
            },
        )
    verified = password_verification(
        password=params.old_password, hashed_password=db_user.password
    )
    if not verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Invalid password", "code": "INVALID_PASSWORD"},
        )
    user = change_password_service(id=params.id, password=params.password, db=db)

    if settings.MLFLOW_ON and user.role != UserRolesEnum.user:
        update_mlflow_user_password_service(username=user.email, password=user.password)
    return {"status": "ok", "message": "Password has been successfully changed"}


@router.get("/all-users", response_model=AllUsersSchemas)
async def get_all_users(
    search: str = "",
    filter: UserRolesFilterEnum = UserRolesFilterEnum.all,
    sort: SortKeyEnum = SortKeyEnum.default,
    reverse: bool = False,
    page: int = 1,
    limit: int = Query(default=10, lte=10),
    db: Session = Depends(get_db),
    current_user: UserSchemas = Depends(admin_permission),
) -> AllUsersSchemas:
    rsl = get_all_user_service(
        search=search,
        filter=filter,
        sort=sort,
        reverse=reverse,
        page=page,
        limit=limit,
        db=db,
    )
    return rsl


@router.post(
    "/change-user-data",
    response_model=UserServiceSchemas,
    responses={
        400: {
            "description": "The user does not exist",
            "content": {
                "application/json": {"example": {"detail": "The user does not exist"}}
            },
        },
        422: {
            "description": "Role is not valid",
            "content": {
                "application/json": {"example": {"detail": "Role is not valid"}}
            },
        },
    },
)
async def change_user_data(
    params: ChangeUserDataSchemas,
    db: Session = Depends(get_db),
    current_user: UserSchemas = Depends(admin_permission),
) -> UserServiceSchemas:
    db_user = get_user_by_id_service(id=params.id, db=db)
    if not db_user or not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "The user does not exist", "code": "USER_NOT_FOUND"},
        )
    user = change_user_data_service(
        id=params.id, username=params.username, role=params.role, db=db
    )
    return user


@router.post(
    "/change-status-user",
    response_model=UserServiceSchemas,
    responses={
        400: {
            "description": "The user does not exist",
            "content": {
                "application/json": {"example": {"detail": "The user does not exist"}}
            },
        },
    },
)
async def change_status_user(
    params: ChangeStatusUserSchemas,
    db: Session = Depends(get_db),
    current_user: UserSchemas = Depends(admin_permission),
) -> UserServiceSchemas:
    db_user = get_user_by_id_service(id=params.id, db=db)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "The user does not exist", "code": "USER_NOT_FOUND"},
        )
    user = change_status_user_service(id=params.id, status=params.status, db=db)
    return user


@router.get(
    "/invite-user",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "message": "An invitation has been sent to the mail",
                    }
                }
            },
        },
        400: {
            "description": "The user does not exist",
            "content": {
                "application/json": {"example": {"detail": "The user does not exist"}}
            },
        },
    },
)
async def get_invite_user(
    id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserSchemas = Depends(admin_permission),
) -> Dict[str, str]:
    db_user = get_user_by_id_service(id=id, db=db)
    if not db_user or not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "The user does not exist", "code": "USER_NOT_FOUND"},
        )

    if not db_user.external_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Сannot restore access internal user",
                "code": "INTERNAL_USER_CANNOT_RESTORE_ACCESS",
            },
        )
    delete_active_hash_by_user_id_service(user_id=db_user.id, db=db)
    hash_key = restore_access_service(user=db_user, db=db)
    path = f"/restore-access/{hash_key}?isNew=true"
    secure = "s" if settings.HTTPS_ON else ""
    port_full = "" if settings.HTTPS_ON else f":{settings.PORT}"
    url = f"http{secure}://{settings.EXTERNAL_HOST}{port_full}{path}"
    template = INVITE_USER_TEMPLATE.format(
        title="Account is activated", name=db_user.email, link=url
    )
    background_tasks.add_task(
        send_email,
        receiver_email=db_user.email,
        subject="Account is activated",
        template=template,
    )
    return {"status": "ok", "message": "An invitation has been sent to the mail"}


@router.post(
    "/restore_access",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "message": "Link to change your password will be sent to <email> email",
                    }
                }
            },
        },
        400: {
            "description": "User is not exist",
            "content": {
                "application/json": {"example": {"detail": "User is not exist"}}
            },
        },
    },
)
async def restore_access(
    params: RestoreAccess,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    db_user = get_user_by_email_service(email=params.email, db=db)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "User is not exist", "code": "USER_NOT_FOUND"},
        )
    if not db_user.external_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Сannot restore access internal user",
                "code": "INTERNAL_USER_CANNOT_RESTORE_ACCESS",
            },
        )
    delete_active_hash_by_user_id_service(user_id=db_user.id, db=db)
    hash_key = restore_access_service(user=db_user, db=db)
    path = f"/restore-access/{hash_key}"
    secure = "s" if settings.HTTPS_ON else ""
    port_full = "" if settings.HTTPS_ON else f":{settings.PORT}"
    url = f"http{secure}://{settings.EXTERNAL_HOST}{port_full}{path}"
    template = RESTORE_ACCESS_TEMPLATE.format(link=url)
    background_tasks.add_task(
        send_email,
        receiver_email=db_user.email,
        subject="Restore access",
        template=template,
    )
    return {
        "status": "ok",
        "message": f"Link to change your password will be sent to {params.email} email",
    }


@router.get(
    "/restore_access/status",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": True,
                },
            },
        },
    },
)
async def get_status_hash_key(key: str, db: Session = Depends(get_db)) -> bool:
    status = get_status_hash_key_service(key=key, db=db)
    return status


@router.post(
    "/restore_access/change-password",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "message": "Password has been successfully changed",
                    }
                }
            },
        },
        400: {
            "description": "Something went wrong",
            "content": {
                "application/json": {"example": {"detail": "Something went wrong"}}
            },
        },
        403: {
            "description": "The link has ended",
            "content": {
                "application/json": {"example": {"detail": "The link has ended"}}
            },
        },
    },
)
async def restore_access_change_password(
    key: str,
    params: RestoreAccessChangePasswordSchemas,
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    status_hash = get_status_hash_key_service(key=key, db=db)
    if not status_hash:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "The link has ended", "code": "LINK_HAS_ENDED"},
        )
    active_hash = get_id_user_by_hash(key=key, db=db)
    if not active_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Something went wrong", "code": "к"},
        )
    db_user = get_user_by_id_service(id=active_hash.user_id, db=db)
    if not db_user or not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Something went wrong", "code": "SOMETHING_WENT_WRONG"},
        )

    user = change_password_service(id=db_user.id, password=params.password, db=db)

    if settings.MLFLOW_ON and user.role != UserRolesEnum.user:
        update_mlflow_user_password_service(username=user.email, password=user.password)

    delete_active_hash_by_id_service(id=active_hash.id, db=db)
    return {"status": "ok", "message": "Password has been successfully changed"}
