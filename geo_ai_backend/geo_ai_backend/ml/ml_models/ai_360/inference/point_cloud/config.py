import pyproj
from typing import List, Tuple
from dataclasses import dataclass


DEFAULT_WKT = 'PROJCS["40 North",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["World Geodetic System 1984",6378137,298.257223563],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["Degree",0.01745329251994,AUTHORITY["EPSG","9102"]],AXIS["Long",EAST],AXIS["Lat",NORTH],AUTHORITY["EPSG","4326"]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000],PARAMETER["False_Northing",0],PARAMETER["Latitude_Of_Origin",0],PARAMETER["Central_Meridian",57],PARAMETER["Scale_Factor",0.9996],UNIT["Meter",1,AUTHORITY["EPSG","9001"]],AXIS["East",EAST],AXIS["North",NORTH]]'
DEFAULT_EPSG = 4326


@dataclass
class Config:
    """Configuration class for 360 algorithns"""

    # Inference configuration
    inference_type: str = 'triton'
    lang_cls_model_path: str = 'effnetb0_051023'

    # The result point cloud classes that go to .pcd file and .shp files
    classes_pcd: Tuple[str] = (
        'Lights pole',
        'palm_tree',
        'signboard',
        'building',
        'trees_solo',
        'traffic_sign',
    )


    # Template for image name (0 - pano number, 1 - image number, 2 - proejction number)
    template_img_name: str = 'Unnamed Run  {0}_Camera 4 360_{1}_{2}.jpg'
    # template_img_name: str = 'pano_{0:06d}_{1:06d}_{2}.jpg'
    template_img_name_alternative: str = r'pano_(\d+)_(\d+)_(\d+)\.jpg'

    # Template for trajectory point in trajectory file (0 - pano number, 1 - image number)
    template_trajectory_point: str = 'pano_{0:06d}_{1:06d}'

    # Lidar coordinate reference system (source CRS) from *.las.txt file
    # TODO: find a way to extract this data
    src_crs: pyproj.CRS = pyproj.CRS.from_wkt(DEFAULT_WKT)

    # Result coordinate reference system (destionation CRS) which represents standart latitude-longitude
    dst_crs: pyproj.CRS = pyproj.CRS.from_epsg(DEFAULT_EPSG)


# field(default_factory=list)

