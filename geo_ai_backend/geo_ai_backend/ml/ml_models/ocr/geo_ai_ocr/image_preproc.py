import os
import cv2
import numpy as np
from PIL import ImageFont, ImageDraw, Image, ImageOps
from geo_ai_backend.ml.ml_models.ocr.geo_ai_ocr.utils import add_padding


# import onnx
# import onnxruntime as ort


def binarize_image(image: np.ndarray) -> np.ndarray:
    """
    Binarize image using Otsu's method
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, output = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return output


def enhance_image_clahe(image: np.ndarray) -> np.ndarray:
    """
    Enhance image using CLAHE
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    lab_planes = list(cv2.split(lab))

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    lab_planes[0] = clahe.apply(lab_planes[0])
    lab = cv2.merge(lab_planes)
    output = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    return output


def enhance_image(image: np.ndarray) -> np.ndarray:
    """
    Enhance image using detailEnhance
    """
    output = cv2.detailEnhance(image, sigma_s=10, sigma_r=0.15)

    return output


def median_filter(image: np.ndarray) -> np.ndarray:
    """
    Median filter
    """
    output = cv2.medianBlur(image, 5)

    return output


def superresolution(image: np.ndarray, ort_sess) -> np.ndarray:
    """
    Superresolution
    """
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # add padding
    h, w, _ = image.shape

    # bring sizes to multiple of 16 and increase it
    if h % 16 != 0:
        h = h + (16 - h % 16)

    if w % 16 != 0:
        w = w + (16 - w % 16)

    image = Image.fromarray(image)
    image = add_padding(image, (w, h))
    image = np.array(image)

    image = image.astype(np.float32)
    image = np.transpose(image, (2, 0, 1))
    image = np.expand_dims(image, axis=0)
    image /= 255.0

    in_name = ort_sess.get_inputs()[0].name
    outputs = ort_sess.run(None, {in_name: image})

    img_out = outputs[0]

    img_out = np.squeeze(img_out)
    img_out = np.clip(img_out, 0.0, 1.0)
    img_out = np.transpose(img_out, (1, 2, 0))
    img_out = (img_out * 255.0).round()
    img_out = img_out.astype(np.uint8)
    img_out = cv2.cvtColor(img_out, cv2.COLOR_RGB2BGR)

    return img_out
