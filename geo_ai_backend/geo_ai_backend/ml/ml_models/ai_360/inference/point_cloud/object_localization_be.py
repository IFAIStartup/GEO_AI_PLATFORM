import os
import numpy as np
from typing import List
import tritonclient.http as httpclient
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.inference import ModelEnsemble
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.config import Config
from geo_ai_backend.ml.ml_models.utils.inference_models import InferenceModel
from geo_ai_backend.ml.ml_models.utils.model_info import (
    ModelInfo,
    ModelTypeEnum
)
from geo_ai_backend.ml.ml_models.utils.triton_inference import (
    create_model_sets,
)
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.inference import (
    InferenceAdapter,
    get_image_segments
)

from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.io import (
    parse_image_paths,
    read_point_cloud,
    read_reference,
    create_vis_pcd,
)
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.projection import (
    find_scene_targets
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


def get_pcd_localization(
    image_paths: List[str],
    save_pcd_path: str,
    triton_client: httpclient.InferenceServerClient,
    save_shp_path: str,
    ml_model: str,
    cfg: Config = None,
):

    cfg = Config() if cfg is None else cfg
    scenes_info = parse_image_paths(image_paths)

    result_clusters_ids = {}
    result_points = np.zeros((0, 3))

    model = get_model_from_cfg(cfg, ml_model, triton_client)

    povs_list = []
    for scene_num in scenes_info:
        cur_image_paths = scenes_info[scene_num]['image_paths']
        reference_path = scenes_info[scene_num]['reference_path']
        las_path = scenes_info[scene_num]['las_path']
        scene_path = scenes_info[scene_num]['scene_path']

        points = read_point_cloud(las_path, True)
        trajectory = read_reference(reference_path)

        # Perform instance segmentation
        image_segments = get_image_segments(cur_image_paths, model, False, True)

        # Find reprojected points in lidar scenes using found segmentation masks
        scene_objs, povs = find_scene_targets(points, trajectory, cur_image_paths,
                                              int(scene_num), image_segments, cfg)
        povs_list.append(povs)

        # Build point clusters and add them to common result
        clusters_ids = find_clusters(points, scene_objs, cfg.classes_pcd)

        result_clusters_ids, result_points = update_result_clusters(
            result_clusters_ids, result_points, points, clusters_ids
        )

    # Create GeoDataFrames
    src_crs = cfg.src_crs
    dst_crs = cfg.dst_crs
    trajectory_lines = create_trajectory_lines(povs_list, src_crs, dst_crs)
    clusters_geometries = create_clusters_geometries(result_points,
                                                     result_clusters_ids, src_crs,
                                                     dst_crs)

    # Save results
    convert_geometries_to_shp(clusters_geometries, cfg.classes_pcd, save_shp_path)
    convert_trajectories_to_shp(trajectory_lines, save_shp_path)
    create_vis_pcd(result_points, result_clusters_ids, save_pcd_path)


def get_model_from_cfg(
    cfg: Config,
    triton_client: httpclient.InferenceServerClient
):
    model = ModelEnsemble(
        cfg.yolo_model_path,
        cfg.deeplab_model_path,
        cfg.inference_type,
        cfg.class_names_yolo,
        cfg.class_names_deeplab,
        triton_client=triton_client
    )

    return model


