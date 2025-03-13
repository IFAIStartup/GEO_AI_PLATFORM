import os
import glob
import colorsys
import open3d as o3d
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Union, Sequence
import laspy


def parse_image_paths(image_paths: List[str], with_las_file: bool = True) -> List[dict]:
    image_dirs = []
    for image_path in image_paths:
        image_dir = os.path.dirname(image_path)
        image_dirs.append(image_dir)

    image_dirs = set(image_dirs)

    scenes_info = {}
    for image_dir in image_dirs:
        scene_num = os.path.basename(image_dir)

        reference_path = glob.glob(os.path.join(image_dir, '*.csv'))

        if len(reference_path) == 0:
            continue
        reference_path = reference_path[0]

        cur_image_paths = [path for path in image_paths if path.startswith(image_dir)]
        cur_scene_info = {
            'scene_path': image_dir,
            'image_paths': cur_image_paths,
            'reference_path': reference_path,
        }

        if not with_las_file:
            scenes_info[scene_num] = cur_scene_info
            continue

        las_paths = glob.glob(os.path.join(image_dir, '*.las'))
        if len(las_paths) == 0:
            continue

        las_path = las_paths[0]
        cur_scene_info['las_path'] = las_path
        scenes_info[scene_num] = cur_scene_info

    return scenes_info


def read_point_cloud(las_path: str, use_cached=False) -> np.ndarray:

    if use_cached and os.path.exists(las_path + '.npy'):
        return np.load(las_path + '.npy')

    # Read las file
    with laspy.open(las_path) as fh:
        las = fh.read()
    points = np.stack([las.x, las.y, las.z], axis=0).T

    # Voxel downsampling
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    down_pcd = pcd.voxel_down_sample(voxel_size=0.5)
    down_pcd_points = np.asarray(down_pcd.points)

    np.save(os.path.splitext(las_path)[0] + '.npy', down_pcd_points)
    return down_pcd_points


def read_reference(reference_path: str) -> pd.DataFrame:
    # Read trajectory-file as pandas.DataFrame and set indexing by 'file_name'
    trajectory = pd.read_csv(reference_path, sep='\t')
    trajectory.index = trajectory['file_name']
    return trajectory


def get_palette(num_of_colors: int) -> list:
    hsv_tuples = [((x / num_of_colors) % 1, 1, 1) for x in range(num_of_colors)]
    rgb_tuples = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
    return rgb_tuples


def get_fixed_hue_palette(hue: float, num_of_values: int) -> list:
    hsv_tuples = [(hue, 1, 0.5 + (x / num_of_values) % 1 * 0.5) for x in range(num_of_values)]
    rgb_tuples = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
    return rgb_tuples


def create_vis_pcd(points: np.ndarray, clusters: dict, save_pcd_path: str):
    pcd = o3d.geometry.PointCloud()
    cls_pallete = get_palette(len(clusters))

    pcd.points = o3d.utility.Vector3dVector(points)

    colors = np.zeros(points.shape, dtype='float32')
    scale = points[:, 2].max() - points[:, 2].min()
    colors[:, 0] = (points[:, 2] - points[:, 2].min()) / scale
    colors[:, 2] = colors[:, 1] = colors[:, 0]

    for i, cls_name in enumerate(clusters):
        hue, _, _ = colorsys.rgb_to_hsv(*cls_pallete[i])
        cltr_palette = get_fixed_hue_palette(hue, len(clusters[cls_name]))

        for color_num, j in enumerate(clusters[cls_name]):
            cluster_ids = clusters[cls_name][j]
            color = cltr_palette[color_num]
            colors[cluster_ids, 2], colors[cluster_ids, 1], colors[cluster_ids, 0] = color

    pcd.colors = o3d.utility.Vector3dVector(colors)
    o3d.io.write_point_cloud(save_pcd_path, pcd)



