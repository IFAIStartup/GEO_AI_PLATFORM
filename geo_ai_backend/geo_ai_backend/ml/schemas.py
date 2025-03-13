from enum import Enum
from typing import Any, List, Optional, Dict

from fastapi import HTTPException, status
from pydantic import BaseModel, validator


class TypeMlModelTrainingEnum(str, Enum):
    yolov = "yolov8"
    yolov_det = "yolov8_det"
    deeplab = "deeplabv3"


class ViewMLModelEnum(str, Enum):
    yolov = "yolov8"
    yolov_det = "yolov8_det"
    deeplab = "deeplabv3"
    panorama_360 = "panorama_360"


class CropSizeEnum(int, Enum):
    aerial_images = 640
    satellite_images = 640
    panorama_360 = 0
    garbage = 0


class CropSizeEnumDeeplab(int, Enum):
    aerial_images = 640
    satellite_images = 640
    panorama_360 = 640


class ImageSizeEnum(int, Enum):
    aerial_images = 640
    satellite_images = 640
    panorama_360 = 1280
    garbage = 640


class ScaleFactorYoloEnum(float, Enum):
    aerial_images = 1
    satellite_images = 1
    panorama_360 = 0
    garbage = 0


class ScaleFactorDeeplabEnum(float, Enum):
    aerial_images = 0.625
    satellite_images = 1
    panorama_360 = 0


class ImageSizeEnumDeeplab(int, Enum):
    aerial_images = 640
    satellite_images = 640
    panorama_360 = 640


class SortKeyEnum(str, Enum):
    name = "name"
    created_at = "created_at"


class TypeMLModelEnum(str, Enum):
    aerial_images = "aerial_images"
    satellite_images = "satellite_images"
    panorama_360 = "panorama_360"
    garbage = "garbage"
    all = "all"


class StatusModelEnum(str, Enum):
    ready_to_use = "Ready to use"
    error = "Error"
    not_trained = "Not trained"
    in_the_training = "In the training"
    preparing = "Preparing"
    trained = "Trained"


class TaskIdSchemas(BaseModel):
    task_id: str
    project_id: Optional[int]
    task_name: str
    task_status: str


class TaskIdsSchemas(BaseModel):
    task_id: str
    project_ids: int
    task_name: str
    task_status: str


class GetTaskResultSchemas(BaseModel):
    task_id: str
    task_status: str
    task_result: Any


class Qualities(str, Enum):
    x1 = "Aerial_HAT-L_SRx1_8985"
    x2 = "Aerial_HAT-L_SRx2_8985"
    x3 = "Aerial_HAT-L_SRx3_8985"
    x4 = "Aerial_HAT-L_SRx4_11980"


class SendSuperResolutionSchemas(BaseModel):
    paths: List[str]
    quality: Qualities = Qualities.x4

    @validator("paths")
    def empty_paths(cls, v: List[str]) -> List[str]:
        if not v:
            raise HTTPException(
                detail="Paths cannot be empty",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("quality", pre=True)
    def empty_quality(cls, v: List[str]) -> List[str]:
        if not v:
            raise HTTPException(
                detail="Quality cannot be empty",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("quality", pre=True)
    def valid_quality(cls, v: str) -> str:
        if v and v not in [i.value for i in Qualities]:
            detail = (
                "Quality is not valid; ",
                "Permitted: ",
                "'Aerial_HAT-L_SRx1_8985', ",
                "'Aerial_HAT-L_SRx2_8985', ",
                "'Aerial_HAT-L_SRx3_8985', ",
                "'Aerial_HAT-L_SRx4_11980'",
            )
            raise HTTPException(
                detail=detail,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v


class SendAerialSchemas(BaseModel):
    paths: List[str]
    save_image_flag: bool = True
    save_json_flag: bool = True

    @validator("paths")
    def empty_paths(cls, v: List[str]) -> List[str]:
        if not v:
            raise HTTPException(
                detail="Paths cannot be empty",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v


class SendDetectionSchemas(BaseModel):
    paths: List[str]
    ml_model: List[str]
    ml_model_deeplab: List[str]
    quality: Qualities = Qualities.x4
    save_image_flag: bool = True
    save_json_flag: bool = True

    @validator("paths")
    def empty_paths(cls, v: List[str]) -> List[str]:
        if not v:
            raise HTTPException(
                detail="Paths cannot be empty",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("quality", pre=True)
    def empty_quality(cls, v: List[str]) -> List[str]:
        if not v:
            raise HTTPException(
                detail="Quality cannot be empty",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("quality", pre=True)
    def valid_quality(cls, v: str) -> str:
        if v and v not in [i.value for i in Qualities]:
            detail = (
                "Quality is not valid; ",
                "Permitted: ",
                "'Aerial_HAT-L_SRx1_8985', ",
                "'Aerial_HAT-L_SRx2_8985', ",
                "'Aerial_HAT-L_SRx3_8985', ",
                "'Aerial_HAT-L_SRx4_11980'",
            )
            raise HTTPException(
                detail=detail,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v


class Send360Schemas(BaseModel):
    paths: List[str]
    ml_model: List[str]
    ml_model_deeplab: List[str]

    @validator("paths")
    def empty_paths(cls, v: List[str]) -> List[str]:
        if not v:
            raise HTTPException(
                detail="Paths cannot be empty",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v


class Result360Schemas(BaseModel):
    image_list: List[str]
    pcd_path: Optional[str]


class CreateMLModelSchemas(BaseModel):
    name: str
    link: str
    type_of_data: TypeMLModelEnum

    @validator("type_of_data", pre=True)
    def valid_type(cls, v: str) -> str:
        if v and v not in [i.value for i in TypeMLModelEnum]:
            raise HTTPException(
                detail=(
                    "Type of ml model is not valid enumeration member; "
                    "permitted: 'Aerial, Satellite', 'Panorama 360'"
                ),
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("name", pre=True)
    def empty_name(cls, v: str) -> str:
        if not v:
            raise HTTPException(
                detail="Name cannot be empty",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v

    @validator("link", pre=True)
    def empty_link(cls, v: str) -> str:
        if not v:
            raise HTTPException(
                detail="Link cannot be empty",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        return v


class MLModelSchemas(BaseModel):
    id: int
    name: str
    type_of_data: List[str]
    type_of_objects: List[str]
    default_model: bool
    task_id: Optional[str]
    task_result: Optional[Dict[str, Any]]
    status: Optional[str]
    created_at: str
    mlflow_url: Optional[str]
    created_by: Optional[str]


class MLModelsSchemas(BaseModel):
    models: List[MLModelSchemas]
    page: int
    pages: int
    total: int
    limit: int


class TrainMLModelSchemas(BaseModel):
    id: int
    type_model: TypeMlModelTrainingEnum
    epochs: int
    scale_factor: Optional[float]
    classes: List[str]


class GetFoldersNextcloudSchemas(BaseModel):
    links: List[str]
