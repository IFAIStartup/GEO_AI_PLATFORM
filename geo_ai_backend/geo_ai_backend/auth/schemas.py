import re
from enum import Enum
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, validator


class TokenSchemas(BaseModel):
    access_token: str


class UserRolesEnum(str, Enum):
    user = "user"
    ml_user = "ml_user"
    admin = "admin"


class UserRolesFilterEnum(str, Enum):
    all = "all"
    user = "user"
    ml_user = "ml_user"
    admin = "admin"


class SortKeyEnum(str, Enum):
    id = "id"
    role = "role"
    created_at = "created_at"
    default = "default"


class UserSchemas(BaseModel):
    id: int
    email: str
    username: str
    password: str
    role: str
    created_at: str
    external_user: bool


class UserServiceSchemas(BaseModel):
    id: int
    email: str
    username: str
    role: str
    created_at: str
    is_active: bool
    external_user: bool


class LoginSchemas(BaseModel):
    email: str
    password: str


class LoginResponseSchemas(BaseModel):
    access_token: str
    user: UserServiceSchemas


class DeleteUserResponseSchemas(BaseModel):
    status: str
    user: UserServiceSchemas


class CreateUserSchemas(BaseModel):
    email: str
    username: Optional[str]
    role: Optional[str] = UserRolesEnum.user

    @validator("email")
    def empty_email(cls, v: str) -> str:
        if not v:
            raise HTTPException(
                detail={"message": "Email cannot be empty", "code": "EMPTY_EMAIL"},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("email")
    def check_email(cls, v: str) -> str:
        regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        if not re.match(regex, v):
            raise HTTPException(
                detail={"message": "Email address is not valid", "code": "INVALID_EMAIL"},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("role")
    def valid_role(cls, v: str) -> str:
        if v and v not in [i.value for i in UserRolesEnum]:
            raise HTTPException(
                detail={"message": "Role is not valid", "code": "INVALID_ROLE"},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("role")
    def empty_role(cls, v: str) -> str:
        if not v:
            return UserRolesEnum.user
        return v


class AllUsersSchemas(BaseModel):
    users: List[Optional[UserServiceSchemas]]
    page: int
    pages: int
    total: int
    limit: int


class UserChangePasswordSchemas(BaseModel):
    id: int
    old_password: str
    password: str
    confirm_password: str

    @validator("old_password")
    def empty_old_password(cls, v: str) -> str:
        if not v:
            raise HTTPException(
                detail={"message": "Old password cannot be empty", "code": "EMPTY_OLD_PASSWORD"},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("password")
    def empty_password(cls, v: str) -> str:
        if not v:
            raise HTTPException(
                detail={"message": "Password cannot be empty", "code": "EMPTY_PASSWORD"},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("confirm_password")
    def empty_confirm_password(cls, v: str) -> str:
        if not v:
            raise HTTPException(
                detail={"message": "Password cannot be empty", "code": "EMPTY_CONFIRM_PASSWORD"},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("password")
    def check_password(cls, v: str) -> str:
        """Description regex.
        Has minimum 8 characters in length. {8,}
        At least one uppercase English letter. (?=.*?[A-Z])
        At least one lowercase English letter. (?=.*?[a-z])
        At least one digit. (?=.*?[0-9])
        At least one special character. (?=.*?[#?!@$%^&*-])
        """
        regex = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$"
        if not re.search(re.compile(regex), v):
            raise HTTPException(
                detail={"message": "Password is not valid", "code": "INVALID_CHANGE_PASSWORD"},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("password")
    def match_password_old_password(cls, v: str, values: Dict[str, str]) -> str:
        if "old_password" in values and v == values["old_password"]:
            raise HTTPException(
                detail={"message": "The old and new password must not match", "code": "PASSWORD_MATCH_OLD_PASSWORD"},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("confirm_password")
    def verify_password_match(cls, v: str, values: Dict[str, str]) -> str:
        if "password" in values and v != values["password"]:
            raise HTTPException(
                detail={"message": "Passwords do not match", "code": "PASSWORDS_DO_NOT_MATCH"},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v


class RestoreAccessChangePasswordSchemas(BaseModel):
    password: str
    confirm_password: str

    @validator("password")
    def empty_password(cls, v: str) -> str:
        if not v:
            raise HTTPException(
                detail={"message": "Password cannot be empty", "code": "EMPTY_PASSWORD"},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("confirm_password")
    def empty_confirm_password(cls, v: str) -> str:
        if not v:
            raise HTTPException(
                detail={"message": "Password cannot be empty", "code": "EMPTY_PASSWORD"},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("password")
    def check_password(cls, v: str) -> str:
        """Description regex.
        Has minimum 8 characters in length. {8,}
        At least one uppercase English letter. (?=.*?[A-Z])
        At least one lowercase English letter. (?=.*?[a-z])
        At least one digit. (?=.*?[0-9])
        At least one special character. (?=.*?[#?!@$%^&*-])
        """
        regex = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$"
        if not re.search(re.compile(regex), v):
            raise HTTPException(
                detail={"message": "Password is not valid", "code": "INVALID_RESTORE_ACCESS_PASSWORD"},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("confirm_password")
    def verify_password_match(cls, v: str, values: Dict[str, str]) -> str:
        if "password" in values and v != values["password"]:
            raise HTTPException(
                detail={"message": "Passwords do not match", "code": "PASSWORDS_DO_NOT_MATCH"},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v


class ChangeUserDataSchemas(BaseModel):
    id: int
    username: str
    role: str

    @validator("role")
    def valid_role(cls, v: str) -> str:
        if v and v not in [i.value for i in UserRolesEnum]:
            raise HTTPException(
                detail={"message": "Role is not valid", "code": "INVALID_ROLE"},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v


class ChangeStatusUserSchemas(BaseModel):
    id: int
    status: bool


class RestoreAccess(BaseModel):
    email: str

    @validator("email")
    def empty_email(cls, v: str) -> str:
        if not v:
            raise HTTPException(
                detail={"message": "Email cannot be empty", "code": "EMPTY_EMAIL"},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("email")
    def check_email(cls, v: str) -> str:
        regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        if not re.match(regex, v):
            raise HTTPException(
                detail={"message": "Email address is not valid", "code": "INVALID_EMAIL"},
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v
