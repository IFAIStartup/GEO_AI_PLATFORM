import os
import cv2
import numpy as np
from PIL import ImageOps
from pathlib import Path
from easydict import EasyDict
# from ultralytics import YOLO
import easyocr
import torch
import onnxruntime as ort
from typing import Optional


def load_models(
        models_path: Path,
        detection_model_path: Optional[str] = None,
        classification_quality_model_path: Optional[str] = None,
        classification_language_model_path: Optional[str] = None,
        super_resolution_model_path: Optional[str] = None,
        magface_model_path: Optional[str] = None,
        easy_ocr: bool = True
) -> EasyDict:
    """
    Load models
    """

    # Load detection model
    # detection_model = YOLO(models_path / detection_model_path) if detection_model_path else None
    detection_model = None

    # Load classification quality model
    # classification_quality_model = YOLO(
    #     models_path / classification_quality_model_path) if classification_quality_model_path else None
    classification_quality_model = None
    
    # # Load classification language model
    # classification_language_model = ort.InferenceSession(str(models_path / classification_language_model_path),
    #                                                      providers=['CUDAExecutionProvider']) \
    #     if classification_language_model_path else None

    # Load classification language model
    classification_language_model = ort.InferenceSession(str(models_path / classification_language_model_path)) \
        if classification_language_model_path else None

    # Load super resolution model
    super_resolution_model = torch.load(
        models_path / super_resolution_model_path) if super_resolution_model_path else None

    if magface_model_path:
        import sys
        sys.path.append('./magface/MagFace/')
        from magface.MagFace.inference.network_inf import builder_inf

        params = {'arch': 'iresnet100',
                  'inf_list': '',
                  'feat_list': '',
                  'workers': 4,
                  'batch_size': 256,
                  'embedding_size': 512,
                  'resume': models_path / magface_model_path,
                  'print_freq': 100,
                  'cpu_mode': False,
                  'dist': 1}

        params = EasyDict(params)
        magface_model = builder_inf(params)
        magface_model.eval()
    else:
        magface_model = None

    easyocr_detection_model = easyocr.Reader(['ar', 'en']) if easy_ocr else None
    easyocr_arabic_model = easyocr.Reader(['ar']) if easy_ocr else None
    easyocr_english_model = easyocr.Reader(['en']) if easy_ocr else None

    # create easydict with models
    models = EasyDict()

    models.detection_model = detection_model
    models.classification_quality_model = classification_quality_model
    models.classification_language_model = classification_language_model
    models.super_resolution_model = super_resolution_model
    models.magface_model = magface_model
    models.easyocr_detection_model = easyocr_detection_model
    models.easyocr_arabic_model = easyocr_arabic_model
    models.easyocr_english_model = easyocr_english_model

    return models


def check_save_dir(save_dir: str) -> str:
    """
    Check if save directory exists, if not, create it.
    :param save_dir: path to save directory
    :return: None
    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        return save_dir

    else:
        for i in range(1, 9999):
            if not os.path.exists(save_dir + '_' + str(i)):
                save_dir = save_dir + '_' + str(i)
                os.makedirs(save_dir)
                return save_dir


def masks2segments(masks, strategy='largest', epsilon=5):
    """
    It takes a list of masks(n,h,w) and returns a list of segments(n,xy)

    Args:
      masks (torch.Tensor): the output of the model, which is a tensor of shape (batch_size, 160, 160)
      strategy (str): 'concat' or 'largest'. Defaults to largest
      epsilon (float): Parameter specifying the approximation accuracy for Douglas-Peaker algorithm.
      This is the maximum distance between the original curve and its approximation.

    Returns:
      segments (List): list of segment masks
    """
    segments = []
    for x in masks.int().cpu().numpy().astype('uint8'):
        c = cv2.findContours(x, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        if c:
            if strategy == 'concat':  # concatenate all segments
                c = np.concatenate([x.reshape(-1, 2) for x in c])
            elif strategy == 'largest':  # select largest segment
                c = np.array(c[np.array([len(x) for x in c]).argmax()]).reshape(-1, 2)
        else:
            c = np.zeros((0, 2))  # no segments found

        # if c.shape[0] != 0:
        #     c = cv2.approxPolyDP(c, epsilon, True).reshape(-1, 2)
        segments.append(c.astype('float32'))
    return segments


def create_square_crop(img: np.ndarray, bbox: list) -> np.ndarray:
    """
    Create square crop from bbox by higher side
    :param img: image
    :param bbox: bbox
    :return: square crop
    """
    x1, y1, x2, y2 = bbox

    h = y2 - y1
    w = x2 - x1

    if w > h:
        y1 -= (w - h) // 2
        y2 += (w - h) // 2
        h += (w - h)
    else:
        x1 -= (h - w) // 2
        x2 += (h - w) // 2
        w += (h - w)

    x1 = max(x1, 0)
    y1 = max(y1, 0)
    w = min(w, img.shape[1] - x1)
    h = min(h, img.shape[0] - y1)

    # crop_square = img[y1:y2, x1:x2]
    crop_square = img[y1:y1 + h, x1:x1 + w]
    return crop_square


def add_padding(image, target_size):
    # Открываем изображение

    # Определяем текущий размер изображения
    current_width, current_height = image.size

    # Определяем требуемый размер изображения
    target_width, target_height = target_size

    # Вычисляем размеры паддинга для каждой стороны
    pad_width = max(target_width - current_width, 0)
    pad_height = max(target_height - current_height, 0)

    # Вычисляем размеры верхнего, нижнего, левого и правого паддинга
    left_padding = pad_width // 2
    right_padding = pad_width - left_padding
    top_padding = pad_height // 2
    bottom_padding = pad_height - top_padding

    # Добавляем паддинг с помощью метода `ImageOps.expand`
    padded_image = ImageOps.expand(image, border=(left_padding, top_padding, right_padding, bottom_padding),
                                   fill='black')

    # Возвращаем изображение с добавленным паддингом
    return padded_image
