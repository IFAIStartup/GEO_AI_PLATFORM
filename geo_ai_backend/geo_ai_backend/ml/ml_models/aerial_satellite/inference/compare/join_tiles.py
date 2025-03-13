import numpy as np
from shapely.geometry import Polygon, Point, MultiPolygon, GeometryCollection
from shapely import distance, intersects, get_coordinates, convex_hull, area, is_empty
import matplotlib.pyplot as plt
from shapely.ops import nearest_points, unary_union
import os
import fiona
from shapely.geometry import mapping
import shutil
from fiona.crs import CRS


def convert_pixel_to_geo_coords(x: float, y: float, geo_coefs: dict):
    """Convert point coordinates to geo coordinates

        Args:
            x (float): Point X-axis coordinate
            y (float): Point Y-axis coordinate
            geo_coefs (dict): Coefficients from worldfile

        Returns:
            Return geo point
        """

    geo_x = geo_coefs["A"] * x + geo_coefs["B"] * y + geo_coefs["C"]
    geo_y = geo_coefs["D"] * x + geo_coefs["E"] * y + geo_coefs["F"]
    return geo_x, geo_y


def convert_to_geo_poly(poly, geo_coefs):
    """Convert polygon to polygon with geo coords

        Args:
            poly (shapely.Polygon): Polygon for check
            geo_coefs (dict): Coefficients from worldfile

        Returns:
            Return converted polygon
        """

    exterior_coords = get_coordinates(poly.exterior)
    holes_coords = [get_coordinates(geom) for geom in list(poly.interiors)]

    geo_exterior = [convert_pixel_to_geo_coords(*point, geo_coefs) for point in exterior_coords]
    geo_holes = []
    for hole in holes_coords:
        geo_hole = [convert_pixel_to_geo_coords(*point, geo_coefs) for point in hole]
        geo_holes.append(geo_hole)
    return Polygon(geo_exterior, holes=geo_holes)


def on_edge(poly, tile_left_corner, tile_size, edge, vicinity):
    """Check if polygon have connection with specified edge

        Args:
            poly (shapely.Polygon): Polygon for check
            tile_left_corner (tuple): Coordinates of left-upper corner of tile
            tile_size (tuple): Tuple with tile width and height
            edge (str): The edge touched by the adjacent tile ('upper', 'lower', 'left', 'right')
            vicinity (int): Vicinity at which the continuation of the object on the adjacent tile is searched.

        Returns:
            True if polygon on edge, False - otherwise
        """
    coords = np.array(get_coordinates(poly))

    if edge == 'left':
        coords += np.array([-vicinity, 0])
        next_tile_left_corner = np.array([tile_left_corner[0]-tile_size[0], tile_left_corner[1]])
    elif edge == 'top':
        coords += np.array([0, -vicinity])
        next_tile_left_corner = np.array([tile_left_corner[0], tile_left_corner[1] - tile_size[1]])
    elif edge == 'right':
        coords += np.array([vicinity, 0])
        next_tile_left_corner = np.array([tile_left_corner[0] + tile_size[0], tile_left_corner[1]])
    else:
        coords += np.array([0, vicinity])
        next_tile_left_corner = np.array([tile_left_corner[0], tile_left_corner[1] + tile_size[1]])

    next_tile_coords = [next_tile_left_corner,
                        next_tile_left_corner + np.array([tile_size[0], 0]),
                        next_tile_left_corner + np.array([tile_size[0], tile_size[1]]),
                        next_tile_left_corner + np.array([0, tile_size[1]])
                        ]

    poly = Polygon(coords)
    next_tile_poly = Polygon(next_tile_coords)

    return poly.intersects(next_tile_poly)


def get_joining_poly(tile_1, tile_2, edge_vicinity, vicinity, edge, tile_1_left_corner, tile_size=(1000,1000)):
    """Create polygons for connection polygon from tile_1 and tile_2

        Args:
            tile_1 (list): List of polygons from tile_1
            tile_2 (list): List of polygons from tile_2
            edge_vicinity (int): Vicinity at which the continuation of the object on the adjacent tile is searched.
            vicinity (int): Vicinity where objects are searched for joining
            edge (str): The edge touched by the adjacent tile ('upper', 'lower', 'left', 'right')
            tile_1_left_corner (tuple): Coordinates of left-upper corner of tile_1
            tile_size (tuple): Tuple with tile width and height

        Returns:
            List of polygons for connection
        """

    find_pair = []
    for poly in tile_1:
        if on_edge(poly, tile_1_left_corner, tile_size, edge, edge_vicinity):
            find_pair.append(poly)

    join_pairs = []
    for poly1 in find_pair:
        for poly2 in tile_2:
            if is_poly_joining(poly1, poly2, edge_vicinity):
                join_pairs.append([poly1, poly2])

    joining_polys = []
    for pair in join_pairs:
        poly1, poly2 = pair[0], pair[1]
        coords1 = get_coordinates(poly1)
        close_points_poly = []

        for point in coords1:
            point = Point(point)
            nearest_pair = nearest_points(point, poly2)
            if distance(*nearest_pair) < vicinity:
                close_points_poly.append(nearest_pair[0])
                close_points_poly.append(nearest_pair[1])

        connection_poly = convex_hull(Polygon(close_points_poly))
        joining_polys.append(connection_poly)
    return joining_polys


