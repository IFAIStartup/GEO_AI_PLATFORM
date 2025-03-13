import os
import numpy as np
import pandas as pd
import cv2
import tritonclient.http as httpclient
import rasterio
import shapely
from typing import List
from shapely.affinity import translate
import json
import geopandas as gpd
from shapely import (
    get_coordinates,
    MultiPolygon,
    GeometryCollection,
    Polygon,
    is_empty,
    Point,
)


from geo_ai_backend.ml.ml_models.HAT.inference.utils import getWKT_PRJ
from geo_ai_backend.ml.ml_models.utils.triton_inference import (
    add_padding,
)
from geo_ai_backend.ml.ml_models.aerial_satellite.inference.utils import (
    draw_segment_results_scene,
)
from geo_ai_backend.ml.ml_models.aerial_satellite.inference.join_tiles import (
    join_tiles,
    save_polys_to_shp
)
from geo_ai_backend.ml.ml_models.utils.model_sets import (
    ModelSet,
)
from geo_ai_backend.ml.ml_models.utils.model_info import (
    ModelInfo,
    ModelTypeEnum,
)
from geo_ai_backend.ml.ml_models.utils.inference_models import (
    InferenceModel,
    filter_predictions_by_classes,
    YOLOv8segModel,
    DeepLabv3Model,
)
from geo_ai_backend.ml.ml_models.utils.triton_inference import (
    get_tiles_meta,
    get_tiles,
    create_model_sets
)

DEFAULT_CLASS_NAMES_YOLO = ['palm_tree', 'buildings', 'farms', 'trees']
DEFAULT_CLASS_NAMES_DEEPLAB = ['roads', 'tracks']



def get_content_poly(img_in: np.ndarray) -> shapely.Polygon:
    """
    Get non-black zone covering polygon
    Args:
        img_in: Image for covering

    Returns:
        non_black_area_poly: shapely.Polygon
    """

    # Gray image
    imgray = cv2.cvtColor(img_in, cv2.COLOR_BGR2GRAY)

    # Binarized image
    ret, thresh = cv2.threshold(imgray, 0, 255, cv2.THRESH_BINARY)

    # Get contour of non-black area
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        non_black_area_cnt = max(contours, key=cv2.contourArea)
        non_black_area_cnt = non_black_area_cnt.reshape((len(non_black_area_cnt), 2))
        # Get polygon from contour
        non_black_area_poly = Polygon(non_black_area_cnt)
    else:
        non_black_area_poly = Point([-1, -1])

    return non_black_area_poly


# def get_tiles(image: np.ndarray, tile_size: int, overlap: int) -> list:
#     """
#     Split image into tiles with overlap.
#     :param image: image to split
#     :param tile_size: size of tile
#     :param overlap: overlap between tiles
#     :return: list of tiles
#     """
#     tiles = []
#     h, w = image.shape[:2]
#     for i in range(0, h - tile_size + 1, tile_size - overlap * 2):
#         for j in range(0, w - tile_size + 1, tile_size - overlap * 2):
#             tile = image[i:i + tile_size, j:j + tile_size]
#             tiles.append(tile)
#     return tiles


