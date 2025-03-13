import cv2
import colorsys
# import open3d as o3d
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import pyproj
from typing import Tuple, List, Dict
from geo_ai_backend.ml.ml_models.ocr.geo_ai_ocr.cropinfo import CropInfo
# from sklearn.cluster import DBSCAN
# from sklearn.ensemble import IsolationForest


# def get_target_ids(
#         crops_list,
#         classes,
#         trajectory,
#         points,
#         scene_num,
#         mask_size
# ):
#     all_target_ids = {cls_name: np.zeros((0,), dtype='int32') for cls_name in classes}

#     for crop_obj in crops_list:
#         img_name = crop_obj.img_data['img_name']

#         img_num = crop_obj.img_data['num']
#         proj_num = crop_obj.img_data['proj']

#         pano_name = f'pano_{scene_num:06d}_{img_num:06d}'

#         coord_names = ['projectedX[m]', 'projectedY[m]', 'projectedZ[m]', 'heading[deg]', 'pitch[deg]', 'roll[deg]']
#         x, y, z, h, p, r = trajectory.loc[pano_name][coord_names]

#         point_of_view = np.array([x, y, z])
#         rotations = np.array([h, p, r])

#         extrinsic_cam = get_extrinsic_cam(point_of_view, rotations, proj_num)

#         target_ids = find_image_targets(
#             points,
#             crop_obj,
#             mask_size,
#             img_name,
#             extrinsic_cam,
#             point_of_view
#         )

#         if target_ids is None:
#             continue

#         if len(target_ids) == 0:
#             continue

#         for cls_name in classes:
#             all_target_ids[cls_name] = np.concatenate([all_target_ids[cls_name],
#                                                        target_ids[cls_name]])
#             all_target_ids[cls_name] = np.unique(all_target_ids[cls_name])

#     return all_target_ids


def calculate_signboards_iou(crops_list: List[CropInfo], clusters: dict, points: np.ndarray, mask_size):
    intrinsic = np.array(
        [
            [1280 / 2, 0, 1280 / 2],
            [0, 1280 / 2, 1280 / 2],
            [0, 0, 1],
        ],
        dtype='float32'
    )

    for img_info in crops_list:
        if img_info.cluster_id is None:
            continue

        cluster_id = img_info.cluster_id
        extrinsic = img_info.extrinsic
        polygons = img_info.polygons

        cluster_pt_ids = clusters['signboard'][cluster_id]
        cluster_pts = points[cluster_pt_ids]

        augmented_cluster_pts = []
        cube_shift = 0.125
        for pt in cluster_pts:
            for i in range(7):
                x = (-1 + 2 * (i & 1)) * cube_shift
                y = (-1 + 2 * (i & 2)) * cube_shift
                z = (-1 + 2 * (i & 4)) * cube_shift
                augmented_cluster_pts.append(pt + np.array([x, y, z]))
        augmented_cluster_pts = np.array(augmented_cluster_pts)

        pred_mask = np.zeros((mask_size, mask_size), dtype='uint8')
        polygons = polygons.reshape((-1, 1, 2)) * mask_size
        polygons = polygons.astype('int32')
        cv2.fillPoly(pred_mask, [polygons], 1)

        hull = get_projected_cluster_hull(augmented_cluster_pts, extrinsic, intrinsic)
        gt_mask = np.zeros(pred_mask.shape, dtype=pred_mask.dtype)
        if len(hull) > 0:
            cv2.fillPoly(gt_mask, [hull], 1)

        vis_img = gt_mask.copy() * 128
        vis_img += pred_mask * 64
        cv2.imwrite("iou_vis_img.jpg", vis_img)

        visible_gt_mask_square = gt_mask.sum()
        whole_gt_mask_square = 0 if len(hull) == 0 else cv2.contourArea(hull)
        nonvisible_gt_mask_square = whole_gt_mask_square - visible_gt_mask_square

        visible_intersection = cv2.bitwise_and(pred_mask, gt_mask).sum()
        visible_union = cv2.bitwise_or(pred_mask, gt_mask).sum()

        whole_union = visible_union + nonvisible_gt_mask_square
        iou = visible_intersection / whole_union if whole_union > 0 else 0

        img_info.iou = iou


