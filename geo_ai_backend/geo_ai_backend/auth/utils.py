import random
import re
import secrets
import string
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

import bcrypt
from jose import jwt
from passlib.context import CryptContext

from geo_ai_backend.auth.constants import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    JWT_REFRESH_SECRET_KEY,
    JWT_SECRET_KEY,
    REFRESH_TOKEN_EXPIRE_MINUTES,
)

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_password() -> str:
    "Generates a password."
    all = string.ascii_lowercase + string.ascii_uppercase + string.digits
    temp = random.sample(all, 16)
    password = "".join(temp)
    return password


def hash_password(password: str) -> str:
    """Hashes the password."""
    byte_password = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(byte_password, salt).decode("utf-8")
    return hashed_password


def password_verification(password: str, hashed_password: str) -> bool:
    """Check the password with a hash password"""
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_hashed_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password, hashed_pass)


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[int] = None
) -> str:
    if expires_delta:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any], expires_delta: Optional[int] = None
) -> str:
    if expires_delta:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(
            minutes=REFRESH_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, ALGORITHM)
    return encoded_jwt


def decode_token(token: str, key: str) -> Dict[str, str]:
    return jwt.decode(token, key, algorithms=[ALGORITHM])


def check_token_lifetime(exp: str) -> bool:
    if datetime.fromtimestamp(exp) < datetime.now():
        return False
    return True


def get_username_from_email(email: str) -> str:
    return email.split("@")[0]


def generate_random_hash() -> str:
    return secrets.token_hex(nbytes=16)


def is_email(email: str) -> bool:
    regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
    if not re.match(regex, email):
        return False
    return True
