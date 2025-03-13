import shutil

import fiona
from fiona.crs import CRS
from shapely.geometry import mapping, Point, Polygon
import numpy as np
import os
import re
from typing import List, Dict, Tuple


def get_geo_coefs_from_file(path_to_geo_file: str):
    coef_names = ["A", "D", "B", "E", "C", "F"]
    with open(path_to_geo_file, "r") as world_file:
        coefs = [float(line) for line in world_file]
    return dict(zip(coef_names, coefs))


def convert_pixel_to_geo_coords(x: float, y: float, path_to_geo_file: str, x_offset, y_offset):
    geo_coefs = get_geo_coefs_from_file(path_to_geo_file)
    x += x_offset
    y += y_offset
    geo_x = geo_coefs["A"] * x + geo_coefs["B"] * y + geo_coefs["C"]
    geo_y = geo_coefs["D"] * x + geo_coefs["E"] * y + geo_coefs["F"]
    return geo_x, geo_y


def convert_single_yolo_to_shp(seg_class: List[Dict[str, List]], save_to, worldfile_dir='', epsg_code=4326,
                               scale_factor=1000):
    """Convert dictionary to .shp file

        Args:
            yolo_dir (str): Path to the dir with yolofiles
            save_to (str): The name of the .zip file where .shp layers are saved
            worldfile_dir (str): Path to the dir with worldfiles
            epsg_code (int): The EPSG code of geodetic coordinate system
            scale_factor (float): Scale factor for yolo values

        Returns:
            None. Saves the .zip with .shp layers
        """

    objects = {}
    class_names = ['roads', 'Lights pole', 'palm_tree', 'singboard',
                   'building', 'farms', 'garbage', 'tracks', 'trees_field',
                   'trees_group', 'trees_solo', 'traffic_sign']

    subtile_num = int(re.findall(r'(_[\d]+)', save_to)[-1][1:])
    x_offset = subtile_num % 5 * 1000
    y_offset = subtile_num // 5 * 1000
    worldfile = re.search(r'[A-Za-z_ ]+\d+_\d+_\d+', save_to)[0] + '.tfw'
    worldfile_path = os.path.join(worldfile_dir, worldfile)

    # yolo_list = os.listdir(yolo_dir)

    for found_object in seg_class:
        class_name = class_names[int(found_object['class'])]
        if class_name not in objects:
            objects[class_name] = []

        pixel_points = np.array(found_object['segment']).reshape(-1, 2)
        geo_coords = [convert_pixel_to_geo_coords(point[0], point[1], worldfile_path, x_offset, y_offset)
                      for point in pixel_points]
        objects[class_name].append(geo_coords)
        pass

    for category_name in objects.keys():
        if len(objects[category_name][0]) > 1:
            geometry_type = 'Polygon'
        else:
            geometry_type = 'Point'

        schema = {
            'geometry': geometry_type,
            'properties': {'id': 'int'},
        }

        with fiona.open(save_to, 'w', 'ESRI Shapefile', schema, crs=CRS.from_epsg(epsg_code),
                        layer=category_name) as shape_file:
            obj_id = 1
            for obj in objects[category_name]:
                if geometry_type == 'Polygon':
                    # TODO: check trouble with polygons
                    if len(obj) < 3:
                        continue
                    obj = Polygon(obj)
                else:
                    obj = Point(obj)

                shape_file.write({
                    'geometry': mapping(obj),
                    'properties': {'id': obj_id},
                })
                obj_id += 1


def convert_yolo_to_shp(yolo_dir: str, save_to: str, worldfile_dir='', epsg_code=4326, scale_factor=1000):
    """Convert dictionary to .shp file

        Args:
            yolo_dir (str): Path to the dir with yolofiles
            save_to (str): The name of the .zip file where .shp layers are saved
            worldfile_dir (str): Path to the dir with worldfiles
            epsg_code (int): The EPSG code of geodetic coordinate system
            scale_factor (float): Scale factor for yolo values

        Returns:
            None. Saves the .zip with .shp layers
        """

    objects = {}
    class_names = ['roads', 'Lights pole', 'palm_tree', 'singboard',
                   'building', 'farms', 'garbage', 'tracks', 'trees_field',
                   'trees_group', 'trees_solo', 'traffic_sign']
    yolo_list = os.listdir(yolo_dir)

    for yolofile in yolo_list:
        yolo_path = os.path.join(yolo_dir, yolofile)
        with open(yolo_path, "r") as yolo:
            subtile_num = int(re.findall(r'(_[\d]+)', yolofile)[-1][1:])
            x_offset = subtile_num % 5 * 1000
            y_offset = subtile_num // 5 * 1000
            worldfile = re.search(r'[A-Za-z_ ]+\d+_\d+_\d+', yolofile)[0] + '.tfw'
            worldfile_path = os.path.join(worldfile_dir, worldfile)

            for line in yolo:
                coords = line.split()
                class_name = class_names[int(coords[0])]
                if class_name not in objects:
                    objects[class_name] = []
                pixel_coords = np.fromiter(map(float, coords[1:]), dtype=np.float64) * scale_factor
                pixel_points = pixel_coords.reshape((int(len(pixel_coords) / 2), 2))
                geo_coords = [convert_pixel_to_geo_coords(point[0], point[1], worldfile_path, x_offset, y_offset)
                              for point in pixel_points]
                objects[class_name].append(geo_coords)

    for category_name in objects.keys():
        if len(objects[category_name][0]) > 2:
            # TODO: check trouble with polygons
            try:
                obj = Polygon(obj)
            except:
                continue
        else:
            geometry_type = 'Point'

        schema = {
            'geometry': geometry_type,
            'properties': {'id': 'int'},
        }

        with fiona.open(save_to, 'w', 'ESRI Shapefile', schema, crs=CRS.from_epsg(epsg_code),
                        layer=category_name) as shape_file:
            obj_id = 1
            for obj in objects[category_name]:
                if geometry_type == 'Polygon':
                    obj = Polygon(obj)
                else:
                    obj = Point(obj)

                shape_file.write({
                    'geometry': mapping(obj),
                    'properties': {'id': obj_id},
                })
                obj_id += 1

    # shutil.make_archive(save_to, 'zip', save_to)