def project_point(object_points: np.ndarray,
                  extrinsic: np.ndarray[np.float32],
                  intrinsic: np.ndarray[np.float32]) -> np.ndarray[np.int32]:
    object_points = object_points.reshape(-1, 1, 3)
    object_points_cam = cv2.perspectiveTransform(object_points, extrinsic)

    # Create mask to hide point, that places in non-visible half of space
    # If it is not done, then points from non-visible half will be projected on result image
    visibility_mask = object_points_cam[:, 0, 2] > 0

    if visibility_mask.max() == False:
        return np.zeros((0, 2), dtype='int32')

    visible_points_cam = object_points_cam[visibility_mask]

    # Project 3d point in camera coord system onto image surface
    image_points, jacobian = cv2.projectPoints(
        visible_points_cam,
        np.zeros((1, 3)),
        np.zeros((1, 3)),
        intrinsic,
        None,
    )

    image_points = image_points.reshape(-1, 2)
    image_points = image_points.astype('int32')


def get_projected_cluster_hull(cluster_points,
                               extrinsic,
                               intrinsic):
    image_points = project_point(cluster_points, extrinsic, intrinsic)

    if len(image_points) == 0:
        return np.zeros((0, 1, 2), dtype='int32')

    image_points = image_points.astype('float32')

    hull = cv2.convexHull(image_points)
    hull = hull.astype('int32')

    return hull


def project_point(object_points: np.ndarray,
                  extrinsic: np.ndarray[np.float32],
                  intrinsic: np.ndarray[np.float32]) -> np.ndarray[np.int32]:
    object_points = object_points.reshape(-1, 1, 3)
    object_points_cam = cv2.perspectiveTransform(object_points, extrinsic)

    # Create mask to hide point, that places in non-visible half of space
    # If it is not done, then points from non-visible half will be projected on result image
    visibility_mask = object_points_cam[:, 0, 2] > 0

    if visibility_mask.max() == False:
        return np.zeros((0, 2), dtype='int32')

    visible_points_cam = object_points_cam[visibility_mask]

    # Project 3d point in camera coord system onto image surface
    image_points, jacobian = cv2.projectPoints(
        visible_points_cam,
        np.zeros((1, 3)),
        np.zeros((1, 3)),
        intrinsic,
        None,
    )

    image_points = image_points.reshape(-1, 2)
    image_points = image_points.astype('int32')

    return image_points


# def filter_clusters(points, clusters):
#     # clusters['palm_tree'] = remove_small_clusters(clusters['palm_tree'], 25)
#     # clusters['trees_solo'] = remove_small_clusters(clusters['trees_solo'], 25)
#     # clusters['Lights pole'] = remove_small_clusters(clusters['Lights pole'], 5)
#     clusters['signboard'] = remove_small_clusters(clusters['signboard'], 5)

#     # clusters['palm_tree'], clusters['trees_solo'] = delete_intersections(points,
#     #                                                                      clusters['palm_tree'],
#     #                                                                      clusters['trees_solo'])

#     return clusters


def delete_intersections(points: np.ndarray, clusters1: dict, clusters2: dict) -> tuple:
    centers1 = {}
    for i in clusters1:
        cluster_points = points[clusters1[i]]
        center = np.array([cluster_points[:, 0].mean(), cluster_points[:, 1].mean(), cluster_points[:, 2].mean()])
        centers1[i] = center

    centers2 = {}
    for i in clusters2:
        cluster_points = points[clusters2[i]]
        center = np.array([cluster_points[:, 0].mean(), cluster_points[:, 1].mean(), cluster_points[:, 2].mean()])
        centers2[i] = center

    for i in centers1:
        for j in centers2:
            center1 = centers1[i]
            center2 = centers2[j]
            dist = np.linalg.norm(center2 - center1)
            if dist > 2:
                continue

            if len(clusters1[i]) > len(clusters2[j]):
                clusters2.pop(j)
            else:
                clusters1.pop(i)

    return clusters1, clusters2


