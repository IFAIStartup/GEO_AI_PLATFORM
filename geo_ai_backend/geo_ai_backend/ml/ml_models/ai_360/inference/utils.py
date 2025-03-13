import os
import argparse
import cv2
import numpy as np
import albumentations as A
# from geo_ai_backend.ml.ml_models.ai_360.inference.classes_config import class_names


colors_palette = [
    [255, 0, 0],
    [255, 165, 0],
    [255, 255, 0],
    [127, 255, 0],
    [0, 128, 0],
    [0, 255, 127],
    [0, 255, 255],
    [0, 127, 255],
    [0, 0, 255],
    [127, 0, 255],
    [255, 0, 255],
    [255, 0, 127],
    [255, 255, 255],
    [128, 128, 128],
    [0, 0, 0],
    [165, 42, 42],
    [245, 245, 220],
    [210, 180, 140],
    [128, 128, 0],
    [128, 0, 0],
    [0, 0, 128],
    [127, 255, 212],
    [64, 224, 208],
    [192, 192, 192],
    [191, 255, 0],
    [0, 128, 128],
    [75, 0, 130],
    [255, 192, 203],
    [255, 218, 185]
]


def check_save_dir(save_dir: str) -> str:
    """
    Check if save directory exists, if not, create it.
    :param save_dir: path to save directory
    :return: None
    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        return save_dir

    else:
        for i in range(1, 9999):
            if not os.path.exists(save_dir + '_' + str(i)):
                save_dir = save_dir + '_' + str(i)
                os.makedirs(save_dir)
                return save_dir


def add_padding(image: np.ndarray, tile_size: int, overlap: int) -> np.ndarray:
    h, w = image.shape[:2]

    h_pad = 0
    w_pad = 0
    if h % (tile_size - overlap) != 0:
        h_pad = (tile_size - overlap) - (h % (tile_size - overlap))

    if w % (tile_size - overlap) != 0:
        w_pad = (tile_size - overlap) - (w % (tile_size - overlap))

    transform = A.Compose([
        A.PadIfNeeded(min_height=h + h_pad, min_width=w + w_pad, border_mode=cv2.BORDER_CONSTANT, value=0)
    ])

    image = transform(image=image)['image']

    return image


def draw_segment_results(img: np.ndarray, objects_info, class_names) -> np.ndarray:
    vis_img = img.copy()
    color_masks = {}
    # for i in range(objects_info):
    for obj_info in objects_info:

        class_id = obj_info['class']
        color = colors_palette[class_id % len(colors_palette)]

        segments = obj_info['segment']

        bbox = cv2.boundingRect(segments.astype('int32'))
        x1, y1, w, h = bbox
        x2, y2 = x1 + w, y1 + h

        class_name = class_names[class_id]

        if class_name not in color_masks:
            color_masks[class_name] = np.zeros(img.shape, dtype='uint8')

        if segments.shape[0] != 0:
            cv2.fillPoly(color_masks[class_name], [segments.astype('int32')], color)

        vis_img = cv2.rectangle(vis_img, (x1, y1), (x2, y2), color, 2)

        label = f'{class_name}'
        ((text_width, text_height), _) = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX,
                                                         0.6, 1)
        cv2.rectangle(vis_img, (x1, y1), (x1 + text_width, y1 + text_height), color, -1)
        cv2.putText(vis_img, text=label, org=(x1, y1 + int(0.8 * text_height)),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5,
                    color=(255, 255, 255),
                    lineType=cv2.LINE_AA)

    for class_name in color_masks:
        vis_img = cv2.addWeighted(vis_img, 1, color_masks[class_name], 0.3, 0)

    return vis_img


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--model_yolo", type=str, default='yolov8x_seg_360_1280_dataset_260923')
    parser.add_argument("--model_seg", type=str, default='buildings360_r50_250923')
    parser.add_argument("--src_img", type=str, default='./inference/images/trees.jpg')
    parser.add_argument("--dst", type=str, default='./outs')
    parser.add_argument("--save_image", type=bool, default=True)
    parser.add_argument("--save_json", type=bool, default=True)
    parser.add_argument("--url", type=str, default=r"localhost:8000")

    args = parser.parse_args()
    return args
