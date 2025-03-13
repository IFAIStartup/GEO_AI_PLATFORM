from PIL import ImageFont, ImageDraw, Image
import os
import cv2
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import pyproj
import albumentations as A
from typing import Tuple, List, Dict, Union
# from ultralytics import YOLO
import arabic_reshaper
from bidi.algorithm import get_display
from pathlib import Path
from geo_ai_backend.ml.ml_models.ocr.geo_ai_ocr.signboard import SignBoard
from geo_ai_backend.ml.ml_models.ocr.geo_ai_ocr.cropinfo import CropInfo


def create_signboards_list(images_list: list, point_cloud: bool = True) -> list:
    """
    Create a list of every signboard from list of images with crops info
    """

    signboards_list = []
    signboard_id = 0
    for signboard_img in images_list:
        cluster_id = signboard_img.cluster_id
        if not point_cloud:
            signboard = SignBoard(signboard_id)

            signboard.add_crop(signboard_img)
            signboards_list.append(signboard)
            signboard_id += 1
            continue

        if cluster_id is None:
            continue

        # distribute all crops by signboards
        signboard_found = False
        for signboard in signboards_list:
            # check if signboard with the same id already exists
            if str(signboard.signboard_id) == cluster_id:
                signboard.add_crop(signboard_img)
                signboard_found = True
                break

        # if signboard with the same id does not exist, create a new one
        if not signboard_found:
            signboard = SignBoard(signboard_img.cluster_id)

            signboard.add_crop(signboard_img)
            signboards_list.append(signboard)
            # signboard_id += 1

    return signboards_list


def get_clusters_centers(clusters: dict, points: np.ndarray) -> dict:
    """
    Get center points of clusters
    """

    clusters_centers = {}
    for cluster_id in clusters:
        if cluster_id == '-1':
            continue
        cluster_points = clusters[cluster_id]
        target_points = points[cluster_points]
        clusters_centers[cluster_id] = np.array(
            [target_points[:, 0].mean(), target_points[:, 1].mean(), target_points[:, 2].mean()])

    return clusters_centers


def connect_signboards_to_clusters(crops_list: List[CropInfo], clusters_centers: dict):
    """
    Connect signboards to clusters by center distance
    """

    # create a list of clusters by distance to the signboard
    for img_info in crops_list:
        if img_info.center is None:
            continue
        cluster_dist = {}

        for cluster_id in clusters_centers:
            cluster_center = clusters_centers[cluster_id]
            dist = np.linalg.norm(np.array(cluster_center) - img_info.center)
            cluster_dist[cluster_id] = dist

        sorted_cluster_dist = {k: v for k, v in sorted(cluster_dist.items(), key=lambda item: item[1])}
        sorted_cluster_dist_keys = list(sorted_cluster_dist.keys())

        img_info.cluster_dist = sorted_cluster_dist_keys
        img_info.cluster_id = None if len(sorted_cluster_dist_keys) == 0 else sorted_cluster_dist_keys[0]


# def remove_outliers(signboards_list: list, threshold: float = 0.4):
#     """
#     Remove outliers from signboards list using magface
#     """
#     # compare all crops of each signboard and remove outliers
#     for signboard in signboards_list:
#         embeddings = [crop.embedding for crop in signboard.crops_info]
#         model_outliers = IsolationForest()
#         model_outliers.fit(embeddings)
#         outliers = model_outliers.predict(embeddings)
#         outlier_indices = np.where(outliers == -1)[0]
#
#         for outlier_index in sorted(outlier_indices, reverse=True):
#             # remove outlier from signboard
#             signboard.crops_info.pop(outlier_index)


