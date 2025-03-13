import numpy as np
from typing import Tuple, List, Dict, Union, Sequence
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.dbscan import dbscan

DEFAULT_MIN_SAMPLES = 2
DEFAULT_EPS = 0.9

SPEC_MIN_SAMPLES_MAP = {
    'palm_tree': 7,
    'trees_solo': 15,
    'Lights pole': 6,
    'signboard': 2,
    'building': 75,
}


def find_clusters(points: np.ndarray, scene_objs: dict, classes_pcd: List[str]):

    all_target_ids = {cls_name: [] for cls_name in classes_pcd}

    for image_name in scene_objs:
        image_objs = scene_objs[image_name]
        for obj in image_objs:
            class_name = obj['class_name']
            target_ids = obj['target_ids']
            all_target_ids[class_name] += target_ids

    for class_name in classes_pcd:
        all_target_ids[class_name] = np.unique(np.array(all_target_ids[class_name], dtype=np.int32))

    clusters_ids = get_clusters(points, all_target_ids, SPEC_MIN_SAMPLES_MAP)
    clusters_ids = filter_clusters(points, clusters_ids)

    return clusters_ids


def get_clusters(
        points: np.ndarray, 
        target_ids: List[np.ndarray], 
        spec_min_samples_map: Dict[str, int] = None) -> Dict[str, np.ndarray]:
    
    """Apply clusterization to found object ids

    :param points: array of shape (N, 3) that contains a point cloud
    :param target_ids: list of array with ids that points to value in `points` param
    :param: min_samples
    :return: dict, key '-1' - background points ids, keys '0', '1',..., 'n' - clusters points ids
    """

    all_clusters = {}

    for cls_name in target_ids:
        min_samples = spec_min_samples_map.get(cls_name, DEFAULT_MIN_SAMPLES)
        
        target_points = points[target_ids[cls_name]]
        if len(target_points) < min_samples:
            all_clusters[cls_name] = {}
            continue

        clustering_labels = dbscan(target_points, DEFAULT_EPS, min_samples)
        num_of_obj_clusters = clustering_labels.max() + 1

        clusters = {}
        for i in range(num_of_obj_clusters):
            clusters[str(i)] = target_ids[cls_name][clustering_labels == i]
        all_clusters[cls_name] = clusters

    return all_clusters


def filter_clusters(points, clusters):
    if 'palm_tree' in clusters and 'trees_solo' in clusters:
        clusters['palm_tree'], clusters['trees_solo'] = delete_intersections(
            points, clusters['palm_tree'], clusters['trees_solo']
        )
    
    for cls_name in ['palm_tree', 'building', 'signboard']:
        if cls_name in clusters:
            clusters = delete_extra_objects(clusters, cls_name)
    
    return clusters


def remove_small_clusters(clusters: Dict[str, np.ndarray], min_len: int) -> Dict[str, np.ndarray]:
    res = {}
    cnt = 0
    for i in clusters:
        if len(clusters[i]) >= min_len:
            res[str(cnt)] = clusters[i]
            cnt += 1
    return res



def delete_extra_objects(clusters, extra_class):
    non_extra_ids = []
    for name in clusters:
        if name == extra_class:
            continue
        for i in clusters[name]:
            non_extra_ids += clusters[name][i].tolist()

    non_extra_ids = np.array(non_extra_ids)

    new_extra_class_clusters = {}
    for i in clusters[extra_class]:
        mask = np.isin(clusters[extra_class][i], non_extra_ids)
        cluster = clusters[extra_class][i][~mask]

        if len(cluster) > 0:
            new_extra_class_clusters[str(len(new_extra_class_clusters))] = cluster

    clusters[extra_class] = new_extra_class_clusters

    return clusters


def delete_intersections(points: np.ndarray, clusters1: dict, clusters2: dict) -> tuple:
    centers1 = {}
    for i in clusters1:
        cluster_points = points[clusters1[i]]
        center = np.array([cluster_points[:, 0].mean(), cluster_points[:, 1].mean(), cluster_points[:, 2].mean()])
        centers1[i] = center

    centers2 = {}
    for i in clusters2:
        cluster_points = points[clusters2[i]]
        center = np.array([cluster_points[:, 0].mean(), cluster_points[:, 1].mean(), cluster_points[:, 2].mean()])
        centers2[i] = center

    for i in centers1:
        for j in centers2:

            if j not in clusters2:
                continue
            
            center1 = centers1[i]
            center2 = centers2[j]
            dist = np.linalg.norm(center2 - center1)
            if dist > 2:
                continue

            if len(clusters1[i]) > len(clusters2[j]):
                clusters2.pop(j)
            else:
                clusters1.pop(i)

    return clusters1, clusters2


def update_result_clusters(
    result_clusters_ids: dict,
    result_points: np.ndarray,
    points: np.ndarray,
    clusters_ids: dict) -> dict:

    for category in clusters_ids:
        category_ids = clusters_ids[category]
        if category not in result_clusters_ids:
            result_clusters_ids[category] = {}

        for i in category_ids:
            result_clusters_ids[category][len(result_clusters_ids[category])] = clusters_ids[category][i] + len(result_points)

    result_points = np.concatenate([result_points, points], axis=0)
    return result_clusters_ids, result_points

