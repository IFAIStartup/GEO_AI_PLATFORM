import numpy as np
from typing import List, Dict
from scipy import stats
import pickle
import json
import matplotlib.pyplot as plt
import tritonclient.http as httpclient
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.inference import LangClsModel
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.config import Config
import easyocr
from easydict import EasyDict
from geo_ai_backend.ml.ml_models.ocr.geo_ai_ocr.cropinfo import (
    CropInfo,
    get_surface,
    get_surface_line_angle
)
from geo_ai_backend.ml.ml_models.ocr.geo_ai_ocr.funcs import connect_signboards_to_clusters
from geo_ai_backend.ml.ml_models.ocr.geo_ai_ocr.funcs import save_imgs
from geo_ai_backend.ml.ml_models.ocr.geo_ai_ocr.point_cloud import calculate_signboards_iou
from geo_ai_backend.ml.ml_models.ocr.geo_ai_ocr.main import OCR_inference
from geo_ai_backend.ml.ml_models.ocr.geo_ai_ocr.reader import TritonEasyocrReader

from geo_ai_backend.ml.ml_models.utils.model_info import (
    ModelInfo
)
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
from geo_ai_backend.ml.ml_models.utils.triton_inference import ( 
    create_model_sets,
)
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.inference import (
    get_model_from_info_list
)


def get_pcd_localization_ocr(
    image_paths: List[str],
    model_info_list: List[ModelInfo],
    triton_client: httpclient.InferenceServerClient,
    save_pcd_path: str,
    save_shp_path: str,
    cfg: Config = None
):
    cfg = Config() if cfg is None else cfg
    scenes_info = parse_image_paths(image_paths)

    result_clusters_ids = {}
    result_points = np.zeros((0, 3))

    povs_list = []
    texts = {'signboard': {}, 'traffic_sign': {}}

    # Create common class names dictionary, that contains all classes,
    # which will be in results.
    common_class_names = set()
    for model_info in model_info_list:
        common_class_names |= set(model_info.class_names)

    common_class_names = list(common_class_names)
    common_class_names_dict = {i: c for i, c in enumerate(common_class_names)}

    model = get_model_from_info_list(
        model_info_list, 
        triton_client, 
        common_class_names_dict)
    
    ocr_models = load_ocr_models(cfg.lang_cls_model_path, cfg.inference_type, triton_client)

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
                                              int(scene_num), image_segments, common_class_names, cfg)

        povs_list.append(povs)

        # Build point clusters and add them to common result
        clusters_ids = find_clusters(points, scene_objs, cfg.classes_pcd)

        for class_name in texts:
            offset = 0 if class_name not in result_clusters_ids else len(
                result_clusters_ids[class_name])
            scene_texts = get_scene_ocr_texts(
                points, clusters_ids[class_name], scene_objs, scene_path, ocr_models,
                offset, class_name
            )
            texts[class_name].update(scene_texts)

        result_clusters_ids, result_points = update_result_clusters(
            result_clusters_ids, result_points, points, clusters_ids
        )

    # Create GeoDataFrames
    src_crs = cfg.src_crs
    dst_crs = cfg.dst_crs
    trajectory_lines = create_trajectory_lines(povs_list, src_crs, dst_crs)
    clusters_geometries = create_clusters_geometries(result_points, result_clusters_ids, src_crs, dst_crs)

    # Save results
    convert_geometries_to_shp(clusters_geometries, cfg.classes_pcd, save_shp_path, texts=texts)
    convert_trajectories_to_shp(trajectory_lines, save_shp_path)
    create_vis_pcd(result_points, result_clusters_ids, save_pcd_path)
    # shutil.make_archive(save_shp_path, 'zip', save_shp_path)


def load_ocr_models(lang_cls_model_path: str, inference_type: str, triton_client: httpclient.InferenceServerClient) -> EasyDict:
    easyocr_detection_model = TritonEasyocrReader(triton_client, 'easyocr_detector')
    easyocr_arabic_model = TritonEasyocrReader(triton_client, 'easyocr_classifier_ar')
    easyocr_english_model = TritonEasyocrReader(triton_client, 'easyocr_classifier_en')
    classification_language_model = LangClsModel(lang_cls_model_path, inference_type,
                                                 triton_client)

    models = EasyDict()
    models.detection_model = None
    models.classification_quality_model = None
    models.classification_language_model = classification_language_model
    models.super_resolution_model = None
    models.magface_model = None
    models.easyocr_detection_model = easyocr_detection_model
    models.easyocr_arabic_model = easyocr_arabic_model
    models.easyocr_english_model = easyocr_english_model

    return models


