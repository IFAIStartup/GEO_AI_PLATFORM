import numpy as np
from PIL import Image, ImageOps
import urllib3


def add_padding(image: np.ndarray, target_size: tuple) -> np.ndarray:
    """
    Add padding to image
    :param image: image to add padding
    :param target_size: target size
    :return: padded image
    """
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)

    current_width, current_height = image.size

    target_width, target_height = target_size

    pad_width = max(target_width - current_width, 0)
    pad_height = max(target_height - current_height, 0)

    left_padding = pad_width // 2
    right_padding = pad_width - left_padding
    top_padding = pad_height // 2
    bottom_padding = pad_height - top_padding

    padded_image = ImageOps.expand(image, border=(left_padding, top_padding, right_padding, bottom_padding),
                                   fill='black')

    padded_image = np.array(padded_image)

    return padded_image


def getWKT_PRJ(epsg_code: str):
    # access projection information
    http = urllib3.PoolManager()
    wkt = http.request("GET",
                       f"http://spatialreference.org/ref/epsg/{epsg_code}/prettywkt/")
    output = wkt.data.decode('UTF-8')
    return output
