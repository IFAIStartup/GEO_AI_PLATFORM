import os
import cv2
import re
import open3d as o3d
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Union, Sequence
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.dbscan import dbscan
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.config import Config


def find_scene_targets(
    points: np.ndarray,
    trajectory: pd.DataFrame,
    image_paths: List[str],
    scene_num: int,
    image_segments: Dict[str, List[List[float]]],
    common_class_names: List[str],
    cfg: Config
):
    """_summary_

    :param points: _description_
    :param trajectory: _description_
    :param image_paths: _description_
    :param scene_num: _description_
    :param model: _description_
    """

    povs = {}
    scene_objs = {}

    for img_path in image_paths:

        img_fn = os.path.basename(img_path)
        name, ext = os.path.splitext(img_fn)
        _, img_num, proj_num = parse_image_filename(img_fn, cfg.template_img_name)
        x, y, z, h, p, r = get_coords_from_trajectory(
            trajectory,
            scene_num,
            img_num,
            cfg.template_trajectory_point
        )

        point_of_view = np.array([x, y, z])
        rotations = np.array([h, p, r])
        povs[img_num] = point_of_view.tolist()

        if not os.path.exists(img_path):
            continue

        if name not in image_segments:
            continue

        extrinsic_cam = get_extrinsic_cam(point_of_view, rotations, proj_num)
        image_objs = find_image_targets(
            points,
            image_segments[name],
            extrinsic_cam,
            point_of_view,
            common_class_names,
            cfg,
            proj_num == 4)

        scene_objs[name] = image_objs

    return scene_objs, povs


def find_image_targets(
    points: np.ndarray,
    segments: list,
    extrinsic: np.ndarray,
    point_of_view,
    common_class_names,
    cfg: Config,
    upper_image: bool = False,
    imgsz=1280):

    res = {}
    if len(segments) == 0:
        return res

    class_names_pred = common_class_names

    boxes, masks = [], []
    for seg in segments:
        mask = np.zeros((imgsz, imgsz), dtype='uint8')

        seg_arr = np.array(seg[1:-1])
        seg_arr = seg_arr.reshape(-1, 1, 2)
        seg_arr[..., 0] *= imgsz
        seg_arr[..., 1] *= imgsz
        seg_arr = seg_arr.astype('int32')

        cv2.fillPoly(mask, [seg_arr], 255)
        masks.append(mask)

        cls_id = seg[0]
        conf = seg[-1]

        # TODO: Get rid of this hardcode sh!t
        box = [seg_arr[..., 0].min() * 2048 / 1280, seg_arr[..., 1].min() * 2048 / 1280,
               seg_arr[..., 0].max() * 2048 / 1280, seg_arr[..., 1].max() * 2048 / 1280,
               conf, cls_id]
        boxes.append(box)

    points_cam, points_cam_mask = project_to_cam(points, extrinsic)

    image_objs = []
    for i, image_mask in enumerate(masks):
        mask_cls = class_names_pred[int(boxes[i][5])]

        if upper_image:
            mask_cls = 'building'

        if mask_cls == 'trees_group':
            mask_cls = 'trees_solo'

        if mask_cls not in cfg.classes_pcd:
            continue

        image_mask = cv2.resize(image_mask, (imgsz, imgsz))
        target_ids = find_target_ids(points_cam, points_cam_mask, image_mask, imgsz)

        if len(target_ids) == 0:
            continue

        pos = np.linalg.inv(extrinsic)[:3, 3:4].T

        if mask_cls not in ['signboard', 'building']:
            target_ids = find_nearest_pts(points, target_ids, pos)
            # target_ids = find_inlier_ids(points, target_ids, 0.2)

        image_obj = {
            'class_name': mask_cls,
            'target_ids': target_ids.tolist(),
            'extrinsic': extrinsic,
            'box': np.array(boxes[i][:4]),
            'segment': np.array(segments[i][1: -1]),
            'point_of_view': point_of_view,
        }
        image_objs.append(image_obj)

    return image_objs