# def show_object_points(points: np.ndarray, obj_ids: np.ndarray):
#     pcd = o3d.geometry.PointCloud()
#     cls_pallete = get_palette(len(obj_ids))

#     pcd.points = o3d.utility.Vector3dVector(points)

#     colors = np.zeros(points.shape, dtype='float32')
#     scale = points[:, 2].max() - points[:, 2].min()
#     colors[:, 0] = (points[:, 2] - points[:, 2].min()) / scale
#     colors[:, 2] = colors[:, 1] = colors[:, 0]

#     for i, cls_name in enumerate(obj_ids):
#         ids = obj_ids[cls_name]
#         color = cls_pallete[i]
#         colors[ids, 2], colors[ids, 1], colors[ids, 0] = color

#     pcd.colors = o3d.utility.Vector3dVector(colors)
#     o3d.visualization.draw_geometries([pcd])


# def show_clusters(points: np.ndarray, clusters: Dict[str, Dict[str, np.ndarray]]):
#     pcd = o3d.geometry.PointCloud()
#     cls_pallete = get_palette(len(clusters))

#     pcd.points = o3d.utility.Vector3dVector(points)

#     colors = np.zeros(points.shape, dtype='float32')
#     scale = points[:, 2].max() - points[:, 2].min()
#     colors[:, 0] = (points[:, 2] - points[:, 2].min()) / scale
#     colors[:, 2] = colors[:, 1] = colors[:, 0]

#     for i, cls_name in enumerate(clusters):
#         hue, _, _ = colorsys.rgb_to_hsv(*cls_pallete[i])
#         cltr_palette = get_fixed_hue_palette(hue, len(clusters[cls_name]))

#         for color_num, j in enumerate(clusters[cls_name]):
#             cluster_ids = clusters[cls_name][j]
#             color = cltr_palette[color_num]
#             colors[cluster_ids, 2], colors[cluster_ids, 1], colors[cluster_ids, 0] = color

#     pcd.colors = o3d.utility.Vector3dVector(colors)
#     o3d.visualization.draw_geometries([pcd])


def get_cluster_positions(points: np.ndarray, clusters: Dict[str, np.ndarray]) -> np.ndarray:
    centers = []
    num_of_clusters = len(clusters) - 1
    for i in range(num_of_clusters):
        cluster_points = points[clusters[str(i)]]
        center = [cluster_points[:, 0].mean(), cluster_points[:, 1].mean(), cluster_points[:, 2].min()]
        centers.append(center)

    centers = np.array(centers)
    return centers


def get_gis_positions(points: np.ndarray, centers: np.ndarray) -> List[List[float]]:
    centers_xy = centers[:, 0:2]
    centers_xy_pt = [Point(xy) for xy in centers_xy]

    wkt = 'PROJCS["40 North",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["World Geodetic System 1984",6378137,298.257223563],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["Degree",0.01745329251994,AUTHORITY["EPSG","9102"]],AXIS["Long",EAST],AXIS["Lat",NORTH],AUTHORITY["EPSG","4326"]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000],PARAMETER["False_Northing",0],PARAMETER["Latitude_Of_Origin",0],PARAMETER["Central_Meridian",57],PARAMETER["Scale_Factor",0.9996],UNIT["Meter",1,AUTHORITY["EPSG","9001"]],AXIS["East",EAST],AXIS["North",NORTH]]'
    centers_loc = gpd.GeoDataFrame(centers_xy_pt,
                                   columns=['geometry'],
                                   crs=pyproj.CRS.from_wkt(wkt))

    centers_loc = centers_loc.to_crs(crs=pyproj.CRS.from_epsg(4326))
    centers_gis = [[pt.y, pt.x] for pt in centers_loc['geometry']]

    return centers_gis


# def show_positions(points, clusters, centers):
#     background_pcd = o3d.geometry.PointCloud()
#     background_points = points[clusters['-1']]
#     background_pcd.points = o3d.utility.Vector3dVector(background_points)
#     colors = np.zeros(background_points.shape, dtype='float32')
#     colors[:, 0] = (background_points[:, 2] - background_points[:, 2].min()) / (
#             background_points[:, 2].max() - background_points[:, 2].min())
#     colors[:, 1] = colors[:, 0]
#     colors[:, 2] = colors[:, 1]
#     background_pcd.colors = o3d.utility.Vector3dVector(colors)

