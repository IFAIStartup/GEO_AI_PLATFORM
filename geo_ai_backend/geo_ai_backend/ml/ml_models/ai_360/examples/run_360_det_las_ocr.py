import os
import cv2
import sys
import re
import pickle
import shutil
import numpy as np
import laspy
import glob
import colorsys
import open3d as o3d
from pathlib import Path
import json
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Sequence
from abc import ABC
import fiona
from fiona.crs import CRS
import geopandas as gpd
import earthpy as et
import pyproj
from shapely.geometry import mapping, Point, Polygon, LineString
from scipy import stats
import random
import matplotlib.pyplot as plt
import tritonclient.http as httpclient

from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.config import (
    Config
)
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.object_localization_be_ocr import (
    get_pcd_localization_ocr
)

from geo_ai_backend.ml.ml_models.ai_360.inference.triton_inference import (
    check_save_dir,
    get_360_images,
    DEFAULT_CLASS_NAMES_YOLO,
    DEFAULT_CLASS_NAMES_DEEPLAB,
)
from geo_ai_backend.ml.ml_models.utils.model_info import (
    ModelInfo,
    ModelTypeEnum,
)


COCO_CLASS_NAMES_YOLO = list({
    0: 'person',
    1: 'bicycle',
    2: 'car',
    3: 'motorcycle',
    4: 'airplane',
    5: 'bus',
    6: 'train',
    7: 'truck',
    8: 'boat',
    9: 'traffic light',
    10: 'fire hydrant',
    11: 'stop sign',
    12: 'parking meter',
    13: 'bench',
    14: 'bird',
    15: 'cat',
    16: 'dog',
    17: 'horse',
    18: 'sheep',
    19: 'cow',
    20: 'elephant',
    21: 'bear',
    22: 'zebra',
    23: 'giraffe',
    24: 'backpack',
    25: 'umbrella',
    26: 'handbag',
    27: 'tie',
    28: 'suitcase',
    29: 'frisbee',
    30: 'skis',
    31: 'snowboard',
    32: 'sports ball',
    33: 'kite',
    34: 'baseball bat',
    35: 'baseball glove',
    36: 'skateboard',
    37: 'surfboard',
    38: 'tennis racket',
    39: 'bottle',
    40: 'wine glass',
    41: 'cup',
    42: 'fork',
    43: 'knife',
    44: 'spoon',
    45: 'bowl',
    46: 'banana',
    47: 'apple',
    48: 'sandwich',
    49: 'orange',
    50: 'broccoli',
    51: 'carrot',
    52: 'hot dog',
    53: 'pizza',
    54: 'donut',
    55: 'cake',
    56: 'chair',
    57: 'couch',
    58: 'potted plant',
    59: 'bed',
    60: 'dining table',
    61: 'toilet',
    62: 'tv',
    63: 'laptop',
    64: 'mouse',
    65: 'remote',
    66: 'keyboard',
    67: 'cell phone',
    68: 'microwave',
    69: 'oven',
    70: 'toaster',
    71: 'sink',
    72: 'refrigerator',
    73: 'book',
    74: 'clock',
    75: 'vase',
    76: 'scissors',
    77: 'teddy bear',
    78: 'hair drier',
    79: 'toothbrush',
}.values())


def main():

    img_path_template = os.path.join(os.path.dirname(__file__), '../360_scenes/1/*.jpg')
    img_paths = glob.glob(img_path_template)

    save_dir = check_save_dir(os.path.join(os.path.dirname(__file__), '..', 'outs/360_las_ocr'))
    save_pcd_path = os.path.join(save_dir, 'result.pcd')
    save_shp_path = os.path.join(save_dir, 'result_shp')
    print(f"Result will be saved in {save_dir}")

    triton_url = "localhost:8000"
    client = httpclient.InferenceServerClient(url=triton_url)

    yolo_model_info = ModelInfo(
        model_name='yolov8n',
        model_type=ModelTypeEnum.yolov_det,
        class_names=list(COCO_CLASS_NAMES_YOLO),
        tile_size=640,
        scale_factor=0.3125,   # 640 / 2048
    )

    model_info_list = [yolo_model_info]

    cfg = Config()
    cfg.classes_pcd = COCO_CLASS_NAMES_YOLO
    get_pcd_localization_ocr(
        img_paths,
        model_info_list,
        client,
        save_pcd_path,
        save_shp_path,
        cfg,
    )


if __name__ == '__main__':
    main()