def get_gis_positions(points: np.ndarray, centers: np.ndarray) -> List[List[float]]:
    centers_xy = centers[:, 0:2]
    centers_xy_pt = [Point(xy) for xy in centers_xy]

    wkt = 'PROJCS["40 North",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["World Geodetic System 1984",6378137,298.257223563],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["Degree",0.01745329251994,AUTHORITY["EPSG","9102"]],AXIS["Long",EAST],AXIS["Lat",NORTH],AUTHORITY["EPSG","4326"]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000],PARAMETER["False_Northing",0],PARAMETER["Latitude_Of_Origin",0],PARAMETER["Central_Meridian",57],PARAMETER["Scale_Factor",0.9996],UNIT["Meter",1,AUTHORITY["EPSG","9001"]],AXIS["East",EAST],AXIS["North",NORTH]]'
    centers_loc = gpd.GeoDataFrame(centers_xy_pt,
                                   columns=['geometry'],
                                   crs=pyproj.CRS.from_wkt(wkt))

    centers_loc = centers_loc.to_crs(crs=pyproj.CRS.from_epsg(4326))
    centers_gis = [[pt.y, pt.x] for pt in centers_loc['geometry']]

    return centers_gis


def draw_result(img: np.ndarray, bbox: list, all_text: list) -> np.ndarray:
    """
    Draw bbox and text on image
    :param img: image
    :param bbox: bbox
    :param all_text: list of text to draw on image
    :return: image with bbox and text
    """
    res_img = img.copy()

    transform = A.Compose([
        A.LongestMaxSize(max_size=1080, always_apply=True),
        A.PadIfNeeded(min_height=1080, min_width=1920, border_mode=cv2.BORDER_CONSTANT, value=[0, 0, 0],
                      always_apply=True),
    ], bbox_params=A.BboxParams(format='pascal_voc', label_fields=['category']))

    # res_trans = transform(image=res_img, bboxes=[bbox], category=[0])
    #
    # res_img = res_trans['image']
    # bbox = res_trans['bboxes'][0]
    # bbox = [int(x) for x in bbox]

    # scale_x = res_img.shape[0] / img.shape[0]
    # scale_y = res_img.shape[0] / img.shape[0]
    #
    # shift_x = ((img.shape[1] - res_img.shape[1]) // 2) * scale_x
    # shift_y = ((img.shape[0] - res_img.shape[0]) // 2) * scale_y

    x1, y1, x2, y2 = bbox

    # x1, y1, x2, y2 = (int(x1 * scale_x), int(y1 * scale_y), int(x2 * scale_x), int(y2 * scale_y))
    #
    # x1 += shift_x
    # x2 += shift_x
    # y1 += shift_y
    # y2 += shift_y

    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    res_img = cv2.rectangle(res_img, (x1, y1), (x2, y2), (0, 0, 255), 3)

    fontpath = '/usr/share/fonts/truetype/freefont/FreeMono.ttf' # "arial.ttf"
    font = ImageFont.truetype(fontpath, 38)

    img_pil = Image.fromarray(res_img)

    # new_size = (1920, 1080)
    #
    # img_pil = img_pil.resize(new_size)

    # create a new img size as 16:9
    # if img_pil.size[0] == 2048:
    #     new_size = (int(img_pil.size[0] / 9 * 16), img_pil.size[0])
    # else:
    #     new_size = (img_pil.size[0], img_pil.size[0])

    # new_size = (int(img_pil.size[0] / 9 * 16), img_pil.size[0])
    # x_shift = (img[0] - img_pil.size[0]) // 2
    # x1 += x_shift
    # x2 += x_shift
    #
    # img_pil = add_padding(img_pil, new_size)

    draw = ImageDraw.Draw(img_pil)

    text_margin = 0
    for text in reversed(all_text):
        if 'Text' in text:
            font_text = ImageFont.truetype(fontpath, 48)
            left, top, right, bottom = font_text.getbbox(text)  # draw.textsize(text, font=font_text)
            text_w, text_h = right - left, bottom - top
            text_margin += text_h + 10
            text_position = (x1, y1 - text_margin)
            draw.rectangle(
                (text_position[0], text_position[1] - 3, text_position[0] + text_w, text_position[1] + 3 + text_h),
                fill=(255, 255, 255))

            draw.text(text_position, text, font=font_text, fill=(89, 34, 0))
            draw.rectangle(
                (text_position[0], text_position[1] - 3, text_position[0] + text_w, text_position[1] + 3 + text_h),
                outline='red', width=2)

            continue

        left, top, right, bottom = font_text.getbbox(text)  # draw.textsize(text, font=font_text)
        text_w, text_h = right - left, bottom - top

        # text_w, text_h = draw.textsize(text, font=font)

        text_margin += text_h + 10
        text_position = (x1, y1 - text_margin)
        draw.rectangle(
            (text_position[0], text_position[1] - 3, text_position[0] + text_w, text_position[1] + 3 + text_h),
            fill=(255, 255, 255))
        draw.text(text_position, text, font=font, fill=(0, 0, 0))

    # downscale image
    # img_pil = img_pil.resize((img_pil.size[0] // 2, img_pil.size[1] // 2), Image.ANTIALIAS)

    res_img = np.array(img_pil)

    return res_img


