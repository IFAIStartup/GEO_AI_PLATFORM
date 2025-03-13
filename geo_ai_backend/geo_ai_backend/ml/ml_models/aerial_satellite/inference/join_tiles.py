import os
import numpy as np
import fiona
from shapely.geometry import Polygon, LineString, Point, MultiPolygon
from shapely import distance, intersects, get_coordinates, convex_hull, area, \
    get_exterior_ring, is_empty, intersection, difference, is_valid, make_valid
from shapely.ops import nearest_points, unary_union, cascaded_union, snap
from shapely.geometry import mapping
from shapely.geometry.collection import GeometryCollection


def get_geo_coefs_from_tiff(path_to_geo_file: str):
    """Get coefs from worldfile

        Args:
            path_to_geo_file (str): Path to worldfile

        Returns:
            Coefs from worldfile
        """
    coef_names = ["A", "D", "B", "E", "C", "F"]
    with open(path_to_geo_file, "r") as world_file:
        coefs = [float(line) for line in world_file]
    return dict(zip(coef_names, coefs))


def convert_pixel_to_geo_coords(x: float, y: float, geo_coefs: dict):
    """Convert point coordinates to geo coordinates

        Args:
            x (float): Point X-axis coordinate
            y (float): Point Y-axis coordinate
            geo_coeffs (dict): Coefficients for convert pixel coords to geo coords

        Returns:
            Return geo point
        """

    geo_x = geo_coefs["A"] * x + geo_coefs["B"] * y + geo_coefs["C"]
    geo_y = geo_coefs["D"] * x + geo_coefs["E"] * y + geo_coefs["F"]
    return geo_x, geo_y


def convert_to_geo_poly(poly, geo_coeffs):
    """Convert polygon to polygon with geo coords

        Args:
            poly (shapely.Polygon): Polygon for check
            geo_coeffs (dict): Coefficients for convert pixel coords to geo coords

        Returns:
            Return converted polygon
        """

    exterior_coords = get_coordinates(poly.exterior)
    holes_coords = [get_coordinates(geom) for geom in list(poly.interiors)]

    geo_exterior = [convert_pixel_to_geo_coords(*point, geo_coeffs) for point in exterior_coords]
    geo_holes = []
    for hole in holes_coords:
        geo_hole = [convert_pixel_to_geo_coords(*point, geo_coeffs) for point in hole]
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
        next_tile_left_corner = np.array([tile_left_corner[0] - tile_size[0], tile_left_corner[1]])
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


def get_valid_poly(invalid_geom):
    """Get valid polygon from invalid"""
    if is_valid(invalid_geom):
        return invalid_geom

    else:
        valid_geom = make_valid(invalid_geom)
        polygons = []
        if type(valid_geom) == GeometryCollection:
            for geom in list(valid_geom.geoms):
                if type(geom) == Polygon:
                    polygons.append(geom)
                if type(geom) == MultiPolygon:
                    for geom1 in list(geom.geoms):
                        if type(geom1) == Polygon:
                            polygons.append(geom1)
        if type(valid_geom) == Polygon:
            polygons.append(valid_geom)
        if type(valid_geom) == MultiPolygon:
            polygons.extend(list(valid_geom.geoms))

        if len(polygons) == 0:
            return Polygon()

        polygons_areas = np.array([area(poly) for poly in polygons])
        max_area_idx = np.argmax(polygons_areas)
        return polygons[max_area_idx]


def get_joining_poly(tile_1, tile_2, edge_vicinity, vicinity, edge, tile_1_left_corner, tile_size=(1000, 1000)):
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
    tile_1 = [get_valid_poly(poly) for poly in tile_1]
    tile_2 = [get_valid_poly(poly) for poly in tile_2]

    find_pair = []
    for poly in tile_1:
        if not is_empty(poly):
            if on_edge(poly, tile_1_left_corner, tile_size, edge, edge_vicinity):
                find_pair.append(poly)

    join_pairs = []
    for poly1 in find_pair:
        for poly2 in tile_2:
            if not is_empty(poly2):
                if is_poly_joining(poly1, poly2, edge_vicinity):
                    join_pairs.append([poly1, poly2])

    joining_polys = []
    for pair in join_pairs:
        close_points_poly = []
        for i in range(len(pair)):
            coords = get_coordinates(pair[0 + i])
            for point in coords:
                point = Point(point)
                nearest_pair = nearest_points(point, pair[1 - i])
                if distance(*nearest_pair) < vicinity:
                    close_points_poly.append(nearest_pair[0])
                    close_points_poly.append(nearest_pair[1])

        # TODO: fix troubles leading to this error
        if len(close_points_poly) < 4:
            continue

        connection_poly = Polygon(close_points_poly)
        if not is_valid(connection_poly):
            connection_poly = make_valid(connection_poly)
        connection_poly = convex_hull(connection_poly)
        joining_polys.append(connection_poly)
    return joining_polys


def segment_to_poly(segment, class_id, buffer_val, tile_size=1000, x_offset=0, y_offset=0, ):
    """Collects all polygons from yolofile with label = class_id

        Args:
            segment (dict): Dict with yolofile data
            class_id (int): Index of class in ['roads', 'Lights pole', 'palm_tree', 'singboard', 'building',
            'farms', 'garbage', 'tracks', 'trees_field', 'trees_group', 'trees_solo', 'traffic_sign']
            buffer_val (int): Buffering value
            tile_size (int): Side length of a square tile
            x_offset (int): X-axis offset of tile's left-upper corner relatively field left-upper corner
            y_offset (int): Y-axis offset of tile's left-upper corner relatively field left-upper corner

        Returns:
            List of polygons with labels=class_id
        """

    polys = []

    for found_object in segment:
        obj_class = int(found_object['class'])
        obj_poly = found_object['segment']

        if obj_class == class_id:
            polys.append(obj_poly)

    res_polys = []
    for poly in polys:
        # poly = np.array(poly) * tile_size
        poly = np.array(poly)
        # poly = poly.reshape((len(poly) // 2, 2)) + np.array([x_offset, y_offset])
        poly = poly + np.array([x_offset, y_offset])
        poly = Polygon(poly)
        if class_id == 0:
            poly = poly.buffer(-buffer_val)
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
    poly1 = poly1.buffer(vicinity)
    poly2 = poly2.buffer(0)
    if poly1.intersects(poly2):
        return True
    return False