def get_objects_info(
        tiles_meta: list,
        tiles_info: dict,
        class_names: dict,
        non_black_zone: shapely.Polygon) -> list:
    """
    Get objects info from tiles meta. Save polygons to shp. Return objects info.
    :param tiles_meta: list of tiles meta
    :param tiles_info: dict of tiles info
    :param classes: dict of class names
    :param geo_coeffs: dict of geo coeffs
    :param save_dir: path to save shp
    :param non_black_zone: polygon of non-black area
    :return: list of objects info
    """
    objects_info = []
    count = 0

    tiles_in_col = tiles_info['tiles_in_col']
    tiles_in_row = tiles_info['tiles_in_row']
    tile_width = tiles_info['tile_width']
    tile_height = tiles_info['tile_height']
    padding_diff_x = tiles_info['padding_diff_x']
    padding_diff_y = tiles_info['padding_diff_y']

    for class_id in class_names.keys():
        class_name = class_names[class_id]

        edge_vicinity = 40
        vicinity = 30
        if class_name == 'roads':
            vicinity = 100
            edge_vicinity = 60

        res_poly = join_tiles(
            tiles_meta, 
            class_id, 
            tiles_in_col, 
            tiles_in_row, 
            tile_width, 
            tile_height,
            edge_vicinity=edge_vicinity, 
            vicinity=vicinity, 
            show_poly=False
        )

        # check if res_poly is list
        if not isinstance(res_poly, list):
            continue

        for i in range(len(res_poly)):
            res_poly[i] = translate(
                res_poly[i], 
                xoff=-padding_diff_x, 
                yoff=-padding_diff_y
            )

        # Remove polygons from black areas
        gdf = gpd.GeoSeries(res_poly)
        res_poly = gdf.intersection(non_black_zone).tolist()
        res_poly = [poly for poly in res_poly if not is_empty(poly)]
        ###

        filtred_polys = []
        for poly in res_poly:
            if type(poly) == Polygon:
                filtred_polys.append(poly)
            elif type(res_poly) == MultiPolygon:
                filtred_polys.extend(list(res_poly.geoms))
            elif type(res_poly) == GeometryCollection:
                filtred_polys.extend([geom for geom in list(res_poly.geoms) if type(geom) == Polygon])
        res_poly = filtred_polys

        for obj_poly in res_poly:

            # TODO: It is quick fix, maybe wrond
            if obj_poly.geom_type == 'MultiPolygon':
                obj_poly = obj_poly.convex_hull
            exterior_coords = get_coordinates(obj_poly.exterior).round().astype(np.int32)
            interior_coords = [get_coordinates(hole).astype(np.int32).tolist() for hole in list(obj_poly.interiors)]

            x, y, w, h = cv2.boundingRect(exterior_coords)  # xlu, ylu, w, h
            bbox = [x, y, x + w, y + h]  # xlu, ylu, xrd, yrd

            objects_info.append(
                {
                    'object_num': count,
                    'class_id': class_id,
                    'class_name': class_name,
                    'bbox': bbox,
                    'coordinates': {'exterior': exterior_coords,
                                    'interior': interior_coords}
                }
            )
            count += 1
    return objects_info


# def get_tiles_meta(
#         tiles: list,
#         class_names_common: dict,
#         tile_size: int,
#         overlap: int,
#         inference_models: List[InferenceModel],
#         client: httpclient.InferenceServerClient) -> list:
#     # TODO: Change docs
#     """
#     Get tiles meta from tiles. It contains polygons and classes for every tile.
#     :param tiles: list of tiles
#     :param classes: dict of class names
#     :param tile_size: size of tile
#     :param models: dict of models (yolov8, deeplabv3)
#     :param client: client
#     :return: list of tiles meta
#     """
#     tiles_meta = []
#     for tile_num, tile in enumerate(tiles):
#         results = inference_pipeline(
#             tile,
#             class_names_common,
#             (tile_size, tile_size),
#             overlap,
#             inference_models,
#             client
#         )
#         tiles_meta.append(results)

#     return tiles_meta


# def inference_pipeline(
#         img_in: np.ndarray,
#         class_names_common: dict,
#         imgsz: tuple,
#         overlap: int,
#         inference_models: list,
#         client: httpclient.InferenceServerClient) -> List[List[np.ndarray]]:

#     # TODO: change docs
#     """ Do model inference with preprocessing and postprocessing

#     :param img_in: rgb image with arbitrary height and width (with shape (H0, W0, 3))
#     :param classes: dict of matched ids and class names ({0: cls_name0, 1: cls_name1, ...})
#     :param model_name: specific name of the model in model repository
#     :param client: _description_

#     :return: List of one list of 2 arrays: detections (N, 6) and masks (N, H0, W0)
#     """

#     segments_with_classes = []
#     for model in inference_models:
#         result = model(img_in, client, overlap)
#         segments_with_classes += result

#     segments_with_classes = filter_predictions_by_classes(segments_with_classes, class_names_common)

#     return segments_with_classes


