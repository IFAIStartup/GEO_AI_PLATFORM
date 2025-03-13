from typing import List
from enum import Enum
from pydantic import BaseModel


class ModelTypeEnum(str, Enum):
    yolov8 = "yolov8"
    yolov_det = "yolov8_det"
    deeplabv3 = "deeplabv3"


class ModelInfo(BaseModel):
    """Structure that contains information about neural network model
    that is supposed to be used while inferencing
    """
    model_name: str             # Model name in triton inference server
    model_type: ModelTypeEnum   # Type of the model, which influences on how to handle it
    class_names: List[str]  # Class names, that model has after training
    tile_size: int          # Size of input image, that model has after training

    scale_factor: float     # Scale factor for tile size, which means that, actually,
                            # an image with size `tile_size / scale_factor` will be used
                            # and resized to appropriate tile size

    used_class_names: List[str] or None = None   # Class names, that will be used while inferencing.
                                                # Names, that are not in "class_names", will be ignored
                                                # If it is None, then it equals to "class_names" field

