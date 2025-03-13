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
    model_yolo_name = 'yolov8x_aerial_base'
    model_seg_name = 'aerial_deeplabv3_plus_26012024'

    img_path = os.path.join(os.path.dirname(__file__), '..', 'inputs', '3768.tif')
    save_dir = os.path.join(os.path.dirname(__file__), '..', 'outs')
    img_name = os.path.splitext(os.path.basename(img_path))[0]
    
    save_image_flag = True
    save_json_flag = True
    save_dir = check_save_dir(os.path.join(save_dir, img_name))

    print(f"Result will be saved in {save_dir}")
    url = 'localhost:8000'

    # Setting up client
    triton_client = httpclient.InferenceServerClient(url=url)

    # yolo_model_info = ModelInfo(
    #     model_name=model_yolo_name,
    #     model_type=ModelTypeEnum.yolov8,
    #     class_names=DEFAULT_CLASS_NAMES_YOLO,
    #     tile_size=1024,
    #     scale_factor=1,
    # )
    # deeplab_model_info = ModelInfo(
    #     model_name=model_seg_name,
    #     model_type=ModelTypeEnum.deeplabv3,
    #     class_names=DEFAULT_CLASS_NAMES_DEEPLAB,
    #     tile_size=1024,
    #     scale_factor=1,
    # )

    yolo1_model_info = ModelInfo(
        model_name='aerial_building',
        model_type=ModelTypeEnum.yolov8,
        class_names=['buildings'],
        tile_size=1280,
        scale_factor=1,
    )
    yolo2_model_info = ModelInfo(
        model_name='aerial_palm_tree',
        model_type=ModelTypeEnum.yolov8,
        class_names=['palm_tree'],
        tile_size=640,
        scale_factor=1,
    )
    deeplab_model_info = ModelInfo(
        model_name='aerial_deeplabv3_plus_26012024',
        model_type=ModelTypeEnum.deeplabv3,
        class_names=DEFAULT_CLASS_NAMES_DEEPLAB,
        tile_size=640,
        scale_factor=(640 / 1024),
    )

    model_info_list = [yolo1_model_info, yolo2_model_info, deeplab_model_info]
    # model_info_list = [yolo_model_info, deeplab_model_info]
    # model_info_list = [deeplab_model_info]
    
    get_aerial_satellite_image(
        triton_client,
        model_info_list,
        img_path,
        save_dir,
        save_image_flag,
        save_json_flag,
    )

    create_jpg_image(os.path.join(save_dir, img_name + '.png'))


def create_jpg_image(image_path: str):
    if os.path.exists(image_path):
        img = cv2.imread(image_path)
        cv2.imwrite(image_path.replace('.png', '.jpg'), img)


if __name__ == '__main__':
    main()