def read_tiff(path: str, save_to_wf_dir="worldfiles") -> tuple[np.ndarray, dict]:
    # check if the file is tiff
    if not path.endswith('.tif'):
        img_in = cv2.imread(path)
        return img_in, None

    worldfile = {"image_width": 0,
                 "image_height": 0,
                 "CRS": "EPSG:4326",
                 "worldfile": {}}

    with rasterio.open(path) as tif_file:
        img_in = tif_file.read()
        img_in = np.transpose(img_in, (1, 2, 0))
        img_in = img_in[:, :, :3]
        img_in = cv2.cvtColor(img_in, cv2.COLOR_RGB2BGR)
        worldfile["image_height"] = img_in.shape[0]
        worldfile["image_width"] = img_in.shape[1]

    geo_coeffs = {
        'A': tif_file.transform.a,
        'D': tif_file.transform.d,
        'B': tif_file.transform.b,
        'E': tif_file.transform.e,
        'C': tif_file.transform.c,
        'F': tif_file.transform.f,
    }

    crs = tif_file.crs
    worldfile["CRS"] = str(crs)
    worldfile["worldfile"] = geo_coeffs
    img_name = path.split("/")[-1].split(".")[0]

    if not os.path.exists(save_to_wf_dir):
        os.mkdir(save_to_wf_dir)

    save_to_worldfile = os.path.join(
        save_to_wf_dir,
        img_name + '.jgw'
    )

    with open(save_to_worldfile, 'w') as wf:
        for coef in geo_coeffs.values():
            wf.write(str(coef) + '\n')

    save_to_prj = os.path.join(
        save_to_wf_dir,
        img_name + '.prj'
    )

    epsg = str(crs).split(':')[-1]
    prj_data = getWKT_PRJ(epsg)

    with open(save_to_prj, 'w') as prj_file:
        prj_file.write(prj_data)

    geo_coeffs = {
        'A': tif_file.transform.a,
        'B': tif_file.transform.b,
        'C': tif_file.transform.c,
        'D': tif_file.transform.d,
        'E': tif_file.transform.e,
        'F': tif_file.transform.f,
    }
    save_to_project_data = os.path.join(
        save_to_wf_dir,
        img_name + '_json.json'
    )

    with open(save_to_project_data, 'w') as f:
        json.dump(worldfile, f)
    geo_data = {
        'geo_coeffs': geo_coeffs,
        'crs': crs
    }

    return img_in, geo_data


def truncate_masks(masks: np.ndarray, overlap: int = 128):
    if len(masks.shape) == 2:
        return masks[overlap: masks.shape[0] - overlap, overlap: masks.shape[1] - overlap]

    return masks[:, overlap: masks.shape[1] - overlap, overlap: masks.shape[2] - overlap]


# def create_model_sets(model_info_list: List[ModelInfo], relative_overlap: float = 0) -> List[ModelSet]:

#     scales = {}

#     for model_info in model_info_list:
#         model_name = model_info.model_name
#         model_type = model_info.model_type
#         class_names = model_info.class_names
#         tile_size = model_info.tile_size
#         scale_factor = model_info.scale_factor

#         imgsz = (tile_size, tile_size)

#         # TODO: change dict to list
#         class_names_dict = {i: c for i, c in enumerate(class_names)}

#         if model_type == ModelTypeEnum.yolov8:
#             model = YOLOv8segModel(model_name, class_names_dict, imgsz)
#         else:   # ModelTypeEnum.deeplabv3
#             model = DeepLabv3Model(model_name, class_names_dict, imgsz)

#         key = f"{scale_factor}_{tile_size}"
#         if key not in scales:
#             overlap = int(tile_size * relative_overlap)
#             scales[key] = ModelSet([], scale_factor, tile_size, overlap)        
        
#         scales[key].inference_models.append(model)
    
#     model_sets = []
#     for scale_factor in scales:
#         model_sets.append(scales[scale_factor])

#     return model_sets


