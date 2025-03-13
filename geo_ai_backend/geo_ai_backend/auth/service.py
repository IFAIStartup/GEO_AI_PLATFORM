import math
import requests
from datetime import datetime, timedelta
from typing import Optional

from ldap3 import ALL, Connection, Server
from ldap3.core.exceptions import LDAPException
from sqlalchemy.orm import Session

from geo_ai_backend.auth.exceptions import LoginExternalUserException
from geo_ai_backend.auth.models import ActiveHash, User
from geo_ai_backend.auth.schemas import (
    AllUsersSchemas,
    CreateUserSchemas,
    SortKeyEnum,
    UserRolesFilterEnum,
    UserSchemas,
    UserServiceSchemas,
)
from geo_ai_backend.auth.utils import (
    generate_password,
    generate_random_hash,
    get_username_from_email,
    hash_password,
    is_email,
    password_verification,
)
from geo_ai_backend.config import settings


def get_user_by_email_service(email: str, db: Session) -> User:
    db_user = db.query(User).filter(User.email == email).first()
    return db_user


def get_user_by_id_service(id: int, db: Session) -> User:
    db_user = db.query(User).filter(User.id == id).first()
    return db_user


def get_user_by_username_service(username: str, db: Session) -> User:
    db_user = db.query(User).filter(User.username == username).first()
    return db_user


def get_all_user_service(
    search: str,
    filter: str,
    sort: str,
    reverse: bool,
    page: int,
    limit: int,
    db: Session,
) -> AllUsersSchemas:
    user_table = db.query(User)
    if search:
        user_table = user_table.filter(
            User.email.like(f"%{search}%") | User.username.like(f"%{search}%")
        )

    if filter != UserRolesFilterEnum.all:
        user_table = user_table.filter(User.role == filter)

    total = len(user_table.all())
    offset = (page - 1) * limit
    pages = math.ceil(total / limit) if total else 0
    db_users = user_table.offset(offset).limit(limit).all()

    if not db_users:
        return AllUsersSchemas(
            users=[], page=page, pages=pages, total=total, limit=limit
        )

    users_list = [
        {
            "id": i.id,
            "email": i.email,
            "username": i.username,
            "role": i.role,
            "created_at": i.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "is_active": i.is_active,
            "external_user": i.external_user,
        }
        for i in db_users
    ]
    if sort != SortKeyEnum.default:
        users_list = sorted(users_list, key=lambda d: d[sort], reverse=reverse)
    users = [UserServiceSchemas(**i) for i in users_list]
    return AllUsersSchemas(
        users=users,
        page=page,
        pages=pages,
        total=total,
        limit=limit,
    )


