from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union

from fastapi import HTTPException, status
from pydantic import BaseModel, validator


class TypeProjectEnum(str, Enum):
    aerial_images = "aerial_images"
    satellite_images = "satellite_images"
    panorama_360 = "panorama_360"
    all = "all"


class StatusProjectEnum(str, Enum):
    ready_to_start = "Ready to start"
    in_progress = "In progress"
    completed = "Completed"
    error = "Error"


class SortKeyEnum(str, Enum):
    name = "name"
    date = "date"
    created_at = "created_at"
    created_by = "created_by"


class CreateProjectSchemas(BaseModel):
    name: str
    date: datetime
    link: str
    type: TypeProjectEnum

    @validator("type", pre=True)
    def valid_type(cls, v: str) -> str:
        if v and v not in [i.value for i in TypeProjectEnum]:
            raise HTTPException(
                detail={
                    "message": (
                        "Type of project is not valid enumeration member; "
                        "permitted: 'aerial_images', 'satellite_images', 'panorama_360'"
                    ),
                    "code": "PROJECT_TYPE_INVALID",
                },
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("name", pre=True)
    def empty_name(cls, v: str) -> str:
        if not v:
            raise HTTPException(
                detail={
                    "message": "Name cannot be empty",
                    "code": "PROJECT_NAME_EMPTY",
                },
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("name")
    def short_name(cls, v: str) -> str:
        if len(v) < 6:
            raise HTTPException(
                detail={
                    "message": "The name cannot be shorter than 6 characters",
                    "code": "PROJECT_NAME_TOO_SHORT",
                },
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("date", pre=True)
    def empty_date(cls, v: str) -> str:
        if not v:
            raise HTTPException(
                detail={
                    "message": "Date cannot be empty",
                    "code": "PROJECT_DATE_EMPTY",
                },
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("date", pre=True)
    def format_date(cls, v: str) -> str:
        try:
            bool(datetime.strptime(v, "%Y-%m-%dT%H:%M:%S.%fZ"))
        except ValueError:
            raise HTTPException(
                detail={
                    "message": "Invalid date format",
                    "code": "PROJECT_DATE_INVALID",
                },
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("link", pre=True)
    def empty_link(cls, v: str) -> str:
        if not v:
            raise HTTPException(
                detail={
                    "message": "Link cannot be empty",
                    "code": "PROJECT_LINK_EMPTY",
                },
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v


class ProjectSchemas(BaseModel):
    id: int
    name: str
    date: str
    link: str
    type: TypeProjectEnum
    status: StatusProjectEnum
    created_at: str
    detection_id: Optional[str]
    preview_layer_id: Optional[str]
    task_result: Optional[Dict[str, Any]]
    input_files: Optional[Dict[str, Any]]
    ml_model: Optional[Union[List, str]]
    ml_model_deeplab: Optional[Union[List, str]]
    created_by: Optional[str]
    error_code: Optional[str]
    description: Optional[str]
    classes: Optional[List[str]]
    super_resolution: Optional[str]
    owner_id: Optional[int]


class ProjectsSchemas(BaseModel):
    projects: List[ProjectSchemas]
    page: int
    pages: int
    total: int
    limit: int


class AerialImagesFileSchemas(BaseModel):
    name: str
    path: str
    path_tif: str


class Panorama360FileSchemas(BaseModel):
    name: str
    path: str


class Panorama360DataSchemas(BaseModel):
    name: str
    longitude: str
    latitude: str


class Panorama360FilesSchemas(BaseModel):
    title: str
    images: List[Panorama360FileSchemas]


class ProjectFilesSchemas(BaseModel):
    aerial_images: Optional[List[AerialImagesFileSchemas]]
    panorama_360: Optional[List[Panorama360FilesSchemas]]
    layer_id: str


class DeleteProjectSchemas(BaseModel):
    status: str
    project: ProjectSchemas


class CoordinatesSchemas(BaseModel):
    lon: float
    lat: float


class GeoCoordinateSchemas(BaseModel):
    coordinates: CoordinatesSchemas
    name: str


class FieldNameEnum(str, Enum):
    name = "name"
    longitude = "longitude"
    latitude = "latitude"
    title = "title"


class FieldNameInputEnum(str, Enum):
    name = "file_name"
    longitude = "longitude[deg]"
    latitude = "latitude[deg]"


class DataCsvSchemas(BaseModel):
    data: list[FieldNameInputEnum]


class SortCompareKeyEnum(str, Enum):
    project_1 = "project_1"
    project_2 = "project_2"
    created_at = "created_at"
    default = "default"


class CompareProjectObj(BaseModel):
    name: str
    date: str


class CompareProjectSchemas(BaseModel):
    id: int
    project_1: CompareProjectObj
    project_2: CompareProjectObj
    # project_1: str
    # project_2: str
    # shooting_date_1: str
    # shootion_date_2: str
    type: TypeProjectEnum
    status: StatusProjectEnum
    task_id: Optional[str] = None
    task_result: Optional[Dict[str, Any]] = None
    created_at: str
    error_code: Optional[str]
    description: Optional[str]
    owner: Optional[int] = None


class CompareProjectsSchemas(BaseModel):
    projects: List[CompareProjectSchemas]
    page: int
    pages: int
    total: int
    limit: int
