from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func
from geo_ai_backend.database import Base


class ObjectsHistory(Base):
    __tablename__ = "objects_history"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now())
    object_name = Column(String)
    action = Column(String)
    username = Column(String)
    project = Column(String)
    description = Column(String)


class ActionHistory(Base):
    __tablename__ = "action_history"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now())
    user_action = Column(String)
    username = Column(String)
    project = Column(String)
    description = Column(String)
    project_id = Column(Integer)
    owner_id = Column(Integer)
    project_type = Column(String)


class ErrorHistory(Base):
    __tablename__ = "error_history"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now())
    user_action = Column(String)
    username = Column(String)
    project = Column(String)
    description = Column(String)
    code = Column(String)
    project_id = Column(Integer)
    owner_id = Column(Integer)
    project_type = Column(String)
