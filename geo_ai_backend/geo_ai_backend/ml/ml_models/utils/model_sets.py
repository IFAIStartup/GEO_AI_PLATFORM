from dataclasses import dataclass
from typing import List, Dict
from geo_ai_backend.ml.ml_models.utils.inference_models import (
    InferenceModel,
    YOLOv8segModel, 
    DeepLabv3Model,
)


@dataclass
class ModelSet:
    inference_models: List[InferenceModel]
    scale_factor: float 
    tile_size: int 
    overlap: int
