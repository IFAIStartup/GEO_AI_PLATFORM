import os
import pandas as pd
from typing import List, Dict
import geopandas as gpd
import pyproj
from shapely.geometry import Point
import tritonclient.http as httpclient
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.config import (
    Config
)
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.io import (
    parse_image_paths,
    read_point_cloud,
    read_reference,
    create_vis_pcd,
)
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.inference import (
    InferenceAdapter,
    get_image_segments,
)
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.projection import (
    find_scene_targets,
    parse_image_filename,
    get_coords_from_trajectory,
    get_latlong_from_trajectory,
)
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.clustering import (
    find_clusters, update_result_clusters
)
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.geodata import (
    create_trajectory_lines,
    create_clusters_geometries,
    convert_geometries_to_shp,
    convert_trajectories_to_shp,
)


from geo_ai_backend.ml.ml_models.utils.inference_models import InferenceModel
from geo_ai_backend.ml.ml_models.utils.model_info import (
    ModelInfo,
    ModelTypeEnum
)
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.inference import (
    get_model_from_info_list
)


def get_pcd_localization_without_las(
    image_paths: List[str],
    model_info_list: List[ModelInfo],
    triton_client: httpclient.InferenceServerClient,
    save_shp_path: str,
    cfg: Config = None,
):
    cfg = Config() if cfg is None else cfg
    scenes_info = parse_image_paths(image_paths, False)

    results = []
    povs_list = []

    # Create common class names dictionary, that contains all classes,
    # which will be in results.
    common_class_names = set()
    for model_info in model_info_list:
        common_class_names |= set(model_info.class_names)

    common_class_names = list(common_class_names)
    common_class_names_dict = {i: c for i, c in enumerate(common_class_names)}

    # model = get_model_from_cfg(cfg, triton_client)
    model = get_model_from_info_list(
        model_info_list, 
        triton_client, 
        common_class_names_dict
    )

    for scene_num in scenes_info:
        cur_image_paths = scenes_info[scene_num]['image_paths']
        reference_path = scenes_info[scene_num]['reference_path']

        trajectory = read_reference(reference_path)

        # Perform instance segmentation
        image_segments = get_image_segments(cur_image_paths, model, False, True)

        scene_results, povs = get_objects(trajectory, cur_image_paths, int(scene_num),
                                          image_segments, common_class_names, cfg)
        # povs = get_scene_povs(trajectory, cur_image_paths)
        results += scene_results
        povs_list.append(povs)

    # Create GeoDataFrames
    src_crs = cfg.src_crs
    dst_crs = cfg.dst_crs
    
    trajectory_lines = create_trajectory_lines(povs_list, dst_crs, dst_crs)
    clusters_geometries = create_clusters_geometries(results, dst_crs, dst_crs)

    # Save results
    convert_geometries_to_shp(clusters_geometries, cfg.classes_pcd, save_shp_path)
    convert_trajectories_to_shp(trajectory_lines, save_shp_path)
    # shutil.make_archive(save_shp_path, 'zip', save_shp_path)


def get_objects(
    trajectory: pd.DataFrame,
    image_paths: List[str],
    scene_num: int,
    image_segments: dict,
    common_class_names: list,
    cfg: Config):
    
    class_names_pred = common_class_names
    results = []
    povs = {}

    for img_path in image_paths:
        if not os.path.exists(img_path):
            continue

        img_fn = os.path.basename(img_path)
        name, ext = os.path.splitext(img_fn)

        if name not in image_segments:
            continue

        _, img_num, proj_num = parse_image_filename(img_fn, cfg.template_img_name)
        lat, long = get_latlong_from_trajectory(
            trajectory, 
            scene_num, 
            img_num,
            cfg.template_trajectory_point
        )

        point_of_view = [long, lat]
        povs[int(img_num)] = point_of_view

        segments = image_segments[name]
        cur_result = {'pov': point_of_view, 'class_names': []}

        for segment in segments:
            class_name = class_names_pred[int(segment[0])]

            if class_name == 'trees_group':
                class_name = 'trees_solo'
            cur_result['class_names'].append(class_name)

        results.append(cur_result)

    return results, povs


def create_clusters_geometries(
    results: List[dict],
    src_crs: pyproj.CRS,
    dst_crs: pyproj.CRS) -> Dict[str, gpd.GeoDataFrame]:
    gdfs = {}
    layers = {}
    for res in results:
        pov = res['pov']
        class_names = res['class_names']

        for name in class_names:
            if name not in layers:
                layers[name] = []
            layers[name].append(Point(pov))

    for name in layers:
        layer = layers[name]
        gdf = gpd.GeoDataFrame(layer, columns=['geometry'], crs=src_crs)
        gdf = gdf.to_crs(crs=dst_crs)
        gdfs[name] = gdf

    return gdfs