def yolo_to_poly(path_to_yolo, class_id, tile_size=1000, x_offset=0, y_offset=0):
    """Collects all polygons from yolofile with label = class_id

        Args:
            path_to_yolo (str): Path to the yolo markup
            class_id (int): Index of class in ['roads', 'Lights pole', 'palm_tree', 'singboard', 'building',
            'farms', 'garbage', 'tracks', 'trees_field', 'trees_group', 'trees_solo', 'traffic_sign']
            tile_size (int): Side length of a square tile
            x_offset (int): X-axis offset of tile's left-upper corner relatively field left-upper corner
            y_offset (int): Y-axis offset of tile's left-upper corner relatively field left-upper corner

        Returns:
            List of polygons with labels=class_id
        """
    if os.stat(path_to_yolo).st_size == 0:
        return []
    else:
        polys = []
        with open(path_to_yolo) as yolo_file:
            for line in yolo_file:
                line = list(map(float, line.split()))
                if int(line[0]) == class_id:
                    polys.append(line[1:])

        res_polys = []
        for poly in polys:
            poly = np.array(poly)*tile_size
            poly = poly.reshape((len(poly)//2, 2)) + np.array([x_offset, y_offset])
            poly = Polygon(poly)
            if class_id == 2:
                poly = poly.buffer(-3)
            if type(poly) == MultiPolygon:
                res_polys.extend(list(poly.geoms))
            else:
                res_polys.append(poly)
        return res_polys


def is_poly_joining(poly1, poly2, vicinity):
    """Check if one polygon intersects another

        Args:
            poly1 (shapely.Polygon): First polygon
            poly2 (shapely.Polygon): Second polygon
            vicinity (int): Vicinity where objects are searched for intersection

        Returns:
            True if polygons are intersects, False - otherwise
        """

    if poly1.intersects(poly2):
        return True
    coords1 = get_coordinates(poly1)
    for point in coords1:
        circle = Point(point).buffer(vicinity)
        if circle.intersects(poly2):
            return True
    return False


def sort_files(file_name):
    """Custom function for yolofiles sorting"""

    file_name = file_name.split('_')[-1]
    file_name = file_name.split('.')[0]
    return int(file_name)


def join_tiles(dir_with_tiles, class_id, tiles_in_col, tiles_in_row, tile_width=1000, tile_height=1000,
               edge_vicinity=20, vicinity=50, show_poly=True):
    """Connects a rectangular field of tiles.
    For example: field = 10_000x10_000 pixels image with 1000x1000 pixels tiles

        Args:
            dir_with_tiles (str): Path to the dir with yolo markups of tiles
            class_id (int): Index of class in ['roads', 'Lights pole', 'palm_tree', 'singboard', 'building',
            'farms', 'garbage', 'tracks', 'trees_field', 'trees_group', 'trees_solo', 'traffic_sign']
            tiles_in_col (int): Amount of tiles at field column
            tiles_in_row (int): Amount of tiles at field row
            tile_width (int): Tile's width
            tile_height (int): Tile's height
            edge_vicinity (int): Vicinity at which the continuation of the object on the adjacent tile is searched.
            vicinity (int): Vicinity where objects are searched for joining
            show_poly (bool): Show plots with objects polygons

        Returns:
            List of joined polygons
        """
    tiles_list = sorted(os.listdir(dir_with_tiles), key=sort_files)
    tiles_count = tiles_in_col * tiles_in_row
    joining_polys = []
    all_poly = []

    for i in range(tiles_count):
        path_to_tile = os.path.join(dir_with_tiles, tiles_list[i])
        main_tile = yolo_to_poly(path_to_tile,
                                 class_id=class_id,
                                 x_offset=tile_width*(i%tiles_in_row),
                                 y_offset=tile_height*(i//tiles_in_row))
        if len(main_tile) == 0:
            continue
        all_poly.extend(main_tile)

        if show_poly:
            for poly in main_tile:
                x, y = poly.exterior.xy
                plt.plot(x, y)

        if (i%tiles_in_row) < tiles_in_row - 1:
            path_to_right_tile = os.path.join(dir_with_tiles, tiles_list[i+1])
            right_tile = yolo_to_poly(path_to_right_tile,
                                      class_id=class_id,
                                      x_offset=tile_width*(i%tiles_in_row+1),
                                      y_offset=tile_height*(i//tiles_in_row))
            if len(right_tile) != 0:
                joining_polys.extend(get_joining_poly(main_tile, right_tile, edge_vicinity, vicinity, 'right',
                                 (tile_width*(i%tiles_in_row), tile_height*(i//tiles_in_row))))

                if show_poly:
                    for poly in right_tile:
                        x, y = poly.exterior.xy
                        plt.plot(x, y)

        if (i//tiles_in_row) < (tiles_in_col - 1):
            path_to_lower_tile = os.path.join(dir_with_tiles, tiles_list[i+tiles_in_row])
            lower_tile = yolo_to_poly(path_to_lower_tile,
                                      class_id=class_id,
                                      x_offset=tile_width*(i%tiles_in_row),
                                      y_offset=tile_height*(i//tiles_in_row + 1))

            if len(lower_tile) != 0:
                joining_polys.extend(get_joining_poly(main_tile, lower_tile, edge_vicinity, vicinity, 'lower',
                                                      (tile_width * (i % tiles_in_row), tile_height * (i // tiles_in_row))))

                if show_poly:
                    for poly in lower_tile:
                        x, y = poly.exterior.xy
                        plt.plot(x, y)

    if show_poly:
        plt.gca().invert_yaxis()
        for poly in joining_polys:
            x, y = poly.exterior.xy
            plt.plot(x, y)
        plt.savefig('res_without_join.jpg', dpi=300)
        plt.clf()

    res = unary_union([*all_poly, *joining_polys])
    if type(res) == MultiPolygon:
        res = list(res.geoms)

    if class_id == 2:
        for i in range(len(res)):
            res[i] = res[i].buffer(-5)
            if type(res[i]) == MultiPolygon:
                res[i] = list(res[i].geoms)
                biggest_poly = res[i][0]
                biggest_area = area(biggest_poly)
                for poly in res[i][1:]:
                    poly_area = area(poly)
                    if poly_area > biggest_area:
                        biggest_poly = poly
                        biggest_area = poly_area
                res[i] = biggest_poly
            res[i] = res[i].buffer(8)

    if show_poly:
        plt.gca().invert_yaxis()
        if type(res) == Polygon:
            res = [res]
        for poly in res:
            x, y = poly.exterior.xy
            plt.plot(x, y)
        plt.savefig('res_with_join.jpg', dpi=300)
    return res


def save_polys_to_shp(
    polys,
    save_to_dir,
    layer_name,
    crs,
    path_to_geo_file=0,
    geometry_type='Polygon',
    make_zip=True,
    remove_res_dir=True,
    status=[]
):

    """Save list of polygons to .shp file
        Args:
            polys (list): List of polygons
            path_to_geo_file (str): Path to worldfile for coords converting
            save_to (str): Path to save folder
            epsg (int): EPSG code

        Returns:
            .zip with .shp file
        """

    geo_polys = []

    if geometry_type == "Road":
        geometry_type = "Polygon"
    schema = {
        "geometry": geometry_type,
        "properties": {"name": 'str:100',
                       "type": 'str:100'}
    }
    if status:
        schema["properties"]["name_old"] = 'str:100'
        schema["properties"]["name_new"] = 'str:100'

    if type(polys) == MultiPolygon:
        polys = list(polys.geoms)
    if type(polys) == Polygon:
        polys = [polys]
    if type(polys) == GeometryCollection:
        polys = [geom for geom in list(polys.geoms) if type(geom) == Polygon]

    for poly in polys:
        if not is_empty(poly):
            geo_polys.append(poly)
    with fiona.open(save_to_dir, 'w', 'ESRI Shapefile', schema, layer=layer_name, crs=crs) as shape_file:
        for i in range(len(geo_polys)):
            shp_el = {'geometry': mapping(geo_polys[i]), "properties": {"name": str(i), "type": layer_name}}
            if status:
                if layer_name in ['roads', 'tracks']:
                    shp_el["properties"]["name_old"] = None
                    shp_el["properties"]["name_new"] = None
                else:
                    if status[i]["Status"] == "Deleted":
                        shp_el["properties"]["name_old"] = str(status[i]["Old object id"])
                        shp_el["properties"]["name_new"] = None
                    if status[i]["Status"] == "New":
                        shp_el["properties"]["name_old"] = None
                        shp_el["properties"]["name_new"] = str(status[i]["New object id"])
                    if status[i]["Status"] in ["Unchanged", "Changed"]:
                        shp_el["properties"]["name_old"] = str(status[i]["Old object id"])
                        shp_el["properties"]["name_new"] = str(status[i]["New object id"])
            shape_file.write(shp_el)

    if make_zip:
        shutil.make_archive(save_to_dir, 'zip', save_to_dir)
        if remove_res_dir:
            shutil.rmtree(save_to_dir)