#     centers_pcd = o3d.geometry.PointCloud()
#     centers_pcd.points = o3d.utility.Vector3dVector(centers)
#     colors = np.ones(centers.shape, dtype='float32')
#     colors[:, 0], colors[:, 1], colors[:, 2] = 0, 0, 1
#     centers_pcd.colors = o3d.utility.Vector3dVector(colors)

#     o3d.visualization.draw_geometries([background_pcd, centers_pcd])


# def show_point_clouds(points: List[np.ndarray], colors: List[np.ndarray]):
#     assert len(points) == len(colors)
#     pcds = []
#     for i in range(len(points)):
#         pcd = o3d.geometry.PointCloud()
#         pcd.points = o3d.utility.Vector3dVector(points)
#         pcd.colors = o3d.utility.Vector3dVector(colors)
#         pcds.append(pcd)
#     o3d.visualization.draw_geometries(pcds)


# def get_clusters(points: np.ndarray, target_ids: List[np.ndarray]) -> Dict[str, np.ndarray]:
#     """Apply clusterization to found object ids

#     :param points: array of shape (N, 3) that contains a point cloud
#     :param target_ids: list of array with ids that points to value in `points` param
#     :return: dict, key '-1' - background points ids, keys '0', '1',..., 'n' - clusters points ids
#     """

#     all_clusters = {}
#     for cls_name in target_ids:
#         target_points = points[target_ids[cls_name]]
#         if len(target_points) == 0:
#             all_clusters[cls_name] = {}
#             continue

#         clustering = DBSCAN(eps=1.2, min_samples=2).fit(target_points)
#         num_of_obj_clusters = clustering.labels_.max() + 1

#         clusters = {}
#         for i in range(num_of_obj_clusters):
#             clusters[str(i)] = target_ids[cls_name][clustering.labels_ == i]
#             # clusters[str(i)] = np.unique(clusters[str(i)])
#         all_clusters[cls_name] = clusters

#     return all_clusters


# def remove_small_clusters(clusters: Dict[str, np.ndarray], min_len: int) -> Dict[str, np.ndarray]:
#     res = {}
#     cnt = 0
#     for i in clusters:
#         if len(clusters[i]) >= min_len:
#             res[str(cnt)] = clusters[i]
#             cnt += 1
#     return res


# def find_image_targets(
#         points: np.ndarray,
#         crop_obj,
#         mask_size: int,
#         img_name: str,
#         extrinsic: np.ndarray,
#         point_of_view: np.ndarray,
# ):
#     """ Find target ids (ids of corresponding points in point cloud)
#     for all images from crop_obj.
#     """

#     res = {}
#     classes = ['signboard']

#     segment = crop_obj.polygons

#     for class_num, cls_name in enumerate(classes):
#         cls_target_ids = np.zeros((0,), dtype='int32')

#         mask = np.zeros((mask_size, mask_size), dtype='uint8')
#         segment = segment.reshape((-1, 1, 2)) * mask_size
#         segment = segment.astype('int32')
#         # hull = cv2.convexHull(segment, returnPoints=True)
#         if len(segment) > 0:
#             cv2.fillPoly(mask, [segment], 1)

#         target_mask = find_target_mask(points, mask, extrinsic)
#         target_ids = np.nonzero(target_mask)[0]
#         target_points = points[target_ids]

#         if len(target_ids) == 0:
#             res[cls_name] = np.zeros((0,), dtype='int32')
#             continue

#         target_points_clusters = DBSCAN(eps=1.2, min_samples=1).fit(target_points)
#         cluster_ids, cluster_counts = np.unique(target_points_clusters.labels_, return_counts=True)
#         max_cluster_id = cluster_ids[np.argmax(cluster_counts)]

#         # remove points from other clusters
#         target_ids = target_ids[target_points_clusters.labels_ == max_cluster_id]
#         target_points = points[target_ids]

