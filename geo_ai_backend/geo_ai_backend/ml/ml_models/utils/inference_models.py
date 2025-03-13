import cv2
import torch
from abc import ABC
import numpy as np
from typing import List, Tuple
import tritonclient.http as httpclient
import warnings

from geo_ai_backend.ml.ml_models.utils.yolo import (
    preprocess_yolo, 
    postprocess_yolo, 
    masks2segments,
)
from geo_ai_backend.ml.ml_models.utils.deeplab import (
    preprocess_deeplabv3
)


class InferenceModel(ABC):
    def __call__(
            self, 
            img: np.ndarray, 
            client: httpclient.InferenceServerClient,
            *args,
            **kwargs) -> List[dict]:
        pass


class YOLOv8segModel(InferenceModel):
    def __init__(self,  
                 model_name: str,
                 class_names: List[str],
                 imgsz: Tuple[int]):
        
        self.model_name = model_name
        self.class_names = class_names
        self.imgsz = imgsz
    
    def __call__(self, img, client: httpclient.InferenceServerClient, overlap=0):
        orig_imgsz = img.shape[:2]
        img_yolo = img.copy()
        class_names_dict = {i: c for i, c in enumerate(self.class_names)}
    
        img_yolo = preprocess_yolo(img_yolo, self.imgsz)
        preds_yolo = self.inference_triton_yolo(img_yolo, self.model_name, client)
        preds_yolo = postprocess_yolo(preds_yolo, class_names_dict, orig_imgsz, self.imgsz, conf=0.15)

        segments_with_classes = []

        for pred in preds_yolo:
            bboxes, masks = pred
            masks = truncate_masks(masks, overlap)
            segments = masks2segments(masks, epsilon=0.3)

            for i in range(len(segments)):
                segment = segments[i]
                segment_area = cv2.contourArea(segment)
                class_name = self.class_names[bboxes[i][5]]
                confidence = bboxes[i][4]
                
                if class_name is None:
                    continue

                if len(segment) < 4:
                    continue
                
                segment = {
                    'class': class_name, 
                    'confidence': confidence,
                    'segment': segments[i],
                }
                segments_with_classes.append(segment)

        return segments_with_classes

    def inference_triton_yolo(
            self, 
            img_in: np.ndarray, 
            model_name: str, 
            client: httpclient.InferenceServerClient) -> List[np.ndarray]:
        
        """Do inference directly using triton inference server 

        :param img_in: preprocessed ndarray (3, H, W)
        :param model_name: specific name of the model in model repository
        :param client: inference server client instance
        :return: List of 2 arrays: (B, N, CLS + 4 + M) and (B, M, H, W)
                B = 1 - batch size
                N - number of found objects
                CLS - number of classes
                M = 32 - mask dim
                H - inference height
                W - inference height
        """
        img_in = fix_input_dims(client, model_name, img_in)
        
        input0 = httpclient.InferInput("images", img_in.shape, datatype="FP32")
        input0.set_data_from_numpy(img_in, binary_data=True)
        
        input0 = httpclient.InferInput("images", img_in.shape, datatype="FP32")
        input0.set_data_from_numpy(img_in, binary_data=True)
        
        # Setting up output
        output0 = httpclient.InferRequestedOutput("output0", binary_data=True)
        output1 = httpclient.InferRequestedOutput("output1", binary_data=True)
        
        # Querying the server
        results = client.infer(model_name=model_name, inputs=[input0], outputs=[output0, output1])

        inference_output0 = results.as_numpy('output0')
        inference_output1 = results.as_numpy('output1')

        return [inference_output0, inference_output1]


