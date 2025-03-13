import os
import cv2
import pandas as pd
import numpy as np
import tritonclient.http as httpclient
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

from geo_ai_backend.ml.ml_models.aerial_satellite.inference.join_tiles import (
    join_tiles,
    save_polys_to_shp
)

from geo_ai_backend.config import settings
from geo_ai_backend.ml.ml_models.ai_360.inference.utils import (
    check_save_dir,
    parse_args,
    draw_segment_results,
)
from geo_ai_backend.ml.ml_models.utils.triton_inference import (
    inference_pipeline,
    create_model_sets,
    get_tiles,
    add_padding,
    get_tiles_meta,
)
from geo_ai_backend.ml.ml_models.utils.model_sets import (
    ModelSet
)
from geo_ai_backend.ml.ml_models.utils.model_info import (
    ModelInfo
)


DEFAULT_CLASS_NAMES_YOLO = ['Lights pole', 'palm_tree', 'signboard', 'trees_group', 'trees_solo', 'traffic_sign']
DEFAULT_CLASS_NAMES_DEEPLAB = ['building', 'roads']


def save_result_image(
        img_in: np.ndarray,
        results: List[dict],
        res_save_path: str,
        img_name: str,
        class_names: List[str]) -> bool:

    img_out = draw_segment_results(img_in, results, class_names)
    img_save_path = os.path.join(res_save_path, f'{img_name}.jpg')
    status_image = cv2.imwrite(img_save_path, img_out)

    return status_image


def save_result_json(results, res_save_path, img_name):
    df = pd.DataFrame(results)
    json_data = df.to_json(orient='records')
    json_path = os.path.join(res_save_path, f'{img_name}.json')
    with open(json_path, 'w') as f:
        f.write(json_data)


def get_360_images(
    triton_client: httpclient.InferenceServerClient,
    model_info_list: List[ModelInfo],
    img_path: str,
    res_save_path: str,
) -> bool:

    img_name = os.path.splitext(os.path.basename(img_path))[0]
    img_in = cv2.imread(img_path)

    if img_in is None:
        print(img_name)
        return False

    # Create common class names dictionary, that contains all classes,
    # which will be in results.
    # TODO: change to list in the future; move it to inference (maybe)
    common_class_names = set()
    for model_info in model_info_list:
        common_class_names |= set(model_info.class_names)

    common_class_names = list(common_class_names)
    common_class_names_dict = {i: c for i, c in enumerate(common_class_names)}

    # Create list of model sets by provided models info,
    model_sets = create_model_sets(model_info_list)

    # Inference all model sets on the image and get results
    results = inference_model_sets(
        img_in,
        model_sets,
        common_class_names_dict,
        triton_client
    )

    # save image
    status_image = save_result_image(
        img_in,
        results,
        res_save_path,
        img_name,
        common_class_names,
    )

    # save json
    save_result_json(results, res_save_path, img_name)

    return status_image


def inference_model_sets(
        img_in: np.ndarray,
        model_sets: List[ModelSet],
        common_class_names: dict,
        triton_client: httpclient.InferenceServerClient) -> List[dict]:

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
                obj['segment'] = obj['segment'].astype('int32').reshape(-1, 2)

        # get info about tiles images
        tiles_info = {
            'tile_width': int((tile_size - 2 * overlap) / scale_factor),
            'tile_height': int((tile_size - 2 * overlap) / scale_factor),
            'tiles_in_col': int((img_padded.shape[0] - 2 * overlap) / (tile_size - 2 * overlap)),
            'tiles_in_row': int((img_padded.shape[1] - 2 * overlap) / (tile_size - 2 * overlap)),
            'padding_diff_x': 0,
            'padding_diff_y': 0,
        }
        
        objects_info = get_objects_info(
            tiles_meta,
            tiles_info,
            common_class_names
        )

    return objects_info


def get_objects_info(
        tiles_meta: list,
        tiles_info: dict,
        class_names: dict) -> list:
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
            # interior_coords = [get_coordinates(hole).astype(np.int32).tolist() for hole in list(obj_poly.interiors)]

            objects_info.append(
                {
                    'class': class_id,
                    'segment': exterior_coords.reshape(-1, 1, 2),
                }
            )
            count += 1
    return objects_info
