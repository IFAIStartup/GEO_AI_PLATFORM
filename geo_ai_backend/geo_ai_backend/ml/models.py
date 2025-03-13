from sqlalchemy import Column, DateTime, Integer, String, Boolean, ARRAY, JSON, Float
from sqlalchemy.sql import func

from geo_ai_backend.database import Base


class ML(Base):
    __tablename__ = "ml"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    link = Column(String)
    type_of_data = Column(ARRAY(String))
    type_of_objects = Column(ARRAY(String))
    default_model = Column(Boolean)
    constant = Column(Boolean)
    created_at = Column(DateTime, default=func.now())
    task_id = Column(String)
    task_result = Column(JSON, default=None)
    status = Column(String)
    experiment_name = Column(String)
    ml_flow_url = Column(String)
    view = Column(String)
    created_by = Column(String)
    tile_size = Column(Integer)
    scale_factor = Column(Float)


class MLClasses(Base):
    __tablename__ = "ml_classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    type_of_objects = Column(String)
    created_at = Column(DateTime, default=func.now())