def get_json_data(signboards_list: list, ) -> dict:
    """
    Save jsons
    :param signboards_list: list of signboards
    :return:
    """

    all_signboards_info = []
    for signboard in signboards_list:
        json_info = {}
        json_info['signboard_id'] = signboard.signboard_id
        json_info['best_img_name'] = signboard.best_img_name
        json_info['title'] = signboard.title
        json_info['geo_coords'] = signboard.geo_coords

        json_info['best_crop_text_bboxes'] = []
        for text_bbox in signboard.best_crop_text_bboxes:
            bbox = [int(x) for x in text_bbox['bbox']]
            json_info['best_crop_text_bboxes'].append(
                {'bbox': bbox, 'lang': text_bbox['lang'], 'text': text_bbox['text']})

        json_info['crops_info'] = []
        for crop_info in signboard.crops_info:
            center = [float(x) for x in crop_info.center] if crop_info.center is not None else None
            bbox = [int(x) for x in crop_info.bbox]
            json_info['crops_info'].append({
                'img_name': crop_info.img_name,
                'cluster_id': crop_info.cluster_id if crop_info.cluster_id is not None else None,
                'distance': float(crop_info.distance) if crop_info.distance is not None else None,
                'center': center,
                'bbox': bbox,
                'iou': float(crop_info.iou) if crop_info.iou is not None else None,
                'angle': float(crop_info.angle) if crop_info.angle is not None else None
            })

        all_signboards_info.append(json_info)

    return all_signboards_info


def get_detections(
        imgs_list: List[Dict],
        imgs_paths: Path,
        # model: YOLO,
        model,
        classes: List = None
) -> Dict:
    """
    Get detections for images
    """
    detections_dict = {}

    for img_data in imgs_list:
        img_name = img_data['img_name']
        img_path = imgs_paths / img_name

        result = model(img_path, classes=classes, conf=0.25)[0]

        if result.masks is None:
            continue

        boxes_n = result.boxes.xyxyn.cpu().numpy()
        boxes = result.boxes.xyxy.cpu().numpy().astype(np.int32)
        masks = result.masks.xyn
        class_ids = result.boxes.cls.cpu().numpy()

        detects = []
        for i in range(len(masks)):
            bbox = boxes[i]
            bbox_n = boxes_n[i]
            class_id = class_ids[i]
            segments = masks[i]

            detects.append({
                'bbox': bbox,
                'bbox_n': bbox_n,
                'class_id': class_id,
                'segments': segments,
                'img_data': img_data,
            })

        detections_dict[img_name] = detects

    return detections_dict


# def get_embeddings(crops_list, magface_model) -> Dict[str, Dict[str, torch.Tensor]]:
#     """
#     Get detections for images
#     """
#
#     for crop_info in crops_list:
#         img_name = crop_info.img_data['img_name']
#
#         img = cv2.imread(os.path.join(SRC_DIR, img_name))
#
#         bbox = crop_info.bbox
#         x1, y1, x2, y2 = bbox
#
#         crop = img[y1:y2, x1:x2]
#
#         crop_t = magface_inference.preproc(crop)
#
#         emb = magface_model(crop_t).detach().numpy()
#         emb = list(emb[0])
#         crop_info.embedding = emb
#
#         crop_info.set_quality()
#
#     return crops_list


