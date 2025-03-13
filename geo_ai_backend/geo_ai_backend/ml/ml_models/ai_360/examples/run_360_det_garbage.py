import os
import cv2
import pandas as pd
import tritonclient.http as httpclient
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

GARBAGE_CLASSES = [
    'household_garbage',
    'construction_garbage',
    'natural_garbage',
    'furniture_garbage',
    'others',
]



def main():

    img_path = os.path.join(os.path.dirname(__file__), '..', '360_scenes/1/Unnamed Run  1_Camera 4 360_0_1.jpg')
    res_save_path = os.path.join(os.path.dirname(__file__), '..', 'outs')

    url = 'localhost:8000'

    img_name = os.path.splitext(os.path.basename(img_path))[0]
    save_dir = check_save_dir(os.path.join(res_save_path, img_name))
    client = httpclient.InferenceServerClient(url=url)
    print(f"Result will be saved in {save_dir}")

    yolo_model_info = ModelInfo(
        model_name='yolov8s_garbage_29102023',
        model_type=ModelTypeEnum.yolov_det,
        class_names=GARBAGE_CLASSES,
        tile_size=640,
        scale_factor=0, # 0.3125, # 640 / 2048
    )

    model_info_list = [yolo_model_info]

    status_image = get_360_images(
        client,
        model_info_list,
        img_path,
        save_dir,
    )


if __name__ == '__main__':
    main()
