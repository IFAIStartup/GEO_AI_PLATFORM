import numpy as np
from typing import Dict
# from sklearn.linear_model import LinearRegression


class CropInfo:
    """
    A class to store information about cropped signboard images,
    including their bounding box, polygons, and other properties.
    """

    def __init__(
            self,
            img_name: str,
            bbox: np.ndarray,
            polygons: np.ndarray,
            extrinsic: np.ndarray,
            target_ids: np.ndarray,
            targets_points: np.ndarray,
    ):
        """
        Initializes a new instance of the CropInfo class.
        """
        self.img_name = img_name
        self.bbox = bbox
        self.polygons = polygons

        self.extrinsic = extrinsic
        self.target_ids = target_ids
        self.targets_points = targets_points

        self.point_of_view: np.ndarray = None

        self.center = None  # Center of the signboard
        self.distance = None  # Distance from a point of view (POV) to the signboard
        self.angle = None  # Angle of the signboard relative to a POV

        self.embedding = None  # Embedding vector, not currently used
        self.embedding_square = None  # Embedding vector with context, not currently used
        self.quality = None  # Image quality metric, not currently used
        self.area = None  # Area of the signboard
        self.iou = None  # Intersection over Union metric with the nearest cluster
        self.cluster_dist = None  # Distance to the nearest cluster
        self.cluster_id = None  # Identifier of the nearest cluster

    def set_quality(self):
        """
        Computes the quality of the signboard based on its embedding vector.
        """
        mag = np.linalg.norm(self.embedding)
        self.quality = mag

    def set_bbox_area(self):
        """
        Computes the area of the signboard based on its bounding box.
        """
        self.area = (self.bbox[2] - self.bbox[0]) * (self.bbox[3] - self.bbox[1])

    def set_center(self):
        """
        Computes the center point of the signboard based on its target points.
        """
        self.center = np.mean(self.targets_points[:, :3], axis=0)

    def set_distance(self, pov: np.ndarray):
        """
        Computes the distance from a specified point of view (POV) to the center of the signboard.

        Parameters:
        pov (np.ndarray): The point of view coordinates as a NumPy array.
        """
        self.distance = np.linalg.norm(pov - self.center)

    def set_angle(self, pov: np.ndarray):
        """
        Computes the angle between the signboard and a line from a specified point of view (POV).

        Parameters:
        pov (np.ndarray): The point of view coordinates as a NumPy array.
        """
        line = self.center - pov
        surface = get_surface(self.targets_points)
        angle = get_surface_line_angle(surface, line)
        angle = np.degrees(angle)
        self.angle = angle

    def set_iou(self, clusters):
        pass


def get_surface_line_angle(surface, line):
    a, b, c, d = surface
    m, l, k = line
    sin_phi = (a * m + b * l + c * k) / (np.sqrt(a ** 2 + b ** 2 + c ** 2) * np.sqrt(m ** 2 + l ** 2 + k ** 2))
    phi = abs(np.arcsin(sin_phi))

    return phi


def get_surface(pts: np.ndarray) -> tuple:
    # Surface equation: ax + by + cz + d = 0 ->  a'x + b'y + c'z = 1
    A = pts
    y = np.ones((len(pts), 1), dtype=pts.dtype)
    a, b, c = np.linalg.lstsq(A, y, rcond=-1)[0].reshape(-1)
    d = -1

    # XY = pts[:, :2]
    # Z = pts[:, 2:3]

    # # z = ax + by + d -> ax + by - z + d = 0
    # A = np.concatenate([XY, np.ones((len(XY), 1), dtype=XY.dtype)], axis=1)
    # y = Z[:, 0]
    # a, b, d = np.linalg.lstsq(A, y, rcond=-1)[0]
    # c = -1

    # reg = LinearRegression().fit(XY, Z)

    # # z = ax + by + d -> ax + by - z + d = 0
    # a, b = reg.coef_[0]
    # c = -1
    # d = reg.intercept_[0]

    return a, b, c, d