def get_images_list(src_dir: Union[Path, str], template: str = None, imgs_range: Tuple[int, int] = None) -> List[Dict]:
    """
    Get list of images
    """
    src_dir = Path(src_dir)
    src_list = os.listdir(src_dir)
    imgs_list = []

    if imgs_range is None:
        imgs_range = (0, len(src_list))

    if template is None:
        for i in range(imgs_range[0], imgs_range[1]):
            img_name = src_list[i]
            img_size = cv2.imread(str(src_dir / img_name)).shape[:2]
            img_data = {
                'img_name': img_name,
                'img_size': img_size,
            }
            imgs_list.append(img_data)
        return imgs_list

    for i in range(imgs_range[0], imgs_range[1]):
        pov_name = template.format(i)

        for j in range(4):
            img_name = f'{pov_name}_{(j + 2) % 4}.jpg'
            img_size = cv2.imread(str(src_dir / img_name)).shape[:2]
            img_data = {
                'img_name': img_name,
                'img_size': img_size,
                'num': i,
                'proj': j,
            }
            imgs_list.append(img_data)

    return imgs_list


def get_crops_list(detections_dict: Dict) -> List[CropInfo]:
    crops_list = []

    for img_name, detects in detections_dict.items():
        for detect in detects:
            bbox = detect['bbox']
            class_id = detect['class_id']
            segments = detect['segments']
            img_data = detect['img_data']

            if class_id == 0:
                crop = CropInfo(img_data, bbox, segments)
                crops_list.append(crop)

    return crops_list


def get_text(signboards, models_, img_dir):
    reader_detection = models_.easyocr_detection_model
    reader_english = models_.easyocr_english_model
    reader_arabic = models_.easyocr_arabic_model
    model_class_lang = models_.classification_language_model
    model_class_quality = models_.classification_quality_model

    for i, signboard in enumerate(signboards):
        signboard.choose_best_imgs(img_dir)

        if not signboard.best_crops_info:
            continue

        signboard.get_text(reader_detection, reader_english, reader_arabic, model_class_lang)


def save_imgs(signboards_list, img_dir, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    images_with_signboards = []
    for signboard in signboards_list:
        for img_with_crop in signboard.crops_info:
            img_name = img_with_crop.img_name

            if img_name not in [img['img_name'] for img in images_with_signboards]:
                images_with_signboards.append({'img_name': img_name, 'signboards': []})

            if signboard.geo_coords is None:
                coords = []
            else:
                coords = signboard.geo_coords

            signboard_info = {
                'bbox': img_with_crop.bbox,
                'text': signboard.title,
                'distance': img_with_crop.distance,
                'angle': img_with_crop.angle,
                'iou': img_with_crop.iou,
                'area': img_with_crop.area,
                'quality': img_with_crop.quality,
                'signboard_id': signboard.signboard_id,
                'coords': coords,
            }

            images_with_signboards[[img['img_name'] for img in images_with_signboards].index(img_name)][
                'signboards'].append(signboard_info)

    for img_name in images_with_signboards:
        init_img = cv2.imread(os.path.join(img_dir, img_name['img_name']))
        img = init_img.copy()
        for signboard in img_name['signboards']:
            bbox = signboard['bbox']
            text = signboard['text']
            reshaped_text = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)

            bidi_text = f'Text: {bidi_text}'
            distance_text = f'Distance: {str(signboard["distance"])[:5]}'
            angle_text = f'Angle: {str(signboard["angle"])}'
            area_text = f'Area: {str(signboard["area"])}'
            iou_text = f'IoU: {str(signboard["iou"])[:5]}'
            text_id = f'ID: {signboard["signboard_id"]}'
            quality_text = f'Quality: {str(signboard["quality"])}'

            if len(signboard['coords']) == 0:
                coords_text = f'Coords: '
            else:
                coords_text = f'Coords: {str(signboard["coords"][0][0])[:11]}, {str(signboard["coords"][0][1])[:11]}'

            img = draw_result(img, bbox, [text_id, iou_text, angle_text, distance_text, area_text, bidi_text])
            # [text_id, angle_text, bidi_text])

        cv2.imwrite(os.path.join(save_dir, img_name['img_name']), img)
        # print(f'Image {img_name["img_name"]} saved')