#         if len(target_ids) > 4:
#             crop_obj.extrinsic = extrinsic
#             crop_obj.target_ids = target_ids
#             crop_obj.targets_points = target_points

#             crop_obj.set_bbox_area()
#             crop_obj.set_center()
#             crop_obj.set_distance(point_of_view)
#             crop_obj.set_angle(point_of_view)

#         pos = np.linalg.inv(extrinsic)[:3, 3:4].T
#         nearest_target_ids = find_nearest_pts(points, target_ids, pos)
#         inlier_target_ids = find_inlier_ids(points, nearest_target_ids, 0.2)

#         cls_target_ids = np.concatenate([cls_target_ids, inlier_target_ids])  # inlier_target_ids

#         res[cls_name] = cls_target_ids

#     return res


# def find_target_mask(
#         points: np.ndarray,
#         image_mask: np.ndarray,
#         extrinsic: np.ndarray) -> np.ndarray:
#     """Find target mask for point cloud array for specific object
#     """

#     cube_length = image_mask.shape[0]
#     intrinsic = np.array(
#         [
#             [cube_length / 2, 0, cube_length / 2],
#             [0, cube_length / 2, cube_length / 2],
#             [0, 0, 1],
#         ],
#         dtype='float32'
#     )

#     # Remove hidden points, that is leave only visible points from camera position
#     camera_position = np.linalg.inv(extrinsic)[:3, 3]
#     pcd = o3d.geometry.PointCloud()
#     pcd.points = o3d.utility.Vector3dVector(points)
#     _, pt_map = pcd.hidden_point_removal(camera_position, radius=1000)
#     pcd_sel = pcd.select_by_index(pt_map)
#     hpr_points = np.asarray(pcd_sel.points)

#     # o3d.visualization.draw_geometries([pcd_sel])

#     # Turn world coordinates into camera coordinates.
#     points_cam = cv2.perspectiveTransform(hpr_points.reshape(-1, 1, 3), extrinsic).reshape(-1, 3)

#     # Create mask to hide point, that places in non-visible half of space
#     # If it is not done, then points from non-visible half will be projected on result image
#     visibility_mask = points_cam[:, 2] > 0
#     visible_points_cam = points_cam[visibility_mask]

#     # Project 3d point in camera coord system onto image surface
#     image_points, jacobian = cv2.projectPoints(
#         visible_points_cam.reshape(-1, 1, 3),
#         np.zeros((1, 3), dtype='float32'),
#         np.zeros((1, 3), dtype='float32'),
#         intrinsic,
#         None,
#     )
#     image_points = image_points.reshape(-1, 2)
#     image_points = image_points.astype('int32')

#     # Create mask, that hides out of bounds image points
#     bounding_mask = (image_points[:, 0] >= 0) & (image_points[:, 0] < image_mask.shape[1]) & \
#                     (image_points[:, 1] >= 0) & (image_points[:, 1] < image_mask.shape[0])
#     image_points_in_bounds = image_points[bounding_mask]

#     # Create target mask to define points, that correspond to target object from image mask
#     target_mask = image_mask[image_points_in_bounds[:, 1], image_points_in_bounds[:, 0]] != 0
#     image_points_in_bounds = image_points[bounding_mask]

#     # Create common_target_mask for all original points (after hidden points removal),
#     # where True - target, False - background
#     common_target_mask = np.zeros((len(points),), dtype='bool')
#     common_target_mask[pt_map] = True
#     common_target_mask[common_target_mask] = visibility_mask
#     common_target_mask[common_target_mask] = bounding_mask
#     common_target_mask[common_target_mask] = target_mask

#     return common_target_mask


# def find_nearest_pts(points: np.ndarray,
#                      pt_ids: np.ndarray,
#                      pos: np.ndarray):
#     # target_points = points[pt_ids]
#     # tree = KDTree(target_points, leaf_size=max(1, int(0.75 * len(target_points))))
#     # num_nearest = min(num_nearest, len(pt_ids))
#     # nearest_pts_ids = tree.query(pos, num_nearest, sort_results=True)[1][0]
#     # return pt_ids[nearest_pts_ids]

