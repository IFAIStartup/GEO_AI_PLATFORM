import numpy as np
from typing import List
import tritonclient.http as httpclient
from geo_ai_backend.ml.ml_models.utils.inference_models import (
    InferenceModel
)
from geo_ai_backend.ml.ml_models.utils.model_info import (
    ModelInfo,
    ModelTypeEnum,
)
from geo_ai_backend.ml.ml_models.utils.inference_models import (
    YOLOv8segModel,
    YOLOv8detModel,
    DeepLabv3Model,
)
from geo_ai_backend.ml.ml_models.utils.model_sets import (
    ModelSet
)


def create_model_sets(
        model_info_list: List[ModelInfo],
        relative_overlap: float = 0) -> List[ModelSet]:

    scales = {}

    for model_info in model_info_list:
        model_name = model_info.model_name
        model_type = model_info.model_type
        class_names = model_info.class_names
        tile_size = model_info.tile_size
        scale_factor = model_info.scale_factor

        imgsz = (tile_size, tile_size)

        # TODO: change dict to list
        class_names_dict = {i: c for i, c in enumerate(class_names)}

        if model_type == ModelTypeEnum.yolov8:
            model = YOLOv8segModel(model_name, class_names_dict, imgsz)
        elif model_type == ModelTypeEnum.yolov_det:
            model = YOLOv8detModel(model_name, class_names_dict, imgsz)
        else:   # ModelTypeEnum.deeplabv3
            model = DeepLabv3Model(model_name, class_names_dict, imgsz)

        key = f"{scale_factor}_{tile_size}"
        if key not in scales:
            overlap = int(tile_size * relative_overlap)
            scales[key] = ModelSet([], scale_factor, tile_size, overlap)

        scales[key].inference_models.append(model)

    model_sets = []
    for scale_factor in scales:
        model_sets.append(scales[scale_factor])

    return model_sets


def filter_predictions_by_classes(
        predictions: List[dict],
        class_names_common: List[str]):

    filtered_predictions = []

    for prediction in predictions:
        class_name = prediction['class']
        key_idx = list(class_names_common.values()).index(class_name)
        if key_idx == -1:
            continue

        class_idx = list(class_names_common.keys())[key_idx]
        prediction['class'] = class_idx
        filtered_predictions.append(prediction)

    return filtered_predictions


def inference_pipeline(
        img_in: np.ndarray,
        class_names_common: dict,
        imgsz: tuple,
        overlap: int,
        inference_models: List[InferenceModel],
        client: httpclient.InferenceServerClient) -> List[List[np.ndarray]]:

    # TODO: change docs
    """ Do model inference with preprocessing and postprocessing

    :param img_in: rgb image with arbitrary height and width (with shape (H0, W0, 3))
    :param classes: dict of matched ids and class names ({0: cls_name0, 1: cls_name1, ...})
    :param model_name: specific name of the model in model repository
    :param client: _description_

    :return: List of one list of 2 arrays: detections (N, 6) and masks (N, H0, W0)
    """

    segments_with_classes = []
    for model in inference_models:
        result = model(img_in, client, overlap)
        segments_with_classes += result

    segments_with_classes = filter_predictions_by_classes(
        segments_with_classes,
        class_names_common
    )
    return segments_with_classes


def get_tiles_meta(
        tiles: list,
        class_names_common: dict,
        tile_size: int,
        overlap: int,
        inference_models: List[InferenceModel],
        client: httpclient.InferenceServerClient) -> list:

    tiles_meta = []
    for tile_num, tile in enumerate(tiles):
        results = inference_pipeline(
            tile,
            class_names_common,
            (tile_size, tile_size),
            overlap,
            inference_models,
            client
        )
        tiles_meta.append(results)

    return tiles_meta


def add_padding(image: np.ndarray, tile_size: int, overlap: int) -> np.ndarray:
    h, w = image.shape[:2]

    top_pad = overlap
    left_pad = overlap

    tile_size_once_truncated = tile_size - overlap
    tile_size_twice_truncated = tile_size - 2 * overlap

    bottom_pad = overlap + h % tile_size_twice_truncated
    right_pad = overlap + w % tile_size_twice_truncated

    pad_width = ((top_pad, bottom_pad), (left_pad, right_pad), (0, 0))
    padded_image = np.pad(image, pad_width)
    return padded_image


def get_tiles(image: np.ndarray, tile_size: int, overlap: int) -> list:
    """
    Split image into tiles with overlap.
    :param image: image to split
    :param tile_size: size of tile
    :param overlap: overlap between tiles
    :return: list of tiles
    """
    tiles = []
    h, w = image.shape[:2]
    for i in range(0, h - tile_size + 1, tile_size - overlap * 2):
        for j in range(0, w - tile_size + 1, tile_size - overlap * 2):
            tile = image[i:i + tile_size, j:j + tile_size]
            tiles.append(tile)
    return tiles