def save_result_image(
        img_in: np.ndarray,
        common_objects_info: List[dict],
        save_dir: str,
        img_name: str) -> bool:

    img_out = draw_segment_results_scene(img_in, common_objects_info)
    img_save_path = os.path.join(save_dir, f'{img_name}.jpg')
    status_image = cv2.imwrite(img_save_path, img_out)

    # # ** Additional images saving, uncomment this to enable **

    # img_save_path_small = os.path.join(save_dir, f'{img_name}_640.png')
    # cv2.imwrite(img_save_path_small, cv2.resize(img_out, (640, 640)))

    # img_save_path = os.path.join(save_dir, f'{img_name}.jpg')
    # cv2.imwrite(img_save_path, img_out)

    return status_image


def save_result_json(common_objects_info: List[dict], save_dir: str, img_name: str):
    df = pd.DataFrame(common_objects_info)
    json_data = df.to_json(orient='records')
    json_path = os.path.join(save_dir, f'{img_name}.json')
    with open(json_path, 'w') as f:
        f.write(json_data)


def inference_model_sets(
        img_in: np.ndarray,
        model_sets: List[ModelSet],
        common_class_names: dict,
        triton_client: httpclient.InferenceServerClient,
        save_dir: str) -> list:

    # get polygon of non-black image zone
    non_black_zone = get_content_poly(img_in)
    objects_info_list = []

    for model_set in model_sets:
        inference_models = model_set.inference_models
        tile_size = model_set.tile_size
        overlap = model_set.overlap
        scale_factor = model_set.scale_factor

        # If scale factor less or equals zero, then we consider that
        # we need to rescale the input image to the tile size
        # and find actual scale factor.
        # Otherwise just resize image with required scale factor
        h, w = img_in.shape[:2]
        if scale_factor <= 0:
            scale_factor = min(tile_size / h, tile_size / w)
        
        img_resized = cv2.resize(img_in, (int(scale_factor * w), int(scale_factor * h)))

        # add padding to image to make it divisible by tile size
        img_padded = add_padding(img_resized, tile_size, overlap)

        # get tiles from image with overlap
        tiles = get_tiles(img_padded, tile_size, overlap)

        # get info about tiles images
        tiles_info = {
            'tile_width': int((tile_size - 2 * overlap) / scale_factor),
            'tile_height': int((tile_size - 2 * overlap) / scale_factor),
            'tiles_in_col': int((img_padded.shape[0] - 2 * overlap) / (tile_size - 2 * overlap)),
            'tiles_in_row': int((img_padded.shape[1] - 2 * overlap) / (tile_size - 2 * overlap)),
            'padding_diff_x': 0,
            'padding_diff_y': 0,
        }

        # Create tiles meta info from each tile using triton inference
        # tiles meta info contains class and polygon of each object
        tiles_meta = get_tiles_meta(
            tiles,
            common_class_names,
            tile_size,
            overlap,
            inference_models,
            triton_client,
        )

        # Resize tiles meta
        for tile_meta in tiles_meta:
            for obj in tile_meta:
                obj['segment'] = obj['segment'].astype('float64')
                obj['segment'] /= scale_factor
                obj['segment'] = obj['segment'].astype('int32')

        # Join tiles and save to shp
        # collect polygons from all tiles and get objects info dict
        os.makedirs(save_dir, exist_ok=True)
        objects_info = get_objects_info(
            tiles_meta,
            tiles_info,
            common_class_names,
            non_black_zone
        )

        objects_info_list.append(
            {
                'objects_info': objects_info,
                'scale_factor': scale_factor,
                'tile_size': tile_size
            }
        )

    # Join all objects info with filtration
    common_objects_info = join_objects_info(objects_info_list, list(common_class_names.values()))
    return common_objects_info


def save_objects_to_shp(
        geo_data: dict, 
        objects_info: list, 
        class_names: list,
        save_dir: str):
    
    for class_name in class_names:
        polys = []

        for obj in objects_info:
            if obj['class_name'] != class_name:
                continue

            poly = shapely.Polygon(
                obj['coordinates']['exterior'], 
                obj['coordinates']['interior']
            )
            polys.append(poly)
        
        save_path = os.path.join(save_dir, f'{class_name}.shp')
        save_polys_to_shp(polys, geo_data, save_path, class_name)


