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

    img_path = os.path.join(os.path.dirname(__file__), '..', '360_scenes/1/Unnamed Run  1_Camera 4 360_64_0.jpg')
    res_save_path = os.path.join(os.path.dirname(__file__), '..', 'outs')

    url = 'localhost:8000'

    img_name = os.path.splitext(os.path.basename(img_path))[0]
    save_dir = check_save_dir(os.path.join(res_save_path, img_name))
    client = httpclient.InferenceServerClient(url=url)
    print(f"Result will be saved in {save_dir}")

    yolo_model_info = ModelInfo(
        model_name='yolov8n',
        model_type=ModelTypeEnum.yolov_det,
        class_names=list(COCO_CLASS_NAMES_YOLO),
        tile_size=640,
        scale_factor=0.3125,   # 640 / 2048
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
