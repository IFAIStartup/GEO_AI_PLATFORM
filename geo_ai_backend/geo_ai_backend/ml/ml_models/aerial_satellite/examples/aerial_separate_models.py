import os
import cv2
import tritonclient.http as httpclient
from geo_ai_backend.ml.ml_models.aerial_satellite.inference.utils import check_save_dir
from geo_ai_backend.ml.ml_models.aerial_satellite.inference.triton_inference import (
    DEFAULT_CLASS_NAMES_YOLO,
    DEFAULT_CLASS_NAMES_DEEPLAB,
    get_aerial_satellite_image,
    ModelInfo,
    ModelTypeEnum,
)


def main():
    img_path = os.path.join(os.path.dirname(__file__), '..', 'inputs', '3768.tif')
    save_dir = os.path.join(os.path.dirname(__file__), '..', 'outs')
    img_name = os.path.splitext(os.path.basename(img_path))[0]
    
    save_image_flag = True
    save_json_flag = True
    save_dir = check_save_dir(os.path.join(save_dir, img_name))
    print(f"Result will be saved in {save_dir}")

    # Setting up client
    url = 'localhost:8000'
    triton_client = httpclient.InferenceServerClient(url=url)

    yolo1_model_info = ModelInfo(
        model_name='aerial_building',
        model_type=ModelTypeEnum.yolov8,
        class_names=['buildings'],
        tile_size=1280,
        scale_factor=0.5,
    )
    yolo2_model_info = ModelInfo(
        model_name='aerial_trees',
        model_type=ModelTypeEnum.yolov8,
        class_names=['trees'],
        tile_size=1280,
        scale_factor=1,
    )
    yolo3_model_info = ModelInfo(
        model_name='aerial_palm_tree',
        model_type=ModelTypeEnum.yolov8,
        class_names=['palm_tree'],
        tile_size=640,
        scale_factor=0.5,
    )
    deeplab_model_info = ModelInfo(
        model_name='aerial_deeplabv3_plus_26012024',
        model_type=ModelTypeEnum.deeplabv3,
        class_names=DEFAULT_CLASS_NAMES_DEEPLAB,
        tile_size=640,
        scale_factor=0.625,
    )

    model_info_list = [yolo1_model_info, yolo2_model_info, yolo3_model_info, deeplab_model_info]
    
    get_aerial_satellite_image(
        triton_client,
        model_info_list,
        img_path,
        save_dir,
        save_image_flag,
        save_json_flag,
    )


if __name__ == '__main__':
    main()
