import numpy as np
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely import area, intersection, difference
import json
from shapely import unary_union
import os
import shutil

from geo_ai_backend.ml.ml_models.aerial_satellite.inference.compare.join_tiles import (
    save_polys_to_shp
)


def prepare_objects_for_change_detection_360(
    path_to_json_file: str,
    class_name: str,
) -> list:
    """
    Prepare objects from .json for change detection
    :param path_to_json_file: Path to the .json file with objects
    :param class_name: Class name of the objects
    :return: List with prepared objects
    """
    with open(path_to_json_file) as obj_json:
        objects = json.load(obj_json)

    prepared_objects = []
    geom_type = 'None'
    for obj in objects:
        if obj['class_name'] == class_name:
            prepared_obj = {'id': obj['object_num'],
                            'class_name': obj['class_name']}
            exterior_coords = obj['coordinates']['exterior']
            interior_coords = obj['coordinates']['interior']
            if len(exterior_coords) > 1:
                prepared_obj['geometry'] = 'Polygon'
            else:
                prepared_obj['geometry'] = 'Point'

            prepared_obj['coordinates'] = {'exterior': exterior_coords,
                                           'interior': interior_coords}
            prepared_objects.append(prepared_obj)

    if len(prepared_objects) > 0:
        geom_type = prepared_obj['geometry']

    return prepared_objects, geom_type


def compare_polygon_objects_360(old_objects: list, new_objects: list, area_ratio: float):
    """
    Compare two lists of objects which presented by polygons
    :param old_objects: Prepared list of 1st project objects
    :param new_objects: Prepared list of 2nd project objects
    :param area_ratio:
    :return: Two dicts with pairs description and four lists with polygons
    for deleted, unchanged, changed, added objects
    """
    old_idx = np.array([obj['id'] for obj in old_objects])
    new_idx = np.array([obj['id'] for obj in new_objects])

    old_polys = []
    for obj in old_objects:
        obj = Polygon(obj['coordinates']['exterior'],
                      holes=obj['coordinates']['interior'])
        if area(obj.buffer(0)) == 0:
            old_polys.append(obj.buffer(0.000001))
        else:
            old_polys.append(obj.buffer(0))
    old_polys = np.array(old_polys)

    new_polys = []
    for obj in new_objects:
        obj = Polygon(obj['coordinates']['exterior'],
                      holes=obj['coordinates']['interior'])
        if area(obj.buffer(0)) == 0:
            new_polys.append(obj.buffer(0.000001))
        else:
            new_polys.append(obj.buffer(0))
    new_polys = np.array(new_polys)

    deleted_polys = []
    unchanged_polys = []
    changed_polys = []
    added_polys = []

    deleted_polys_statuses = []
    unchanged_polys_statuses = []
    changed_polys_statuses = []
    added_polys_statuses = []

    used_new = []
    used_old = []
    pairs_old = np.zeros(len(old_idx), dtype=object)
    pairs_new = np.zeros(len(new_idx), dtype=object)

    for i in range(len(old_polys)):
        old_area = area(old_polys[i])
        intersection_areas = np.array(
            [area(intersection(old_polys[i], poly)) / old_area for poly in new_polys])
        nearest_poly_idx = np.asarray(intersection_areas > area_ratio).nonzero()[0]
        if len(nearest_poly_idx) == 0:
            status = {"Status": 'Deleted',
                      "Old object id": old_idx[i]}
            pairs_old[i] = status
            deleted_polys_statuses.append(status)
            deleted_polys.append(old_polys[i])
        else:
            nearest_polys = {idx: intersection_areas[idx] for idx in nearest_poly_idx}
            nearest_polys = dict(sorted(nearest_polys.items(), key=lambda item: item[1]))
            for poly_idx in nearest_polys:
                if poly_idx not in used_new and i not in used_old:
                    intersection_area = intersection_areas[poly_idx]
                    nearest_poly_idx = poly_idx
                    status = {"Status": '',
                              "Old object id": old_idx[i],
                              "New object id": new_idx[nearest_poly_idx],
                              "Old area": old_area,
                              "New area": area(new_polys[nearest_poly_idx]),
                              "Intersection area": intersection_area}
                    if 0.8 < area(new_polys[nearest_poly_idx]) / old_area < 1.2:
                        status['Status'] = 'Unchanged'
                        pairs_old[i] = status
                        pairs_new[nearest_poly_idx] = status
                        unchanged_polys.append(old_polys[i])
                        unchanged_polys_statuses.append(status)
                    else:
                        status['Status'] = 'Changed'
                        pairs_old[i] = status
                        pairs_new[nearest_poly_idx] = status
                        changed_polys.append(new_polys[nearest_poly_idx])
                        changed_polys_statuses.append(status)
                    used_new.append(nearest_poly_idx)
                    used_old.append(i)

    for i in np.asarray(pairs_new == 0).nonzero()[0]:
        status = {"Status": 'New',
                  "New object id": new_idx[i]}
        pairs_new[i] = status
        added_polys_statuses.append(status)
        added_polys.append(new_polys[i])
    for i in np.asarray(pairs_old == 0).nonzero()[0]:
        status = {"Status": 'Deleted',
                  "Old object id": old_idx[i]}
        pairs_old[i] = status
        deleted_polys_statuses.append(status)
        deleted_polys.append(old_polys[i])

    status = {"deleted": deleted_polys_statuses,
              "unchanged": unchanged_polys_statuses,
              "changed": changed_polys_statuses,
              "added": added_polys_statuses}
    return pairs_old, pairs_new, deleted_polys, unchanged_polys, changed_polys, added_polys, status


