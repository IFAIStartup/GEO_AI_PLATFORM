from sqlalchemy import Column, DateTime, Integer, String, JSON, ARRAY
from sqlalchemy.sql import func

from geo_ai_backend.database import Base


class Projects(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    link = Column(String)
    type = Column(String)
    date = Column(DateTime)
    status = Column(String, default="Ready to start")
    created_at = Column(DateTime, default=func.now())
    task_result = Column(JSON, default=None)
    input_files = Column(JSON, default=None)
    detection_id = Column(String, default=None)
    preview_layer_id = Column(String, default=None)
    preview_selected_images = Column(ARRAY(String))
    ml_model = Column(ARRAY(String), default=None)
    ml_model_deeplab = Column(ARRAY(String), default=None)
    created_by = Column(String)
    description = Column(String, default=None)
    error_code = Column(String, default=None)
    classes = Column(ARRAY(String), default=None)
    super_resolution = Column(String, default=None)
    owner_id = Column(Integer, default=None)


class CompareProjects(Base):
    __tablename__ = "compare_projects"
    id = Column(Integer, primary_key=True, index=True)
    project_1 = Column(String)
    project_2 = Column(String)
    shooting_date_1 = Column(String)
    shooting_date_2 = Column(String)
    type = Column(String)
    status = Column(String, default="Ready to start")
    task_id = Column(String, default=None)
    task_result = Column(JSON, default=None)
    compare_id = Column(String, default=None)
    created_at = Column(DateTime, default=func.now())
    description = Column(String, default=None)
    error_code = Column(String, default=None)
    owner_id = Column(Integer, default=None)
