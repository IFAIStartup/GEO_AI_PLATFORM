import numpy as np
import cv2


def preprocess_deeplabv3(img: np.ndarray) -> np.ndarray:
    img_seg = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_seg = img_seg.astype(np.float32)

    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])
    img_seg = (img_seg / 255.0 - mean) / std

    img_seg = cv2.resize(img_seg, (640, 640))
    img_seg = img_seg.astype(np.float32)
    img_seg = img_seg.transpose(2, 0, 1)
    img_seg = np.expand_dims(img_seg, axis=0)

    return img_seg