#     target_points = points[pt_ids]
#     clustering = DBSCAN(eps=1, min_samples=2).fit(target_points)
#     num_of_clusters = clustering.labels_.max() + 1
#     if num_of_clusters == 0:
#         return pt_ids

#     clusters_points = [target_points[clustering.labels_ == i] for i in range(num_of_clusters)]
#     clusters_dist = [np.linalg.norm(np.array([[pts[:, 0].mean(), pts[:, 1].mean(), pts[:, 2].mean()]]) - pos) for pts in
#                      clusters_points]
#     clusters_dist = np.array(clusters_dist)
#     nearest_cluster_idx = clusters_dist.argmin()

#     return pt_ids[clustering.labels_ == nearest_cluster_idx]


# def find_inlier_ids(points: np.ndarray, pt_ids: np.ndarray, contamination=0.1):
#     target_points = points[pt_ids]
#     if len(target_points) < 2:
#         return pt_ids
#     clf = IsolationForest(n_estimators=10, warm_start=True, random_state=0)
#     outlier_pred = clf.fit(target_points).predict(target_points)  # fit the added trees
#     # estimator =  EllipticEnvelope(contamination=contamination, random_state=42)
#     # outlier_pred = estimator.fit(target_points).predict(target_points)
#     return pt_ids[outlier_pred == 1]


def get_extrinsic_cam(point_of_view: np.ndarray, rotations: np.ndarray, shot_number: int) -> np.ndarray:
    """Get camera extrinsic using specific parameters.

    :param point_of_view: array with shape (3,) that contains X, Y, Z coords (m) of point of view
    :param rotations: array with shape (3,) that contains heading, pitch, roll coords (deg) of rotation
    :param shot_number: number of chosen cubic projection (0 - back, 1 - left, 2 - front, 3 - right)
    :return: array with shape (4, 4) that is camera extrinsic
    """

    extrinsic_car = get_extrinsic_car(point_of_view, rotations)
    installation_matrix = get_rot_oz(np.pi / 2) @ get_rot_oy(-np.pi / 2)
    chosen_shot_rotation = get_rot_oy((2 - shot_number) * np.pi / 2)  # additional rotation for chosen cubic projection

    extrinsic_cam = chosen_shot_rotation @ installation_matrix @ extrinsic_car
    return extrinsic_cam


def get_extrinsic_car(point_of_view: np.ndarray, rotations: np.ndarray) -> np.ndarray:
    """Get car extrinsic using specific parameters. For car coord system X - axis of car direction,
    Z is directed upward, Y is perependicular to both X and Z

    :param point_of_view: array with shape (3,) that contains X, Y, Z coords (m) of point of view
    :param rotations: array with shape (3,) that contains heading, pitch, roll coords (deg) of rotation
    :return: array with shape (4, 4) that is car extrinsic
    """

    x, y, z = point_of_view
    h, p, r = rotations

    # Turning into radians and add some covertions to match our coordinate system
    h_rad = (h - 90) * np.pi / 180
    p_rad = p * np.pi / 180
    r_rad = -r * np.pi / 180

    roll_rot = get_rot_ox(r_rad)
    pitch_rot = get_rot_oy(p_rad)
    heading_rot = get_rot_oz(h_rad)

    trans = get_translation(-x, -y, -z)

    extrinsic_car = roll_rot @ pitch_rot @ heading_rot @ trans

    return extrinsic_car


