from typing import List
import pandas as pd
import geopandas as gpd
import os
import shutil


def merge_zips(
    list_paths_dirs: List[str],
    save_to: str,
    name_zip: str,
    classes_list: list,
    remove_res_dir=True
) -> str:
    """
    Merge zip archives with shapefiles

    list_paths_dirs (list(str)): List of paths to folders where shapefiles are stored
    save_to (str): Path archive directory
    remove_res_dir (bool): Remove resulting directory flag

    Return: The path of the zip archive created
    """

    shape_names = [class_name + '.shp' for class_name in classes_list]

    save_to = os.path.join(save_to, name_zip)
    for shp_name in shape_names:
        shapes = []
        for path_dir in list_paths_dirs:
            if not os.path.isdir(path_dir):
                continue
            path_to_shp = os.path.join(path_dir, shp_name)
            if shp_name not in os.listdir(path_dir):
                continue
            gdf_temp = gpd.read_file(path_to_shp)
            if 'text' in gdf_temp.columns:
                if gdf_temp['text'].dtype != object:
                    gdf_temp['text'] = gdf_temp['text'].astype(object)
            shapes.append(gdf_temp)

        if not shapes:
            continue

        gdf = gpd.GeoDataFrame(pd.concat(shapes, ignore_index=True, sort=False))
        if not os.path.exists(save_to):
            os.mkdir(save_to)
        path_to_save = os.path.join(save_to, shp_name)
        gdf.to_file(path_to_save, encoding='utf-8')

    shutil.make_archive(save_to, 'zip', save_to)
    if remove_res_dir:
        shutil.rmtree(save_to)
    path_zip = f"{save_to}.zip"
    return path_zip
