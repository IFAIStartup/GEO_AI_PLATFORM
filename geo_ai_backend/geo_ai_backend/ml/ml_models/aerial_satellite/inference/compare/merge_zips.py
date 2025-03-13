from typing import List
import numpy as np
import pandas as pd
import geopandas as gpd
import os
import shutil
from shapely import Polygon, MultiPolygon, get_coordinates, difference, unary_union, area, GeometryCollection
import json
from geo_ai_backend.ml.ml_models.aerial_satellite.inference.join_large_tiles import join_tiles
from geo_ai_backend.ml.ml_models.aerial_satellite.inference.compare.join_tiles import save_polys_to_shp


def convert_pixel_to_geo_coords(x: float, y: float, worldfile_dict: dict):
    """Convert point coordinates to geo coordinates

        Args:
            x (float): Point X-axis coordinate
            y (float): Point Y-axis coordinate
            path_to_geo_file (str): Path to worldfile

        Returns:
            Return geo point
        """

    geo_coefs = worldfile_dict
    geo_x = geo_coefs["A"] * x + geo_coefs["B"] * y + geo_coefs["C"]
    geo_y = geo_coefs["D"] * x + geo_coefs["E"] * y + geo_coefs["F"]
    return [geo_x, geo_y]


def convert_geo_to_pixel_coords(geo_x: float, geo_y: float, worldfile_dict: str):
    geo_coefs = worldfile_dict
    x = (geo_coefs["E"] * geo_x - geo_coefs["B"] * geo_y
         + geo_coefs["B"] * geo_coefs["F"] - geo_coefs["E"] * geo_coefs["C"]) \
        / (geo_coefs["A"] * geo_coefs["E"] - geo_coefs["D"] * geo_coefs["B"])
    y = (-geo_coefs["D"] * geo_x + geo_coefs["A"] * geo_y
         + geo_coefs["D"] * geo_coefs["C"] - geo_coefs["A"] * geo_coefs["F"]) \
        / (geo_coefs["A"] * geo_coefs["E"] - geo_coefs["D"] * geo_coefs["B"])
    return x, y


def convert_to_pixel_poly(poly, worldfile_dict):
    """Convert geo polygon to polygon with pixel coords

        Args:
            poly (shapely.Polygon): Polygon for converting
            worldfile_dict (str): Worldfile

        Returns:
            Return converted polygon
        """

    exterior_coords = get_coordinates(poly.exterior)
    holes_coords = [get_coordinates(geom) for geom in list(poly.interiors)]

    pixel_exterior = [convert_geo_to_pixel_coords(*point, worldfile_dict) for point in exterior_coords]
    pixel_holes = []
    for hole in holes_coords:
        pixel_hole = [convert_geo_to_pixel_coords(*point, worldfile_dict) for point in hole]
        pixel_holes.append(pixel_hole)
    return Polygon(pixel_exterior, holes=pixel_holes)


def convert_to_geo_poly(poly, worldfile_dict):
    """Convert polygon to polygon with geo coords

        Args:
            poly (shapely.Polygon): Polygon for check
            worldfile_dict (str): Worldfile

        Returns:
            Return converted polygon
        """

    exterior_coords = get_coordinates(poly.exterior)
    holes_coords = [get_coordinates(geom) for geom in list(poly.interiors)]

    geo_exterior = [convert_pixel_to_geo_coords(*point, worldfile_dict) for point in exterior_coords]
    geo_holes = []
    for hole in holes_coords:
        geo_hole = [convert_pixel_to_geo_coords(*point, worldfile_dict) for point in hole]
        geo_holes.append(geo_hole)
    return Polygon(geo_exterior, holes=geo_holes)