def remove_road_parts_360(polys: list, open_radius: float) -> list:
    """
    Remove tiny polygon's artifacts
    :param polys: List of polygons
    :param open_radius: Radius for open operation
    :return: Cleared list of polygons
    """
    if type(polys) != Polygon:
        polys = MultiPolygon(polys)
    polys = polys.buffer(-open_radius, cap_style='square')
    polys = polys.buffer(open_radius, cap_style='square')
    return polys


def compare_roads_360(old_objects: list, new_objects: list, open_radius: float):
    """
    Compare roads polygons
    :param old_objects: Prepared list of 1st project objects
    :param new_objects: Prepared list of 2nd project objects
    :param open_radius: Radius for open operation
    :return: Three lists with polygons for deleted, changed, added roads
    """
    old_roads = np.array([Polygon(obj['coordinates']['exterior'],
                                  holes=obj['coordinates']['interior']).buffer(0)
                          for obj in old_objects])
    new_roads = np.array([Polygon(obj['coordinates']['exterior'],
                                  holes=obj['coordinates']['interior']).buffer(0)
                          for obj in new_objects])

    old_roads = unary_union(old_roads)
    new_roads = unary_union(new_roads)

    deleted_roads = remove_road_parts_360(difference(old_roads, new_roads), open_radius)
    unchanged_roads = intersection(old_roads, new_roads)
    added_roads = remove_road_parts_360(difference(new_roads, old_roads), open_radius)

    status = {"deleted": [],
              "unchanged": [],
              "added": []}
    return '', '', deleted_roads, unchanged_roads, '', added_roads, status


def compare_point_objects_360(old_objects: list, new_objects: list, vicinity: float):
    """
    Compare two lists of objects which presented by points
    :param old_objects:
    :param new_objects:
    :param vicinity:
    :return: Two dicts with pairs description and three lists with points
    for deleted, unchanged and added objects
    """
    old_idx = np.array(
        [obj['id'] for obj in old_objects if len(obj['coordinates']['exterior'])])
    new_idx = np.array(
        [obj['id'] for obj in new_objects if len(obj['coordinates']['exterior'])])

    old_points = np.array(
        [obj['coordinates']['exterior'] for obj in old_objects if
         len(obj['coordinates']['exterior'])])
    old_points = old_points.reshape((len(old_points), 2))
    new_points = np.array(
        [obj['coordinates']['exterior'] for obj in new_objects if
         len(obj['coordinates']['exterior'])])
    new_points = new_points.reshape((len(new_points), 2))

    deleted_points = []
    unchanged_points = []
    added_points = []

    deleted_points_statuses = []
    unchanged_points_statuses = []
    added_points_statuses = []

    used_new = []
    pairs_old = np.zeros(len(old_idx), dtype=object)
    pairs_new = np.zeros(len(new_idx), dtype=object)

    for i in range(len(old_points)):
        distances = np.linalg.norm(new_points - old_points[i], axis=1)
        nearest_points_idx = np.asarray(distances < vicinity).nonzero()[0]
        if len(nearest_points_idx) == 0:
            status = {"Status": 'Deleted',
                      "Old object id": old_idx[i]}
            pairs_old[i] = status
            deleted_points.append(Point(old_points[i]))
            deleted_points_statuses.append(status)
        else:
            min_distance = np.inf

            nearest_points = {idx: distances[idx] for idx in nearest_points_idx}
            nearest_points = dict(
                sorted(nearest_points.items(), key=lambda item: item[1]))
            for point_idx in nearest_points:
                if distances[point_idx] < min_distance and point_idx not in used_new:
                    min_distance = distances[point_idx]
                    nearest_point_idx = point_idx
            if min_distance != np.inf:
                used_new.append(nearest_point_idx)
                status = {"Status": 'Unchanged',
                          "Old object id": old_idx[i],
                          "New object id": new_idx[nearest_point_idx],
                          "Distance": distances[nearest_point_idx]}
                pairs_old[i] = status
                pairs_new[nearest_point_idx] = status
                unchanged_points.append(Point(old_points[i]))
                unchanged_points_statuses.append(status)

    for i in np.asarray(pairs_new == 0).nonzero()[0]:
        status = {"Status": 'New',
                  "New object id": new_idx[i]}
        pairs_new[i] = status
        added_points.append(Point(new_points[i]))
        added_points_statuses.append(status)
    for i in np.asarray(pairs_old == 0).nonzero()[0]:
        status = {"Status": 'Deleted',
                  "Old object id": old_idx[i]}
        pairs_old[i] = status
        deleted_points.append(Point(old_points[i]))
        deleted_points_statuses.append(status)

    status = {"deleted": deleted_points_statuses,
              "unchanged": unchanged_points_statuses,
              "added": added_points_statuses}
    return pairs_old, pairs_new, deleted_points, unchanged_points, '', added_points, status


