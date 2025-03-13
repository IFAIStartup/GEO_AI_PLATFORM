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


def main():
    model_yolo_name = 'yolov8x_seg_360_1280_dataset_080123'
    model_seg_name = 'buildings360_r50_250923'

    img_path_template = os.path.join(os.path.dirname(__file__), '../360_scenes/1/*.jpg')
    img_paths = glob.glob(img_path_template)

    save_dir = check_save_dir(os.path.join(os.path.dirname(__file__), '..', 'outs/360_las_ocr'))
    save_pcd_path = os.path.join(save_dir, 'result.pcd')
    save_shp_path = os.path.join(save_dir, 'result_shp')
    print(f"Result will be saved in {save_dir}")
    
    triton_url = "localhost:8000"
    client = httpclient.InferenceServerClient(url=triton_url)

    yolo_model_info = ModelInfo(
        model_name=model_yolo_name,
        model_type=ModelTypeEnum.yolov8,
        class_names=DEFAULT_CLASS_NAMES_YOLO,
        tile_size=1280,
        scale_factor=0.625,     # 1280 / 2048
    )
    deeplab_model_info = ModelInfo(
        model_name=model_seg_name,
        model_type=ModelTypeEnum.deeplabv3,
        class_names=DEFAULT_CLASS_NAMES_DEEPLAB,
        tile_size=640,
        scale_factor=0.3125,   # 640 / 2048
    )

    model_info_list = [yolo_model_info, deeplab_model_info]

    cfg = Config()
    get_pcd_localization_ocr(
        img_paths, 
        model_info_list, 
        client, 
        save_pcd_path, 
        save_shp_path, 
        cfg
    )


if __name__ == '__main__':
    main()