def project_to_cam(points: np.ndarray, extrinsic: np.ndarray):

    # Remove hidden points, that is leave only visible points from camera position
    camera_position = np.linalg.inv(extrinsic)[:3, 3]
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    _, pt_map = pcd.hidden_point_removal(camera_position, radius=3000)
    pcd_sel = pcd.select_by_index(pt_map)
    hpr_points = np.asarray(pcd_sel.points)

    # Turn world coordinates into camera coordinates.
    points_cam = cv2.perspectiveTransform(hpr_points.reshape(-1, 1, 3), extrinsic).reshape(-1, 3)

    # Create mask to hide point, that places in non-visible half of space
    # If it is not done, then points from non-visible half will be projected on result image
    visibility_mask = points_cam[:, 2] > 0
    visible_points_cam = points_cam[visibility_mask]

    points_cam_mask = np.zeros((len(points),), dtype='bool')
    points_cam_mask[pt_map] = True
    points_cam_mask[points_cam_mask] = visibility_mask

    return visible_points_cam, points_cam_mask


def find_target_ids(points_cam, points_cam_mask, image_mask, imgsz) -> np.ndarray:

    if points_cam.size == 0:
        return np.zeros((0,), dtype='int32')

    intrinsic = np.array(
        [
            [imgsz / 2,         0, imgsz / 2],
            [        0, imgsz / 2, imgsz / 2],
            [        0,         0,         1],
        ]
    )
    # Project 3d point in camera coord system onto image surface
    image_points, jacobian = cv2.projectPoints(
        points_cam.reshape(-1, 1, 3),
        np.zeros((1, 3), dtype='float32'),
        np.zeros((1, 3), dtype='float32'),
        intrinsic,
        None,
    )
    image_points = image_points.reshape(-1, 2)
    image_points = image_points.astype('int32')

    # Create mask, that hides out of bounds image points
    bounding_mask = (image_points[:, 0] >= 0) & (image_points[:, 0] < image_mask.shape[1]) & \
                    (image_points[:, 1] >= 0) & (image_points[:, 1] < image_mask.shape[0])
    image_points_in_bounds = image_points[bounding_mask]

    # Create target mask to define points, that correspond to target object from image mask
    target_mask = image_mask[image_points_in_bounds[:, 1], image_points_in_bounds[:, 0]] != 0

    # Create common_target_mask for all original points (after hidden points removal),
    # where True - target, False - background
    common_target_mask = points_cam_mask.copy()
    common_target_mask[common_target_mask] = bounding_mask
    common_target_mask[common_target_mask] = target_mask

    target_ids = np.nonzero(common_target_mask)[0]
    return target_ids


def find_nearest_pts(points: np.ndarray,
                     pt_ids: np.ndarray,
                     pos: np.ndarray):


    target_points = points[pt_ids]

    # clusters_points = [target_points[clustering.labels_ == i] for i in range(num_of_clusters)]
    clustering_labels = dbscan(target_points, 1, 2)
    num_of_clusters = clustering_labels.max() + 1
    clusters_points = [
        target_points[clustering_labels == i] for i in range(num_of_clusters)
    ]

    clusters_dist = [np.linalg.norm(np.array([[pts[:, 0].mean(),
                                               pts[:, 1].mean(),
                                               pts[:, 2].mean()]]) - pos) for pts in clusters_points]

    if len(clusters_dist) == 0:
        return np.zeros((0,), dtype='int32')

    clusters_dist = np.array(clusters_dist)
    nearest_cluster_idx = clusters_dist.argmin()

    return pt_ids[clustering_labels == nearest_cluster_idx]


def parse_image_filename(img_fn: str, template: str) -> List[int]:
    number_pattern = '\{[0-9]+\}'
    meaningless_parts = re.split(number_pattern, template)
    res_numbers = []

    for i in range(len(meaningless_parts) - 1):
        prev_part = meaningless_parts[i]
        next_part = meaningless_parts[i + 1]

        num_start = re.search(prev_part, img_fn).end()
        num_end = re.search(next_part, img_fn[num_start:]).start() + num_start

        number = int(img_fn[num_start: num_end])
        res_numbers.append(number)

        img_fn = img_fn[num_end:]

    return res_numbers


def get_coords_from_trajectory(trajectory: pd.DataFrame, scene_num: int, img_num: int, template: str):
    coord_names = ['projectedX[m]', 'projectedY[m]', 'projectedZ[m]', 'heading[deg]', 'pitch[deg]', 'roll[deg]']
    x, y, z, h, p, r = trajectory.loc[template.format(scene_num, img_num)][coord_names]
    return x, y, z, h, p, r


