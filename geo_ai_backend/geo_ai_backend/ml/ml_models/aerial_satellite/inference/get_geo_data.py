import numpy as np
import rasterio
import os
import geopandas as gpd
import pyproj
from shapely.geometry import Point
from typing import List
import csv
from geo_ai_backend.project.schemas import (
    GeoCoordinateSchemas,
    CoordinatesSchemas,
    FieldNameEnum,
)


def get_geo_data(path: str) -> GeoCoordinateSchemas:
    """Get coordinates of center of tif file."""
    img_name = os.path.splitext(os.path.basename(path))[0]
    with rasterio.open(path) as src:
        crs = src.crs
        bounds = src.bounds

    center = (
        bounds[0] + (bounds[2] - bounds[0]) / 2,
        bounds[1] + (bounds[3] - bounds[1]) / 2,
    )
    center = np.array(center).reshape(1, -1)
    center_pt = [Point(xy) for xy in center]
    centers_loc = gpd.GeoDataFrame(center_pt, columns=["geometry"], crs=crs)
    centers_loc = centers_loc.to_crs(crs=pyproj.CRS.from_epsg(4326))

    coordinates = CoordinatesSchemas(
        lon=centers_loc.geometry.x[0], lat=centers_loc.geometry.y[0]
    )
    return GeoCoordinateSchemas(coordinates=coordinates, name=img_name)


def get_all_geo_data(paths: List[str]) -> List[GeoCoordinateSchemas]:
    for path in paths:
        yield get_geo_data(path=path)


def create_csv_file(data: List[GeoCoordinateSchemas], name_csv: str) -> str:
    path_csv = f"{name_csv}.csv"
    with open(path_csv, mode="w", newline="") as csv_file:
        fieldnames = [
            FieldNameEnum.name,
            FieldNameEnum.longitude,
            FieldNameEnum.latitude,
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for i in data:
            writer.writerow(
                {
                    FieldNameEnum.name: i.name,
                    FieldNameEnum.longitude: i.coordinates.lon,
                    FieldNameEnum.latitude: i.coordinates.lat,
                }
            )
    return path_csv
