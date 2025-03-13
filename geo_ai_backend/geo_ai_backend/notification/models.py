from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer

from geo_ai_backend.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.now())
    read = Column(Boolean, default=False)