class YOLOv8detModel(InferenceModel):
    def __init__(self,  
                 model_name: str,
                 class_names: List[str],
                 imgsz: Tuple[int]):
        
        self.model_name = model_name
        self.class_names = class_names
        self.imgsz = imgsz
    
    def __call__(self, img, client: httpclient.InferenceServerClient, overlap=0):
        orig_imgsz = img.shape[:2]
        img_yolo = img.copy()
        class_names_dict = {i: c for i, c in enumerate(self.class_names)}
    
        img_yolo = preprocess_yolo(img_yolo, self.imgsz)
        preds_yolo = self.inference_triton_yolo(img_yolo, self.model_name, client)
        preds_yolo = postprocess_yolo(preds_yolo, class_names_dict, orig_imgsz, self.imgsz, conf=0.5)

        segments_with_classes = []

        # TODO: check
        for pred in preds_yolo:
            bboxes = pred[0]
            
            for i in range(len(bboxes)):
                class_name = self.class_names[bboxes[i][5]]
                confidence = bboxes[i][4]
                
                if class_name is None:
                    continue
                
                x1, y1, x2, y2 = bboxes[i, :4]
                segment = np.array(
                    [
                        [[x1, y1]],
                        [[x1, y2]],
                        [[x2, y2]],
                        [[x2, y1]],
                    ],
                )

                segment = {
                    'class': class_name, 
                    'confidence': confidence,
                    'segment': segment,
                }
                segments_with_classes.append(segment)

        return segments_with_classes

    def inference_triton_yolo(
            self, 
            img_in: np.ndarray, 
            model_name: str, 
            client: httpclient.InferenceServerClient) -> List[np.ndarray]:
        
        """Do inference directly using triton inference server 

        :param img_in: preprocessed ndarray (3, H, W)
        :param model_name: specific name of the model in model repository
        :param client: inference server client instance
        :return: List of 2 arrays: (B, N, CLS + 4 + M) and (B, M, H, W)
                B = 1 - batch size
                N - number of found objects
                CLS - number of classes
                M = 32 - mask dim
                H - inference height
                W - inference height
        """
        img_in = fix_input_dims(client, model_name, img_in)

        # Setting up input and output
        input0 = httpclient.InferInput("images", img_in.shape, datatype="FP32")
        input0.set_data_from_numpy(img_in, binary_data=True)

        # input0 = httpclient.InferInput("images", img_in[np.newaxis, ...].shape, datatype="FP32")
        # input0.set_data_from_numpy(img_in[np.newaxis, ...], binary_data=True)

        output0 = httpclient.InferRequestedOutput("output0", binary_data=True)

        # Querying the server
        results = client.infer(model_name=model_name, inputs=[input0], outputs=[output0])
        inference_output0 = results.as_numpy('output0')

        return [inference_output0]



class DeepLabv3Model(InferenceModel):
    def __init__(self,  
                model_name: str,
                class_names: List[str],
                imgsz: Tuple[int]):
        
        self.model_name = model_name
        self.class_names = class_names
        self.imgsz = imgsz

    def __call__(self, img, client: httpclient.InferenceServerClient, overlap=0):
        img_seg = img.copy()
        img_seg = preprocess_deeplabv3(img_seg, self.imgsz)
        preds_seg = self.inference_triton_seg(img_seg, self.model_name, client)
        labels = np.argmax(preds_seg, axis=1)

        labels = cv2.resize(
            labels[0].astype(np.uint8), 
            (img.shape[1], img.shape[0]), 
            interpolation=cv2.INTER_NEAREST
        )

        labels = truncate_masks(labels, overlap)
        segments_with_classes = []

        # Add segments for each semantic class
        for i, class_name in enumerate(self.class_names):
            mask = (labels == (i + 1)).astype('uint8')
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                contour = np.reshape(contour, (-1, 2))

                # Throw away contours with too small number of points (as invalid)
                if len(contour) < 4:
                    continue
                
                class_name = self.class_names[i]
                if class_name is None:
                    continue

                segments_with_classes.append({'class': class_name, 'segment': contour, 'confidence': 1.})

        return segments_with_classes

    def inference_triton_seg(self, img_in: np.ndarray, model_name: str, client: httpclient.InferenceServerClient) -> np.ndarray:
        
        # Setting up input and output
        input = httpclient.InferInput("input", img_in.shape, datatype="FP32")
        input.set_data_from_numpy(img_in, binary_data=True)

        output = httpclient.InferRequestedOutput("output", binary_data=True)

        # Querying the server
        results = client.infer(model_name=model_name, inputs=[input], outputs=[output])

        inference_output = results.as_numpy('output')

        return inference_output


def fix_input_dims(
        client: httpclient.InferenceServerClient,
        model_name: str,
        input_array: np.ndarray) -> np.ndarray:
    """Check the model input format and reshape the input array to the appropriate shape.
    More precisely, check if we need to convert input shape from 3d to 4d

    :param client: Triton http client
    :param model_name: name associaced with the selected model 
    :param input_array: source 3d input array
    :return: input array, reshaped to the appropriate shape
    """

    # Get input dims from mpdel config
    model_config = client.get_model_config(model_name)
    dims = model_config['input'][0]['dims']

    # If 3d is needed, then warn and leave input as is
    if len(dims) == 3:
        warn_msg = f"3-dim input {dims} for model '{model_name}' is deprecated. " \
                    f"Please use 4-dim input {[1, *dims]}"
        warnings.warn(warn_msg)

    else:   # in this case, assume we need to use 4d array
        input_array = input_array[np.newaxis, ...]
    
    return input_array


def truncate_masks(masks: np.ndarray, overlap: int = 128):
    if len(masks.shape) == 2:
        return masks[overlap: masks.shape[0] - overlap, overlap: masks.shape[1] - overlap]

    return masks[:, overlap: masks.shape[1] - overlap, overlap: masks.shape[2] - overlap]


def filter_predictions_by_classes(predictions: List[dict], class_names_common: List[str]):
    filtered_predictions = []

    for prediction in predictions:
        class_name = prediction['class']
        key_idx = list(class_names_common.values()).index(class_name)
        if key_idx == -1:
            continue

        class_idx = list(class_names_common.keys())[key_idx]
        prediction['class'] = class_idx
        filtered_predictions.append(prediction)

    return filtered_predictions
        