def create_user_service(user: CreateUserSchemas, db: Session) -> UserSchemas:
    password = generate_password()
    hashed_password = hash_password(password=password)
    username = (
        user.username if user.username else get_username_from_email(email=user.email)
    )
    db_user = User(
        email=user.email, username=username, password=hashed_password, role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return UserSchemas(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username,
        password=password,
        role=db_user.role,
        created_at=db_user.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        external_user=db_user.external_user,
    )


def create_ldap_user_service(username: str, db: Session) -> UserSchemas:
    password = generate_password()
    hashed_password = hash_password(password=password)
    db_user = User(
        email=username,
        username=username,
        password=hashed_password,
        role="user",
        external_user=False,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return UserSchemas(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username,
        password=password,
        role=db_user.role,
        created_at=db_user.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        external_user=db_user.external_user,
    )


def delete_user_service(id: int, db: Session) -> UserServiceSchemas:
    db_user = db.query(User).filter(User.id == id).first()
    db_user.is_active = False
    db.commit()
    db.refresh(db_user)
    return UserServiceSchemas(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username,
        role=db_user.role,
        created_at=db_user.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        is_active=db_user.is_active,
        external_user=db_user.external_user,
    )


def change_password_service(id: int, password: str, db: Session) -> User:
    hashed_password = hash_password(password=password)
    db_user = db.query(User).filter(User.id == id).first()
    db_user.password = hashed_password
    db.commit()
    db.refresh(db_user)
    return UserSchemas(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username,
        password=password,
        role=db_user.role,
        created_at=db_user.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        external_user=db_user.external_user,
    )


def authenticate_user_service(email: str, password: str, db: Session) -> bool:
    if not is_email(email=email):
        db_user = get_user_by_username_service(username=email, db=db)
        if db_user and db_user.external_user:
            raise LoginExternalUserException
    db_user = get_user_by_email_service(email=email, db=db)
    if not db_user or not db_user.is_active:
        return False
    verified = password_verification(
        password=password, hashed_password=db_user.password
    )
    if not verified:
        return False
    return True


def authenticate_ldap_user_service(username: str, password: str, db: Session) -> bool:
    if settings.LDAP_DOMAIN not in username:
        username = f"{settings.LDAP_DOMAIN}{username}"
    try:
        server = Server(settings.LDAP_SERVER, get_info=ALL)
        conn = Connection(server, user=username, password=password, auto_bind=True)
        if conn.result and conn.result["description"] == "success":
            username = username.removeprefix(settings.LDAP_DOMAIN)
            db_user = get_user_by_username_service(username=username, db=db)
            if not db_user:
                create_ldap_user_service(username=username, db=db)
            return True
        return False
    except LDAPException:
        return False


def change_user_data_service(
    id: int, username: str, role: str, db: Session
) -> UserServiceSchemas:
    db_user = db.query(User).filter(User.id == id).first()
    db_user.username = username
    db_user.role = role
    db.commit()
    db.refresh(db_user)
    return UserServiceSchemas(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username,
        role=db_user.role,
        created_at=db_user.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        is_active=db_user.is_active,
        external_user=db_user.external_user,
    )


def change_status_user_service(
    id: int, status: bool, db: Session
) -> UserServiceSchemas:
    db_user = db.query(User).filter(User.id == id).first()
    db_user.is_active = status
    db.commit()
    db.refresh(db_user)
    return UserServiceSchemas(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username,
        role=db_user.role,
        created_at=db_user.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        is_active=db_user.is_active,
        external_user=db_user.external_user,
    )


def restore_access_service(user: User, db: Session) -> str:
    hash_key = generate_random_hash()
    active_hash = ActiveHash(hash_key=hash_key, user_id=user.id)
    db.add(active_hash)
    db.commit()
    db.refresh(active_hash)
    return hash_key


def get_status_hash_key_service(key: str, db: Session) -> bool:
    active_hash = db.query(ActiveHash).filter(ActiveHash.hash_key == key).first()
    if not active_hash:
        return False
    elif (
        datetime.now() - timedelta(hours=24) <= active_hash.created_at <= datetime.now()
    ):
        return True
    db.delete(active_hash)
    db.commit()
    return False


def get_id_user_by_hash(key: str, db: Session) -> ActiveHash:
    active_hash = db.query(ActiveHash).filter(ActiveHash.hash_key == key).first()
    if not active_hash:
        return None
    return active_hash


def delete_active_hash_by_id_service(id: int, db: Session) -> int:
    db_active_hash = db.query(ActiveHash).filter(ActiveHash.id == id).first()
    db.delete(db_active_hash)
    db.commit()
    return db_active_hash.id


def delete_active_hash_by_user_id_service(user_id: int, db: Session) -> Optional[int]:
    db_active_hash = db.query(ActiveHash).filter(ActiveHash.user_id == user_id).first()
    if not db_active_hash:
        return None
    db.delete(db_active_hash)
    db.commit()
    return db_active_hash.id


def create_mlflow_user_service(
    username: str, password: str, is_admin=False
) -> Optional[int]:
    path = "api/2.0/mlflow/users/create"
    response = requests.post(
        f"{settings.URL_MLFLOW}:{settings.PROT_MLFLOW}/{path}",
        auth=(settings.LOGIN_MLFLOW, settings.PASSWORD_MLFLOW),
        json={
            "username": username,
            "password": password,
        },
    )
    if not response:
        return None
    if is_admin:
        path = "2.0/mlflow/users/update-admin"
        response = requests.patch(
            f"{settings.URL_MLFLOW}:{settings.PROT_MLFLOW}/{path}",
            auth=(settings.LOGIN_MLFLOW, settings.PASSWORD_MLFLOW),
            json={
                "username": username,
                "is_admin": is_admin,
            },
        )
    return response.status_code


def update_mlflow_user_password_service(username: str, password: str) -> Optional[int]:
    path = "api/2.0/mlflow/users/update-password"
    response = requests.patch(
        f"{settings.URL_MLFLOW}:{settings.PROT_MLFLOW}/{path}",
        auth=(settings.LOGIN_MLFLOW, settings.PASSWORD_MLFLOW),
        json={
            "username": username,
            "password": password,
        },
    )
    if not response:
        return None
    return response.status_code


def delete_mlflow_user_service(username: str) -> Optional[int]:
    path = "api/2.0/mlflow/users/delete"
    response = requests.delete(
        f"{settings.URL_MLFLOW}:{settings.PROT_MLFLOW}/{path}",
        auth=(settings.LOGIN_MLFLOW, settings.PASSWORD_MLFLOW),
        json={"username": username},
    )
    if not response:
        return None
    return response.status_code


def create_default_ml_user_service():
    create_mlflow_user_service(
        username="admin@mail.ru", password="3tjq4UKTPwcXELuY", is_admin=True
    )