def project_visible_point(object_points, intrinsic, extrinsic, img_size) -> Tuple[np.ndarray, np.ndarray]:
    # Get object points in camera coord system
    object_points_cam = hmg2cart((extrinsic @ cart2hmg(object_points).T).T)

    # Mask for visible points (visible means having non-negative Z-coordinate camera coord system)
    visibility_mask = object_points_cam[:, 2] >= 0

    # If there are no visible points, return empty arrays
    if visibility_mask.max() == False:
        return np.zeros((0, 3)), np.zeros((0, 2))

    rvec, tvec = homography2rvec_tvec(extrinsic)

    # Leave only visible object_points
    object_points = object_points[visibility_mask]

    # Do projection
    image_points, _ = cv2.projectPoints(
        object_points,
        rvec,
        tvec,
        intrinsic,
        None,
    )
    image_points = image_points.reshape(-1, 2)

    # Leave only points thats in image bounds
    width, height = img_size
    bounding_mask = (0 <= image_points[:, 0]) & (image_points[:, 0] < height) & \
                    (0 <= image_points[:, 1]) & (image_points[:, 1] < width)
    image_points = image_points[bounding_mask]
    object_points = object_points[bounding_mask]

    return object_points, image_points


def get_palette(num_of_colors: int) -> list:
    hsv_tuples = [((x / num_of_colors) % 1, 1, 1) for x in range(num_of_colors)]
    rgb_tuples = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
    return rgb_tuples


def get_fixed_hue_palette(hue: float, num_of_values: int) -> list:
    hsv_tuples = [(hue, 1, 0.5 + (x / num_of_values) % 1 * 0.5) for x in range(num_of_values)]
    rgb_tuples = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
    return rgb_tuples


def draw_projected_points(
        img: np.ndarray,
        object_points: np.ndarray,
        image_points: np.ndarray,
        point_of_view: np.ndarray,
        radius_of_view: float) -> np.ndarray:
    """Draw projected points with color that depends on distance to the point
    """

    for i, pt in enumerate(image_points):
        x, y = int(pt[0]), int(pt[1])

        dist = np.linalg.norm(point_of_view - object_points[i])
        color = colorsys.hsv_to_rgb(dist / radius_of_view, 1, 1)
        color = (color[0] * 255, color[1] * 255, color[2] * 255)

        cv2.circle(img, (x, y), 6, color, -1)

    return img


def homography2rvec_tvec(h_mat: np.ndarray) -> tuple:
    rvec = cv2.Rodrigues(h_mat[0:3, 0:3])[0]
    tvec = h_mat[0:3, 3:4]
    return rvec, tvec


def cart2hmg(pts: np.ndarray) -> np.ndarray:
    "Convert cartesian to homogenous coordinates"
    res = np.concatenate([pts, np.ones((len(pts), 1))], axis=1)
    return res


def hmg2cart(pts: np.ndarray) -> np.ndarray:
    "Convert homogenous to cartesian coordinates"
    xyz = pts[:, 0:3]
    xyz[:, 0] /= pts[:, 3]
    xyz[:, 1] /= pts[:, 3]
    xyz[:, 2] /= pts[:, 3]
    return xyz


def get_rot_ox(angle: float) -> np.ndarray:
    """Get homography matrix that represents rotation aroung Ox

    :param angle: angle in radians
    :return: homography matrix
    """

    mat = np.array(
        [
            [1, 0, 0, 0],
            [0, np.cos(angle), -np.sin(angle), 0],
            [0, np.sin(angle), np.cos(angle), 0],
            [0, 0, 0, 1],
        ]
    )

    return mat


def get_rot_oy(angle: float) -> np.ndarray:
    """Get homography matrix that represents rotation aroung Oy

    :param angle: angle in radians
    :return: homography matrix
    """

    mat = np.array(
        [
            [np.cos(angle), 0, np.sin(angle), 0],
            [0, 1, 0, 0],
            [-np.sin(angle), 0, np.cos(angle), 0],
            [0, 0, 0, 1],
        ]
    )

    return mat


def get_rot_oz(angle: float) -> np.ndarray:
    """Get homography matrix that represents rotation aroung Oz

    :param angle: angle in radians
    :return: homography matrix
    """

    mat = np.array(
        [
            [np.cos(angle), -np.sin(angle), 0, 0],
            [np.sin(angle), np.cos(angle), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ]
    )

    return mat


def get_translation(x: float, y: float, z: float) -> np.ndarray:
    """Get homography matrix that represents translation

    """

    mat = np.array(
        [
            [1, 0, 0, x],
            [0, 1, 0, y],
            [0, 0, 1, z],
            [0, 0, 0, 1],
        ]
    )

    return mat