def sort_files(file_name):
    """Custom function for yolofiles sorting"""

    file_name = file_name.split('_')[-1]
    file_name = file_name.split('.')[0]
    return int(file_name)


def join_tiles(tiles_info, class_id, tiles_in_col, tiles_in_row, tile_width=1000, tile_height=1000,
               edge_vicinity=20, vicinity=50, show_poly=True):
    """Connects a rectangular field of tiles.
    For example: field = 10_000x10_000 pixels image with 1000x1000 pixels tiles

        Args:
            tiles_info (list): List of dicts with yolofile data
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
    # tiles_list = sorted(os.listdir(dir_with_tiles), key=sort_files)
    tiles_count = tiles_in_col * tiles_in_row
    joining_polys = []
    all_poly = []
    buffer_val = 8

    for i in range(len(tiles_info)):
        # print(tiles_list[i])
        # path_to_tile = os.path.join(dir_with_tiles, tiles_list[i])
        segment = tiles_info[i]
        main_tile = segment_to_poly(segment,
                                    class_id=class_id,
                                    buffer_val=buffer_val,
                                    x_offset=tile_width * (i % tiles_in_row),
                                    y_offset=tile_height * (i // tiles_in_row))
        if len(main_tile) == 0:
            continue
        all_poly.extend(main_tile)

        if (i % tiles_in_row) < tiles_in_row - 1:
            segment = tiles_info[i + 1]
            # path_to_right_tile = os.path.join(dir_with_tiles, tiles_list[i + 1])
            right_tile = segment_to_poly(segment,
                                         class_id=class_id,
                                         buffer_val=buffer_val,
                                         x_offset=tile_width * (i % tiles_in_row + 1),
                                         y_offset=tile_height * (i // tiles_in_row))
            if len(right_tile) != 0:
                joining_polys.extend(get_joining_poly(main_tile, right_tile, edge_vicinity, vicinity, 'right',
                                                      (tile_width * (i % tiles_in_row),
                                                       tile_height * (i // tiles_in_row)),
                                                      tile_size=(tile_width, tile_height)))

        if (i // tiles_in_row) < (tiles_in_col - 1):
            segment = tiles_info[i + tiles_in_row]
            # path_to_lower_tile = os.path.join(dir_with_tiles, tiles_list[i + tiles_in_row])
            lower_tile = segment_to_poly(segment,
                                         class_id=class_id,
                                         buffer_val=buffer_val,
                                         x_offset=tile_width * (i % tiles_in_row),
                                         y_offset=tile_height * (i // tiles_in_row + 1))

            if len(lower_tile) != 0:
                joining_polys.extend(get_joining_poly(main_tile, lower_tile, edge_vicinity, vicinity, 'lower',
                                                      (tile_width * (i % tiles_in_row),
                                                       tile_height * (i // tiles_in_row)),
                                                      tile_size=(tile_width, tile_height)))

    all_poly = [i.buffer(0) for i in all_poly]
    joining_polys = [i.buffer(0) for i in joining_polys]
    res = unary_union([*all_poly, *joining_polys])
    if type(res) == MultiPolygon:
        res = list(res.geoms)
    if type(res) == Polygon:
        res = [res]
    if type(res) == GeometryCollection:
        res = [geom for geom in list(res.geoms) if type(geom) == Polygon]

    if class_id == 0:
        if type(res) == GeometryCollection and res.is_empty:
            return []

        for i in range(len(res)):
            res[i] = res[i].buffer(buffer_val)
        res = [poly for poly in res if not poly.is_empty]

    return res


def save_polys_to_shp(polys, geo_data, save_to, class_name):
    """Save list of polygons to .shp file
        Args:
            polys (list): List of polygons
            geo_coeffs (dict): Dict with geo coefficients for converting to geo coordinates
            save_to (str): Path to save folder

        Returns:
            .zip with .shp file
        """

    geo_polys = []
    schema = {
        'geometry': 'Polygon',
        'properties': {'name': 'str:100',
                       'type': 'str:100'}
    }

    geo_coeffs = geo_data['geo_coeffs']
    crs = geo_data['crs']

    # if type(polys) == MultiPolygon:
    #     polys = list(polys.geoms)
    # if type(polys) == Polygon:
    #     polys = [polys]
    # if type(polys) == GeometryCollection:
    #     polys = [geom for geom in list(polys.geoms) if type(geom) == Polygon]

    for poly in polys:
        if not is_empty(poly):
            # TODO: It is quick fix, maybe wrond
            if poly.geom_type == 'MultiPolygon':
                poly = poly.convex_hull

            geo_poly = convert_to_geo_poly(poly, geo_coeffs=geo_coeffs)
            geo_polys.append(geo_poly)

    with fiona.open(save_to, 'w', 'ESRI Shapefile', schema, crs=crs) as shape_file:
        for i in range(len(geo_polys)):
            shp_el = {'geometry': mapping(geo_polys[i]), 'properties': {'name': str(i), 'type': class_name}}
            shape_file.write(shp_el)