def join_objects_info(
        objects_info_list: List[dict],
        class_names: List[str],
        stuff_classes=('roads', 'tracks')):

    common_objects_info = []

    for objects_info in objects_info_list:
        common_objects_info += objects_info['objects_info']

    common_objects_info = remove_overlapping_objects(
        common_objects_info,
        class_names,
        stuff_classes=stuff_classes)

    return common_objects_info


def remove_overlapping_objects(
        objects_info: List[dict],
        class_names: List[str],
        stuff_classes: list = None,
        iou_thresh=0.4):

    """Remove overlapping objects and keep the biggest one among them. Overlapping defines as IoU of boxes"""

    stuff_classes = stuff_classes or []

    # num_of_classes = len(class_names)
    obj_ids = []
    stuff_obj_ids = []
    boxes = []

    for obj_id, object_info in enumerate(objects_info):
        if class_names[object_info['class_id']] in stuff_classes:
            stuff_obj_ids.append(obj_id)
            continue

        box = object_info['bbox']
        boxes.append(box)
        obj_ids.append(obj_id)

    boxes = np.array(boxes).reshape(-1, 4)
    mask = non_largest_suppression(boxes, iou_thresh)

    obj_ids = np.array(obj_ids)
    obj_ids = obj_ids[mask]
    obj_ids = obj_ids.tolist()

    new_objects_info = []
    for obj_id in (obj_ids + stuff_obj_ids):
        obj_info = objects_info[obj_id]
        new_objects_info.append(obj_info)

    return new_objects_info


def non_largest_suppression(boxes, iou_thres):

    rows = len(boxes)
    squares = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    sort_index = np.flip(squares.argsort())

    boxes = boxes[sort_index]
    ious = box_iou_batch(boxes, boxes)
    ious = ious - np.eye(rows)

    keep = np.ones(rows, dtype=bool)

    for index, iou in enumerate(ious):
        if not keep[index]:
            continue

        condition = (iou > iou_thres)
        keep = keep & ~condition

    return np.nonzero(keep[sort_index.argsort()])[0]


def box_iou_batch(
	boxes_a: np.ndarray, boxes_b: np.ndarray
) -> np.ndarray:

    def box_area(box):
        return (box[2] - box[0]) * (box[3] - box[1])

    area_a = box_area(boxes_a.T)
    area_b = box_area(boxes_b.T)

    top_left = np.maximum(boxes_a[:, None, :2], boxes_b[:, :2])
    bottom_right = np.minimum(boxes_a[:, None, 2:], boxes_b[:, 2:])

    area_inter = np.prod(
    	np.clip(bottom_right - top_left, a_min=0, a_max=None), 2)

    return area_inter / (area_a[:, None] + area_b - area_inter)


def get_aerial_satellite_image(
    triton_client: httpclient.InferenceServerClient,
    model_info_list: List[ModelInfo],
    img_path: str,
    save_dir: str,
    save_image_flag: bool = True,
    save_json_flag: bool = True,
    relative_overlap: float = 0,
):

    # Read image and its geo data
    img_name = os.path.splitext(os.path.basename(img_path))[0]
    img_in, geo_data = read_tiff(img_path, save_to_wf_dir=f"{save_dir}")

    # Create common class names dictionary, that contains all classes,
    # which will be in results.
    # TODO: change to list in the future; move it to inference (maybe)
    common_class_names = set()
    for model_info in model_info_list:
        common_class_names |= set(model_info.class_names)

    common_class_names = list(common_class_names)
    common_class_names_dict = {i: c for i, c in enumerate(common_class_names)}

    # Create list of model sets by provided models info,
    # which is a special wrap for using models with different scales
    model_sets = create_model_sets(model_info_list, relative_overlap)

    # Inference all model sets on the image and get results
    common_objects_info = inference_model_sets(
        img_in,
        model_sets,
        common_class_names_dict,
        triton_client,
        save_dir
    )
    
    if geo_data is not None:
        save_objects_to_shp(geo_data, common_objects_info, common_class_names, save_dir)

    # Save result image to save dir
    status_image = False
    if save_image_flag:
        status_image = save_result_image(img_in, common_objects_info, save_dir, img_name)

    # Save result json to save dir
    if save_json_flag:
        save_result_json(common_objects_info, save_dir, img_name)

    return status_image