def merge_files(
    list_paths_dirs: List[str],
    save_to: str,
    res_name: str,
    classes_list: list,
    remove_res_dir=True,
) -> str:
    """
    Merge zip archives with shapefiles

    list_paths_dirs (list(str)): List of paths to folders where shapefiles are stored
    save_to (str): Path archive directory
    res_name (str): Resulting archive name
    remove_res_dir (bool): Remove resulting directory flag
    epsg (int): EPSG Code for objects

    Return: None. Create merged zip archive
    """

    res_name = os.path.join(save_to, res_name)
    wf_path_list = []
    for path in list_paths_dirs:
        json_path = [i for i in os.listdir(path) if i.endswith("_json.json")][0]
        wf_path_list.append(os.path.join(path, json_path))
    shape_names = [class_name + '.shp' for class_name in classes_list]

    classes_aerials = {}
    for i in range(len(classes_list)):
        classes_aerials[shape_names[i]] = (i, classes_list[i], 'Polygon')

    json_for_project = []
    object_num = 0

    # Find main worldfile
    left_corners = []
    right_corners = []

    # wf_path_list = [os.path.join('zips_positions', wf_name) for wf_name in os.listdir('zips_positions')]
    with open(wf_path_list[0]) as worldfile:
        main_wf = json.load(worldfile)
    right_corner = convert_pixel_to_geo_coords(main_wf["image_width"],
                                               main_wf["image_height"],
                                               main_wf["worldfile"])
    right_corners.append(right_corner)
    left_corner = [main_wf["worldfile"]["C"], main_wf["worldfile"]["F"]]
    left_corners.append(left_corner)

    main_left_corner = left_corner
    main_right_corner = right_corner

    for wf_path in wf_path_list[1:]:
        with open(wf_path) as worldfile:
            wf = json.load(worldfile)
        right_corner = convert_pixel_to_geo_coords(wf["image_width"],
                                                   wf["image_height"],
                                                   wf["worldfile"])
        right_corners.append(right_corner)
        left_corner = [wf["worldfile"]["C"], wf["worldfile"]["F"]]
        left_corners.append(left_corner)

    for point in left_corners:
        if point[0] < main_left_corner[0]:
            main_left_corner[0] = point[0]
        if point[1] > main_left_corner[1]:
            main_left_corner[1] = point[1]

    for point in right_corners:
        if point[0] > main_right_corner[0]:
            main_right_corner[0] = point[0]
        if point[1] < main_right_corner[1]:
            main_right_corner[1] = point[1]

    main_wf["worldfile"]["C"], main_wf["worldfile"]["F"] = main_left_corner
    ###
    main_right_corner = convert_geo_to_pixel_coords(*main_right_corner,
                                                    main_wf["worldfile"])

    crs = main_wf["CRS"]
    for shp_name in shape_names:
        shapes = []

        for path_dir in list_paths_dirs:
            if not os.path.isdir(path_dir):
                continue
            path_to_shp = os.path.join(path_dir, shp_name)
            if shp_name not in os.listdir(path_dir):
                continue
            shapes.append(gpd.read_file(path_to_shp))

        if not shapes:
            continue

        if len(shapes) == 0:
            continue

        gdf = gpd.GeoDataFrame(pd.concat(shapes)).set_crs(crs=crs)

        positions = []
        for pos_file in wf_path_list:
            with open(pos_file) as f:
                pos_file = json.load(f)

            img_h = pos_file["image_height"]
            img_w = pos_file["image_width"]
            pos_polys = [[0, 0], [img_w, 0], [0, img_h]]
            for i in range(len(pos_polys)):
                position = pos_polys[i]
                pos_poly_coords = [position,
                                   position + np.array([img_w, 0]),
                                   position + np.array([img_w, img_h]),
                                   position + np.array([0, img_h])
                                   ]
                pos_poly = Polygon(pos_poly_coords)
                pos_poly = convert_to_geo_poly(pos_poly, pos_file["worldfile"])
                pos_poly_diff = pos_poly.buffer(-10)
                pos_polys[i] = difference(pos_poly, pos_poly_diff)

            positions.append({'main_poly': pos_polys[0], "around_polys": pos_polys[1:]})
        joining_polys = []
        for position in positions:
            main_pos_poly = gpd.GeoSeries(position["main_poly"])
            main_pos_poly = gpd.GeoDataFrame({'geometry': main_pos_poly}).set_crs(crs)
            main_polys = gdf.overlay(main_pos_poly, how="intersection")
            main_polys = list(main_polys["geometry"])

            main_polys_without_multipolys = []
            for poly in main_polys:
                if type(poly) == MultiPolygon:
                    main_polys_without_multipolys.extend(list(poly.geoms))
                else:
                    main_polys_without_multipolys.append(poly)
            main_polys = gpd.GeoDataFrame({'geometry': main_polys_without_multipolys})

            around_pos_polys = [
                gpd.GeoDataFrame({'geometry': gpd.GeoSeries(position["around_polys"][i])}).set_crs(crs)
                for i in range(len(position["around_polys"]))]
            around_polys = [gdf.overlay(around_pos_polys[i], how="intersection")
                            for i in range(len(around_pos_polys))]

            for i in range(len(around_polys)):
                around_polys_without_multipolys = []
                for poly in list(around_polys[i]["geometry"]):
                    if type(poly) == MultiPolygon:
                        around_polys_without_multipolys.extend(list(poly.geoms))
                    else:
                        around_polys_without_multipolys.append(poly)
                around_polys[i] = gpd.GeoDataFrame({'geometry': gpd.GeoSeries(around_polys_without_multipolys)})

            if shp_name == 'roads.shp':
                edge_vicinity = 3  # 0.00005
                vicinity = 5  # 0.00005
            else:
                edge_vicinity = 1.5  # 0.00004
                vicinity = 2  # 0.00002

            joining_polys.append(
                join_tiles(main_polys, around_polys, position["around_polys"], edge_vicinity, vicinity)
            )

        flatten_joining_polys = []
        for el in joining_polys:
            flatten_joining_polys.extend(el)
        joining_polys = flatten_joining_polys

        polys = []
        edge_polys = []
        if joining_polys:
            for position in positions:
                main_area_for_search = Polygon(list(position["main_poly"].exterior.coords))
                main_polys = gdf[gdf.intersects(main_area_for_search)]

                # Get rid of invalid geometries
                main_polys['geometry'] = main_polys['geometry'].buffer(0)
                
                main_edge_polys = main_polys[main_polys.intersects(position['main_poly'])]
                for i in range(len(main_edge_polys)):
                    edge_polys.append(main_edge_polys.iloc[i]['geometry'])

                main_polys = main_polys[~main_polys.intersects(position["main_poly"])]
                for i in range(len(main_polys)):
                    polys.append(main_polys.iloc[i]['geometry'])

            edge_polys = edge_polys + joining_polys
            edge_polys = unary_union(edge_polys)
            if type(edge_polys) == MultiPolygon:
                edge_polys = list(edge_polys.geoms)
            elif type(edge_polys) == Polygon:
                edge_polys = [edge_polys]
            elif type(edge_polys) == GeometryCollection:
                edge_polys = [
                    geom for geom in list(edge_polys.geoms) if type(geom) == Polygon
                ]

            if classes_aerials[shp_name][1] == "palm_tree":
                new_edge_polys = []
                for obj in edge_polys:
                    buffer_val = 0.7
                    if area(obj) > buffer_val ** 2 * 2:
                        new_polys = obj.buffer(-buffer_val)
                        if type(new_polys) == MultiPolygon:
                            new_polys = list(new_polys.geoms)
                            new_polys = [el.buffer(buffer_val) for el in new_polys]
                            new_edge_polys.extend(new_polys)
                        else:
                            new_edge_polys.append(new_polys.buffer(buffer_val))
                    else:
                        new_edge_polys.append(obj)
                edge_polys = new_edge_polys

        else:
            for i in range(len(gdf)):
                polys.append(gdf.iloc[i]['geometry'])

        if edge_polys:
            polys = polys + edge_polys

        filtred_polys = []
        for poly in polys:
            if type(poly) == Polygon:
                filtred_polys.append(poly)
            elif type(poly) == MultiPolygon:
                filtred_polys.extend(list(poly.geoms))
            elif type(poly) == GeometryCollection:
                filtred_polys.extend(
                    [geom for geom in list(poly.geoms) if type(geom) == Polygon])
        polys = filtred_polys

        ## Create json for merged project
        for poly in polys:
            poly = convert_to_pixel_poly(poly, main_wf["worldfile"])
            json_for_project.append({"object_num": object_num,
                                     "class_id": classes_aerials[shp_name][0],
                                     "class_name": classes_aerials[shp_name][1],
                                     "coordinates": {"exterior": get_coordinates(poly.exterior).tolist(),
                                                     "interior": [get_coordinates(hole).tolist() for hole in
                                                                  list(poly.interiors)]}
                                     }
                                    )
            object_num += 1
        ###

        gdf = gpd.GeoSeries(polys)
        if not os.path.exists(res_name):
            os.mkdir(res_name)
        save_polys_to_shp(gdf.tolist(), res_name, classes_aerials[shp_name][1], crs=crs,
                          geometry_type=classes_aerials[shp_name][2], make_zip=False)

    with open(res_name + ".json", 'w') as project_json:
        json.dump(json_for_project, project_json)

    twf = {"image_width": int(main_right_corner[0]),
           "image_height": int(main_right_corner[1]),
           "CRS": str(crs),
           "worldfile": main_wf["worldfile"]}

    with open(res_name + "_tfw.json", 'w') as project_tfw:
        json.dump(twf, project_tfw)

    with open(res_name + ".jgw", 'w') as wf:
        for coef in twf["worldfile"].values():
            wf.write(str(coef) + '\n')

    shutil.make_archive(res_name, 'zip', res_name)
    if remove_res_dir:
        shutil.rmtree(res_name)

    return f"{res_name}.zip"