def get_scene_ocr_texts(points, clusters_ids, scene_objs, scene_path, ocr_models, cluster_id_offset, class_name):
    crop_list = create_crop_list(points, scene_objs, class_name)
    connect_signboards_to_clusters(crop_list, clusters_ids)
    calculate_signboards_iou(crop_list, {'signboard': clusters_ids}, points, 1280)  # TODO: change clister input
    calculate_signboards_angle(crop_list, clusters_ids, points)

    signboards_list, ocr_results = OCR_inference(crop_list, ocr_models, scene_path)

    # save_imgs(signboards_list, scene_path, f'ocr_vis_{class_name}')
    # with open('ocr_results.json', 'w') as f:
    #     json.dump(ocr_results, f, indent=4)

    texts = {}
    for res in ocr_results:
        title = res['title']
        cluster_ids = [int(crop_info['cluster_id']) for crop_info in res['crops_info']]
        best_cluster_id = stats.mode(np.array(cluster_ids))[0]
        
        if type(best_cluster_id) == np.int64:
            texts[int(best_cluster_id) + cluster_id_offset] = title
        else:
            texts[int(best_cluster_id[0]) + cluster_id_offset] = title

    return texts


def calculate_signboards_angle(crop_list: List[CropInfo], clusters_ids, points):
    for img_info in crop_list:
        if img_info.cluster_id is None:
            continue

        cluster_points = points[clusters_ids[img_info.cluster_id]]
        line = img_info.center - img_info.point_of_view
        surface = get_surface(cluster_points)
        angle = get_surface_line_angle(surface, line)
        angle = np.degrees(angle)
        img_info.angle = angle

def connect_signboards_to_clusters(crops_list: List[CropInfo], signboard_clusters: dict):
    """Assign appropriate cluster id to each crop (if possible, else None will be assigned)"""

    for img_info in crops_list:
        # If there is no projected points, skip it
        if img_info.target_ids is None:
            continue

        # Find cluster metric
        cluster_iou = {}

        for cluster_id in signboard_clusters:
            cluster_points_ids = signboard_clusters[cluster_id]

            # Metric is a intersection of projected points and cluster points divided by number of points in cluster
            # iou = np.isin(img_info.target_ids, cluster_ids).sum() / len(cluster_ids)
            # cluster_iou[cluster_id] = iou
            intersection = np.isin(img_info.target_ids, cluster_points_ids).sum()
            union = len(img_info.target_ids) + len(cluster_points_ids) - intersection
            iou = intersection / union
            cluster_iou[cluster_id] = iou

        sorted_cluster_iou = {k: v for k, v in
                              sorted(cluster_iou.items(), key=lambda item: -item[1])}
        sorted_cluster_iou_keys = list(sorted_cluster_iou.keys())

        img_info.cluster_dist = None  # sorted_cluster_iou_keys
        if len(sorted_cluster_iou_keys) == 0:
            img_info.cluster_id = None
            continue

        closest_cluster_id = sorted_cluster_iou_keys[0]
        if sorted_cluster_iou[closest_cluster_id] == 0:
            img_info.cluster_id = None
            continue

        img_info.cluster_id = closest_cluster_id


def get_cluster_centers_ocr(points: np.ndarray,
                            clusters: Dict[str, np.ndarray]) -> np.ndarray:
    centers = {}
    num_of_clusters = len(clusters) - 1
    for i in range(num_of_clusters):
        cluster_points = points[clusters[str(i)]]
        center = [cluster_points[:, 0].mean(), cluster_points[:, 1].mean(),
                  cluster_points[:, 2].min()]
        centers[str(i)] = center

    return centers


def create_crop_list(points: np.ndarray, scene_objs: dict, text_class_name: str):
    crop_list = []
    for image_name in scene_objs:
        image_objs = scene_objs[image_name]

        for obj in image_objs:
            class_name = obj['class_name']
            target_ids = obj['target_ids']
            extrinsic = obj['extrinsic']
            box = obj['box']
            segment = obj['segment']
            point_of_view = obj['point_of_view']

            if class_name != text_class_name:
                continue

            target_points = points[target_ids]
            crop_info = CropInfo(
                image_name + '.jpg',  # TODO: change ext
                np.array(box),
                np.array(segment),
                extrinsic,
                target_ids,
                target_points)

            crop_info.point_of_view = point_of_view
            crop_info.set_bbox_area()
            crop_info.set_center()
            crop_info.set_distance(point_of_view)
            # crop_info.set_angle(point_of_view)

            crop_list.append(crop_info)

    return crop_list
