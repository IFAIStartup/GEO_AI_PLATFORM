from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func
from geo_ai_backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String)
    password = Column(String)
    role = Column(String)
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    external_user = Column(Boolean, default=True)


class InternalUser(Base):
    __tablename__ = "internal_users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    role = Column(String)
    created_at = Column(DateTime, default=datetime.now())
    is_active = Column(Boolean, default=True)
    external_user = Column(Boolean, default=False)


class ActiveHash(Base):
    __tablename__ = "active_hash"
    id = Column(Integer, primary_key=True, index=True)
    hash_key = Column(String, unique=True)
    user_id = Column(Integer, unique=True)
    created_at = Column(DateTime, default=datetime.now())