def change_detection_360(
    save_to: str,
    name_zip: str,
    path_to_json_project_old: str,
    path_to_json_project_new: str,
    classes_list: list,
    vicinity=0.01,
    area_ratio=0.8,
    open_radius=1
):
    """
    Change detection for two projects
    :param save_to: Dir name for change detection results
    :param name_zip: Name zip archives
    :param vicinity: Search vicinity for points compare
    :param area_ratio: Area ration for polygons compare
    :param open_radius: Open radius for roads compare
    :param remove_res_dir: Remove dirs with resulting shapefiles
    :return: List with objects statuses. Dir with shapefiles
    """

    classes_360 = {}
    for i in range(len(classes_list)):
        shp_name = classes_list[i] + '.shp'
        classes_360[shp_name] = (i, classes_list[i])

    res_old = []
    res_new = []
    if not os.path.isdir(save_to):
        os.mkdir(save_to)

    change_detection_keys = ["old_status", "new_status", "deleted",
                             "unchanged", "changed", "added", "status"]
    for key in change_detection_keys[2:len(change_detection_keys)-1]:
        key_dir = os.path.join(save_to, key)

        if not os.path.isdir(key_dir):
            os.mkdir(key_dir)

    for cls in classes_360.values():
        old_objs, old_geom_type = prepare_objects_for_change_detection_360(
            path_to_json_project_old, cls[1]
        )
        new_objs, new_geom_type = prepare_objects_for_change_detection_360(
            path_to_json_project_new, cls[1]
        )

        geom_type = 'None'
        if old_geom_type != 'None':
            geom_type = old_geom_type
        elif new_geom_type != 'None':
            geom_type = new_geom_type
        else:
            continue

        if geom_type == 'Point':
            change_detection_res = compare_point_objects_360(old_objs, new_objs,
                                                             vicinity=vicinity)
        elif geom_type == 'Polygon':
            change_detection_res = compare_polygon_objects_360(old_objs, new_objs,
                                                               area_ratio=area_ratio)
        else:
            change_detection_res = compare_roads_360(old_objs, new_objs,
                                                     open_radius=open_radius)

        change_detection_res = dict(zip(change_detection_keys, change_detection_res))

        for key in change_detection_keys[2:len(change_detection_keys)-1]:
            if change_detection_res[key]:
                save_polys_to_shp(change_detection_res[key], os.path.join(save_to, key),
                                  cls[1],
                                  geometry_type=geom_type, make_zip=False, crs='EPSG:4326',
                                  status=change_detection_res["status"][key])

        res_old.append((cls[1], change_detection_res["old_status"]))
        res_new.append((cls[1], change_detection_res["new_status"]))

    paths_zips = []
    action_name = []
    for key in change_detection_keys[2:len(change_detection_keys)-1]:
        key_dir = os.path.join(save_to, key)
        name = f"{key_dir}_{name_zip}"
        if bool(os.listdir(key_dir)):
            shutil.make_archive(name, 'zip', key_dir)
            paths_zips.append(f"{name}.zip")
            action_name.append(key)
        if os.path.isdir(key_dir):
            shutil.rmtree(key_dir)

    return [res_old, res_new], action_name, paths_zips
