import os
import cv2
import numpy as np
from typing import Tuple, List, Dict, Union, Sequence
import fiona
from fiona.crs import CRS
import geopandas as gpd
import pyproj
import shapely
import json
from shapely.geometry import mapping, Point, Polygon, LineString


def create_trajectory_lines(
        povs_list: List[Dict[int, list]],
        src_crs: pyproj.CRS,
        dst_crs: pyproj.CRS) -> gpd.GeoDataFrame:

    objects = []

    for povs in povs_list:
        if len(povs) == 0:
            continue
        if len(povs) == 1:
            # povs.append(povs[0])
            coords = [list(povs.values())[0]] * 2
        else:
            # Sort POVs' order by their image number to build a correct line
            img_nums = list(povs.keys())
            img_nums.sort()

            coords = [povs[i] for i in img_nums]

        line = LineString(coords)
        objects.append(line)

    gdf = gpd.GeoDataFrame(objects, columns=['geometry'], crs=src_crs)
    gdf = gdf.to_crs(crs=dst_crs)

    return gdf



def create_clusters_geometries(
    result_points: np.ndarray,
    result_clusters_ids,
    src_crs: pyproj.CRS,
    dst_crs: pyproj.CRS) -> Dict[str, gpd.GeoDataFrame]:
    """Turn found clusters into GeoDataFrames, converting coordinates from source CRS to destination CRS

    Args:
        result_points (np.ndarray): numpy array (N, 3) of points from all scenes
        result_clusters_ids (__type__):
        src_crs (pyproj.CRS): source coordinate reference system, that result points have
        dst_crs (pyproj.CRS): destination coordinate reference system
        ## texts (dict, optional): dict of text on . Defaults to None.

    Returns:
        Dict[str, gpd.GeoDataFrame]: dict with keys as categories and corresponding GeoDataFrames as values
    """

    geo_data_frames = {}
    for cat in result_clusters_ids:
        if cat == 'building':
            geometry = get_cluster_polygons(result_points, result_clusters_ids[cat])
        else:
            geometry = get_cluster_centers(result_points, result_clusters_ids[cat])

        gdf = gpd.GeoDataFrame(geometry, columns=['geometry'], crs=src_crs)
        gdf = gdf.to_crs(crs=dst_crs)
        geo_data_frames[cat] = gdf

    return geo_data_frames


def convert_geometries_to_shp(
    geometries: Dict[str, gpd.GeoDataFrame],
    classes_pcd: List[str],
    save_path: str,
    epsg_code: int = 4326,
    texts: dict = None,
):
    texts = {} if texts is None else texts
    obj_num = 0
    json_description = []

    for category_name in geometries:
        if len(geometries[category_name]) == 0:
            continue

        geometry_type = geometries[category_name]['geometry'][0].geom_type
        properties = {'name': 'str',
                      'type': 'str:100'} if category_name not in texts else {'name': 'str',
                                                                             'type': 'str:100',
                                                                             'text': 'str'}
        schema = {
            'geometry': geometry_type,
            'properties': properties,
        }

        os.makedirs(save_path, exist_ok=True)
        category_id = {pair[0]: pair[1] for pair in zip(classes_pcd, range(len(classes_pcd)))}

        with fiona.open(save_path, 'w', 'ESRI Shapefile',
                        schema,
                        crs=CRS.from_epsg(epsg_code),
                        layer=category_name,
                        encoding="utf-8") as shape_file:

            for obj in geometries[category_name]['geometry']:
                if type(obj) == Polygon:
                    exterior_coords = shapely.get_coordinates(obj.exterior).tolist()
                    interior_coords = [shapely.get_coordinates(hole) for hole in
                                       list(obj.interiors)]
                if type(obj) == Point:
                    exterior_coords = shapely.get_coordinates(obj).tolist()
                    interior_coords = []
                json_description.append({'object_num': obj_num,
                                         'class_id': category_id[category_name],
                                         'class_name': category_name,
                                         'coordinates': {'exterior': exterior_coords,
                                                         'interior': interior_coords}
                                         })
                obj_num += 1

            for i in range(len(geometries[category_name])):
                obj_properties = {'name': str(i + 1), 'type': category_name}
                if category_name in texts:
                    obj_properties['text'] = ''
                if category_name in texts and i in texts[category_name]:
                    obj_properties['text'] = texts[category_name][i]

                shape_file.write({
                    'geometry': mapping(geometries[category_name]['geometry'][i]),
                    'properties': obj_properties,
                })

    path_json = save_path.split('/')[-1] + ".json"
    path = f"{save_path}/{path_json}"
    with open(path, 'w') as project_json:
        json.dump(json_description, project_json)


def convert_trajectories_to_shp(trajectory_lines: gpd.GeoDataFrame, save_shp_path: str):
    os.makedirs(save_shp_path, exist_ok=True)
    trajectory_lines["name"] = [str(i) for i in range(1, len(trajectory_lines) + 1)]
    trajectory_lines["type"] = ['trajectory' for _ in range(1, len(trajectory_lines) + 1)]
    trajectory_lines.to_file(os.path.join(save_shp_path, 'trajectory.shp'))



def get_cluster_polygons(
    points: np.ndarray,
    clusters: Dict[str, np.ndarray],
    voxel_size=0.5
) -> List[Polygon]:
    polygons = []
    for cluster_id in clusters:
        cluster_points = points[clusters[cluster_id]]
        cluster_points /= voxel_size
        x_min = cluster_points[:, 0].min()
        y_min = cluster_points[:, 1].min()

        cluster_points[:, 0] -= x_min
        cluster_points[:, 1] -= y_min

        cluster_points = cluster_points.astype('int32')
        img = np.zeros((cluster_points[:, 1].max() + 1, cluster_points[:, 0].max() + 1),
                       dtype='uint8')
        img[cluster_points[:, 1], cluster_points[:, 0]] = 255
        # cv2.imshow('img', img)
        # cv2.waitKey()

        contours, hierarchy = cv2.findContours(
            img,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        for cnt in contours:
            cnt = cnt.astype('float64')
            cnt[..., 0] += x_min
            cnt[..., 1] += y_min
            cnt *= voxel_size

            if cnt.size <= 4:
                continue

            polygons.append(Polygon(cnt.reshape(-1, 2).tolist()))

    return polygons



def get_cluster_centers(
    points: np.ndarray,
    clusters: Dict[str, np.ndarray]
) -> List[Point]:
    centers = []
    if len(clusters) == 0:
        return []

    num_of_clusters = len(clusters)
    for i in range(num_of_clusters):
        cluster_points = points[clusters[i]]

        if len(cluster_points) == 0:
            continue

        center = [cluster_points[:, 0].mean(), cluster_points[:, 1].mean(),
                  cluster_points[:, 2].min()]
        centers.append(center)

    centers = np.array(centers)
    centers_xy = centers[:, 0:2]
    centers_xy_pt = [Point(xy) for xy in centers_xy]
    return centers_xy_pt