def get_latlong_from_trajectory(trajectory: pd.DataFrame, scene_num: int, img_num: int, template: str):
    col_names = ['latitude[deg]', 'longitude[deg]']
    lat, long = trajectory.loc[template.format(scene_num, img_num)][col_names]
    return lat, long


def get_extrinsic_cam(point_of_view: np.ndarray, rotations: np.ndarray, shot_number: int) -> np.ndarray:
    """Get camera extrinsic using specific parameters.

    :param point_of_view: array with shape (3,) that contains X, Y, Z coords (m) of point of view
    :param rotations: array with shape (3,) that contains heading, pitch, roll coords (deg) of rotation
    :param shot_number: number of chosen cubic projection (0 - back, 1 - left, 2 - front, 3 - right)
    :return: array with shape (4, 4) that is camera extrinsic
    """

    extrinsic_car = get_extrinsic_car(point_of_view, rotations)
    installation_matrix = get_rot_oz(np.pi / 2) @ get_rot_oy(-np.pi / 2)
    chosen_shot_rotation = get_rot_oy(-shot_number * np.pi / 2)  # additional rotation for chosen cubic projection

    if shot_number == 4:
        extrinsic_cam = get_rot_ox(-np.pi / 2) @ get_rot_oy(np.pi) @ installation_matrix @ extrinsic_car
    elif shot_number == 5:
        extrinsic_cam = get_rot_ox(np.pi / 2) @ get_rot_oy(np.pi) @ installation_matrix @ extrinsic_car
    else:
        extrinsic_cam = chosen_shot_rotation @ installation_matrix @ extrinsic_car
    return extrinsic_cam


def get_extrinsic_car(point_of_view: np.ndarray, rotations: np.ndarray) -> np.ndarray:
    """Get car extrinsic using specific parameters. For car coord system X - axis of car direction,
    Z is directed upward, Y is perependicular to both X and Z

    :param point_of_view: array with shape (3,) that contains X, Y, Z coords (m) of point of view
    :param rotations: array with shape (3,) that contains heading, pitch, roll coords (deg) of rotation
    :return: array with shape (4, 4) that is car extrinsic
    """

    x, y, z = point_of_view
    x, y, z = float(x), float(y), float(z)
    h, p, r = rotations
    h, p, r = float(h), float(p), float(r)

    # Turning into radians and add some covertions to match our coordinate system
    h_rad = (h - 90) * np.pi / 180
    p_rad = p * np.pi / 180
    r_rad = -r * np.pi / 180

    roll_rot = get_rot_ox(r_rad)
    pitch_rot = get_rot_oy(p_rad)
    heading_rot = get_rot_oz(h_rad)

    trans = get_translation(-x, -y, -z)

    extrinsic_car = roll_rot @ pitch_rot @ heading_rot @ trans

    return extrinsic_car


def get_rot_ox(angle: float) -> np.ndarray:
    """Get homography matrix that represents rotation aroung Ox

    :param angle: angle in radians
    :return: homography matrix
    """

    mat = np.array(
        [
            [1, 0, 0, 0],
            [0, np.cos(angle), -np.sin(angle), 0],
            [0, np.sin(angle), np.cos(angle), 0],
            [0, 0, 0, 1],
        ]
    )

    return mat


def get_rot_oy(angle: float) -> np.ndarray:
    """Get homography matrix that represents rotation aroung Oy

    :param angle: angle in radians
    :return: homography matrix
    """

    mat = np.array(
        [
            [np.cos(angle), 0, np.sin(angle), 0],
            [0, 1, 0, 0],
            [-np.sin(angle), 0, np.cos(angle), 0],
            [0, 0, 0, 1],
        ]
    )

    return mat


def get_rot_oz(angle: float) -> np.ndarray:
    """Get homography matrix that represents rotation aroung Oz

    :param angle: angle in radians
    :return: homography matrix
    """

    mat = np.array(
        [
            [np.cos(angle), -np.sin(angle), 0, 0],
            [np.sin(angle), np.cos(angle), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ]
    )

    return mat


def get_translation(x: float, y: float, z: float) -> np.ndarray:
    """Get homography matrix that represents translation

    """

    mat = np.array(
        [
            [1, 0, 0, x],
            [0, 1, 0, y],
            [0, 0, 1, z],
            [0, 0, 0, 1],
        ]
    )

    return mat
