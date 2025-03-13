import os
import cv2
import numpy as np
import albumentations as A


colors_palette = [[255, 128, 0], [255, 153, 51], [255, 178, 102], [230, 230, 0], [255, 153, 255],
                  [153, 204, 255], [255, 102, 255], [255, 51, 255], [102, 178, 255], [51, 153, 255],
                  [255, 153, 153], [255, 102, 102], [255, 51, 51], [153, 255, 153], [102, 255, 102],
                  [51, 255, 51], [0, 255, 0], [0, 0, 255], [255, 0, 0], [255, 255, 255]]


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

    top_pad = overlap
    left_pad = overlap

    tile_size_once_truncated = tile_size - overlap
    tile_size_twice_truncated = tile_size - 2 * overlap

    bottom_pad = overlap + h % tile_size_twice_truncated
    right_pad = overlap + w % tile_size_twice_truncated
    
    pad_width = ((top_pad, bottom_pad), (left_pad, right_pad), (0, 0))
    padded_image = np.pad(image, pad_width)
    return padded_image


def draw_segment_results_scene(img: np.ndarray, objects_info) -> np.ndarray:
    vis_img = img.copy()

    # for i in range(objects_info):
    color_masks = {}
    for obj_info in objects_info:
        x1, y1, x2, y2, = obj_info['bbox']

        class_name = obj_info['class_name']
        class_id = obj_info['class_id']

        if class_name not in color_masks:
            color_masks[class_name] = np.zeros(img.shape, dtype='uint8')

        color = colors_palette[class_id]
        #color_mask = np.zeros(img.shape, dtype='uint8')

        segments = []
        if obj_info['coordinates']['exterior'].shape[0] != 0:
            segments.append(obj_info['coordinates']['exterior'].astype('int32'))

        for cnt in obj_info['coordinates']['interior']:
            if len(cnt) > 0:
                segments.append(np.array(cnt).astype('int32'))

        if len(segments) > 0:
            cv2.fillPoly(color_masks[class_name], segments, color)

        vis_img = cv2.rectangle(vis_img, (x1, y1), (x2, y2), color, 2)

        # Draw label for bounding box
        label = f'{class_name}'

        ((text_width, text_height), _) = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(vis_img, (x1, y1), (x1 + text_width, y1 + text_height), color, -1)
        cv2.putText(vis_img, text=label, org=(x1, y1 + int(0.8 * text_height)),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=(255, 255, 255),
                    lineType=cv2.LINE_AA)

    for class_name in color_masks:
        vis_img = cv2.addWeighted(vis_img, 1, color_masks[class_name], 0.3, 0)

    return vis_img
