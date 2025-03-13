import numpy as np
from shapely.geometry import Polygon, Point
from shapely import distance, get_coordinates, convex_hull
from shapely.ops import nearest_points


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
    if poly1.intersects(poly2):
        return True
    return False


def on_edge(poly, pos_poly, edge, vicinity):
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
    elif edge == 'top':
        coords += np.array([0, vicinity])
    elif edge == 'right':
        coords += np.array([vicinity, 0])
    else:
        coords += np.array([0, -vicinity])

    poly = Polygon(coords)
    next_tile_poly = pos_poly

    return poly.intersects(next_tile_poly)


def get_joining_poly(tile_1, tile_2, edge_vicinity, vicinity, edge, pos_poly):
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
    for i in range(len(tile_1)):
        if on_edge(tile_1.iloc[i]['geometry'], pos_poly, edge, edge_vicinity):
            find_pair.append(tile_1.iloc[i]['geometry'])

    join_pairs = []
    for poly1 in find_pair:
        for i in range(len(tile_2)):
            if is_poly_joining(poly1, tile_2.iloc[i]['geometry'], edge_vicinity):
                join_pairs.append([poly1, tile_2.iloc[i]['geometry']])

    joining_polys = []
    for pair in join_pairs:
        poly1, poly2 = pair[0], pair[1]
        coords1 = get_coordinates(poly1.exterior)
        close_points_poly = []

        for point in coords1:
            point = Point(point)
            nearest_pair = nearest_points(point, poly2)
            if distance(*nearest_pair) < vicinity:
                close_points_poly.append(nearest_pair[0])
                close_points_poly.append(nearest_pair[1])

        try:
            connection_poly = convex_hull(Polygon(close_points_poly))
        except ValueError:
            continue
        joining_polys.append(connection_poly)
    return joining_polys


def join_tiles(main_polys, around_polys, pos_polys, edge_vicinity=3, vicinity=5):
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

        Returns:
            List of joined polygons
        """
    joining_polys = []

    main_tile = main_polys
    sides = ['right', 'bottom']

    for i in range(len(around_polys)):
        if len(around_polys[i]) > 0:
            joining_polys.extend(get_joining_poly(main_tile, around_polys[i], edge_vicinity, vicinity,
                                                  sides[i], pos_polys[i]))

    return joining_polys

