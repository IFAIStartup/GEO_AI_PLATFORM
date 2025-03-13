import os
import cv2
from abc import ABC
import numpy as np
from typing import Tuple, List, Dict, Sequence, Any
from numpy import ndarray
import tritonclient.http as httpclient
import onnxruntime as ort
from geo_ai_backend.ml.ml_models.utils.yolo import (
    postprocess_yolo,
    preprocess_yolo,
)
from geo_ai_backend.ml.ml_models.utils.deeplab import preprocess_deeplabv3
from geo_ai_backend.ml.ml_models.utils.model_sets import (
    ModelSet
)
from geo_ai_backend.ml.ml_models.utils.model_info import (
    ModelInfo
)
from geo_ai_backend.ml.ml_models.utils.triton_inference import (
    inference_pipeline, 
    create_model_sets,
    get_tiles,
    add_padding,
    get_tiles_meta,
)


class Inferencer(ABC):
    """Implementor of inference logic"""

    def __call__(self,
                 input_dict: Dict[str, np.ndarray],
                 model_outs: Sequence[str],
                 *args,
                 **kwargs) -> Dict[str, np.ndarray]:
        """Perform inference

        Args:
            input_dict (Dict[str, np.ndarray]): dictionary of input arrays
            model_outs (Sequence[str]): sequence of model output names

        Returns:
            Dict[str, np.ndarray]: dictionary of output arrays with keys - output names
        """
        pass


class TritonInferencer(Inferencer):
    """Concrete implementor of inference for triton server client.
    This class implements the specific logic for performing inference using Triton Server.

    Attributes:
        model_name (str): The name of the model to be used for inference.
        client (httpclient.InferenceServerClient): The Triton Server client instance.
    """

    def __init__(self, model_name: str, triton_client: httpclient.InferenceServerClient) -> None:
        """
        Args:
            model_name (str): The name of the model to be used for inference.
            triton_client (httpclient.InferenceServerClient): The object connect of the Triton Server.
        """
        self.model_name = model_name
        self.client = triton_client

    def __call__(self,
                 input_dict: Dict[str, np.ndarray],
                 model_outs: Sequence[str],
                 *args,
                 **kwargs) -> Dict[str, np.ndarray]:
        """
        Perform inference using Triton Server.

        Args:
            input_dict (Dict[str, np.ndarray]): A dictionary of input arrays.
            model_outs (Sequence[str]): A sequence of model output names.

        Returns:
            Dict[str, np.ndarray]: A dictionary of output arrays with keys as output names.
        """

        # Setting up input and output
        inputs = []
        for name in input_dict:
            inp = httpclient.InferInput(name, input_dict[name].shape, datatype="FP32")
            inp.set_data_from_numpy(input_dict[name], binary_data=True)
            inputs.append(inp)

        outputs = []
        for name in model_outs:
            out = httpclient.InferRequestedOutput(name, binary_data=True)
            outputs.append(out)

        # Querying the server
        results = self.client.infer(
            model_name=self.model_name,
            inputs=inputs,
            outputs=outputs
        )

        inference_outputs = [results.as_numpy(name) for name in model_outs]
        return inference_outputs


class ONNXInferencer(Inferencer):
    """Concrete implementor of inference for onnxruntime session.
    This class implements the specific logic for performing inference using ONNX Runtime.

    Attributes:
        model_path (str): The path to the ONNX model file.
        providers (Sequence[str]): A sequence of providers for ONNX Runtime.
    """
    # TODO: add provider examples

    def __init__(self, model_path: str, providers: Sequence[str] = None) -> None:
        """
        Args:
            model_path (str): The path to the ONNX model file.
            providers (Sequence[str]): A sequence of providers for ONNX Runtime (e.g., ...).
        """
        super().__init__()
        self.ort = ort.InferenceSession(model_path, providers=providers)

    def __call__(self, input_dict: Dict[str, np.ndarray], check_dims=True, *args, **kwargs) -> Dict[str, np.ndarray]:
        """
        Perform inference using ONNX Runtime.

        Args:
            input_dict (Dict[str, np.ndarray]): A dictionary of input arrays.
            check_dims (bool): Whether to check and adjust input dimensions. Default is True.

        Returns:
            Dict[str, np.ndarray]: A dictionary of output arrays with keys as output names.
        """

        if check_dims:
            input_dict = self.check_dims(input_dict)
        outputs = self.ort.run(None, input_dict)
        return outputs

    def check_dims(self, input_dict: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        for key in input_dict:
            if len(input_dict[key].shape) == 3:
                input_dict[key] = np.expand_dims(input_dict[key], 0)
        return input_dict


class Model(ABC):
    """Abstraction of a ML model.

    This class serves as an abstraction for machine learning models, utilizing the Bridge pattern
    with the `Inferencer` class as the implementor.

    Attributes:
        inferencer (Inferencer): The implementor for inference logic.
        batch_size (int): The batch size used during inference (if dynamic is True - it is a max batch size).
        dynamic (bool): Flag indicating whether the model supports dynamic batch sizes.

    """

    inferencer: Inferencer
    batch_size: int
    dynamic: bool

    def __init__(self, inferencer: Inferencer, batch_size: int = 1, dynamic: bool = False, *args, **kwargs):
        """
        Args:
            inferencer (Inferencer): The implementor for inference logic.
            batch_size (int): The batch size used during inference. Default is 1.
            dynamic (bool): Flag indicating whether the model supports dynamic batch sizes. Default is False.
        """
        self.inferencer = inferencer
        self.batch_size = batch_size
        self.dynamic = dynamic

    def __call__(self, input_arrays: List[np.ndarray], *args, **kwargs) -> Any:
        """
        Performs inference using the specified input arrays.

        Args:
            input_arrays (List[np.ndarray]): List of input arrays for inference.

        Returns:
            Any: The result of the inference.
        """
        pass

    def get_inferencer(
            self,
            model_path: str,
            batch_size: int,
            dynamic: bool,
            inference_type: str,
            triton_client: httpclient.InferenceServerClient) -> Inferencer:

        assert inference_type in ['triton', 'onnx']
        if inference_type == 'triton':
            inferencer = TritonInferencer(model_path, triton_client)
        else:
            inferencer = ONNXInferencer(model_path, None)

        return inferencer

    def build_batches(self, preprocessed_arrays: List[np.ndarray]) -> List[np.ndarray]:

        batches = []
        if len(preprocessed_arrays) == 0:
            return batches

        batch_size = self.batch_size
        dynamic = self.dynamic

        num_of_batches = int(np.ceil(len(preprocessed_arrays) / batch_size))

        for i in range(num_of_batches):
            start_idx = batch_size * i
            stop_idx = min(batch_size * (i + 1), len(preprocessed_arrays))
            batch_arrays = preprocessed_arrays[start_idx: stop_idx]
            batch = np.array(batch_arrays)

            num_to_fill = max(0, batch_size - len(batch_arrays))

            if num_to_fill != 0 and not dynamic:
                zero_arrays = np.zeros((num_to_fill, *batch_arrays[0]), dtype=batch_arrays[0].dtype)
                batch = np.concatenate([batch, zero_arrays], axis=0)

            batches.append(batch)

        return batches


class YoloModel(Model):
    """Refined Abstraction of ML model (YOLOv8)"""
    def __init__(
            self,
            model_path: str,
            names: List[str],
            imgsz: Tuple[int, int],
            batch_size: int = 1,
            dynamic: bool = False,
            inference_type: str = 'triton',
            triton_client: httpclient.InferenceServerClient = None
    ):

        self.imgsz = imgsz
        self.names = names

        inferencer = self.get_inferencer(model_path, 1, False, inference_type, triton_client)
        super().__init__(inferencer, batch_size, dynamic)

    def __call__(self, input_arrays: List[np.ndarray], conf=0.15, squeeze_batch: bool = True) -> Any:
        preprocessed_arrays = self._preprocess(input_arrays)
        batches = self.build_batches(preprocessed_arrays)

        results = []
        for batch in batches:
            if len(batch) == 1 and squeeze_batch:
                batch = batch[0]
            preds_yolo = self.inferencer({'images': batch}, ('output0', 'output1'))
            batch_results = self._postprocess(preds_yolo, input_arrays, conf)
            results += batch_results

        return results

    def _preprocess(self, orig_imgs: List[np.ndarray]) -> List[np.ndarray]:
        preprocessed_imgs = []
        for orig_img in orig_imgs:
            preprocessed_img = preprocess_yolo(orig_img, self.imgsz)
            # img = np.expand_dims(img, axis=0)
            preprocessed_imgs.append(preprocessed_img)

        return preprocessed_imgs

    def _postprocess(self, preds: np.ndarray, input_arrays: List[np.ndarray], conf: float) -> np.ndarray:
        names_dict = {k: self.names[k] for k in range(len(self.names))}
        results = []
        for i in range(len(preds[0])):
            orig_imgsz = input_arrays[i].shape[:2]
            result = postprocess_yolo([preds[0][i: i + 1], preds[1][i: i + 1]], names_dict, orig_imgsz, self.imgsz, conf=conf)
            if len(result) > 0:
                results.append(result[0])
            else:
                results.append([np.zeros((0, 6)), np.zeros((0, orig_imgsz[0], orig_imgsz[1]))])
        return results


class DeepLabModel(Model):
    """Refined Abstraction of ML model (DeepLabv3+)"""
    def __init__(
            self,
            model_path: str,
            names: List[str],
            batch_size: int = 1,
            dynamic: bool = False,
            inference_type: str = 'triton',
            triton_client: httpclient.InferenceServerClient = None):

        self.names = names
        inferencer = self.get_inferencer(model_path, 1, False, inference_type, triton_client)
        super().__init__(inferencer, batch_size, dynamic)

    def __call__(self, input_arrays: List[np.ndarray]) -> Any:

        preprocessed_arrays = self._preprocess(input_arrays)
        batches = self.build_batches(preprocessed_arrays)

        results = []
        for batch in batches:
            preds_seg = self.inferencer({'input': batch}, ('output',))
            batch_results = self._postprocess(preds_seg, input_arrays)
            results += batch_results

        return results

    def _preprocess(self, orig_imgs: List[np.ndarray], *args, **kwargs) -> np.ndarray:
        preprocessed_imgs = []
        for orig_img in orig_imgs:
            preprocessed_img = preprocess_deeplabv3(orig_img)
            preprocessed_imgs.append(preprocessed_img[0])

        return preprocessed_imgs

    def _postprocess(self, preds_seg: np.ndarray, input_arrays: list, *args, **kwargs) -> np.ndarray:
        preds_seg = [preds_seg] if type(preds_seg) != list else preds_seg
        results = []
        for i in range(len(preds_seg[0])):
            labels = np.argmax(preds_seg[0][i], axis=0)
            h, w = input_arrays[i].shape[:2]
            labels = cv2.resize(labels.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)
            results.append(labels)

        return results


class LangClsModel(Model):
    def __init__(
        self,
        model_path: str,
        inference_type: str = 'onnx',
        triton_client: httpclient.InferenceServerClient = None
    ):
        if inference_type == 'triton':
            inferencer = TritonInferencer(model_path, triton_client)
        else:
            inferencer = ONNXInferencer(model_path)
        super().__init__(inferencer)

    def __call__(self, input_arrays: List[np.ndarray]) -> Any:
        model_in = 'onnx::Pad_0'
        model_out = '1043'

        results = []
        for arr in input_arrays:
            result = self.inferencer({model_in: arr}, (model_out,))[0]
            results.append(result)
        return results


class ModelEnsemble:
    def __init__(self,
                 yolo_model_path: str,
                 deeplab_model_path: str,
                 inference_type: str,
                 class_names_yolo: List[str],
                 class_names_deeplab: List[str],
                 triton_client: httpclient.InferenceServerClient,
                 imgsz_yolo = (1280, 1280)) -> None:

        self.inference_type = inference_type

        self.yolo_model = YoloModel(yolo_model_path, class_names_yolo, imgsz_yolo, 1, False, inference_type, triton_client)
        self.deeplab_model = DeepLabModel(deeplab_model_path, class_names_deeplab, 1, False, inference_type, triton_client)

    def __call__(self, imgs: List[np.ndarray], *args, **kwargs) -> Any:

        yolo_results = self.yolo_model(imgs)
        deeplab_results = self.deeplab_model(imgs)

        yolo_segs = []
        for res in yolo_results:
            yolo_segs.append(self._get_yolo_yolosegs(res))

        deeplab_segs = []
        for res in deeplab_results:
            deeplab_segs.append(self._get_deeplab_yolosegs(res))

        for batch in deeplab_segs:
            for seg in batch:
                seg[0] += len(self.yolo_model.names)

        all_segs = []
        for i in range(len(yolo_segs)):
            all_segs.append(yolo_segs[i] + deeplab_segs[i])
        return all_segs

    def _get_yolo_yolosegs(self, res: List[np.ndarray]):
        boxes, masks = res[:2]
        segs = boxes_masks2yolosegments(boxes, masks)
        return segs

    def _get_deeplab_yolosegs(self, labels: np.ndarray):
        all_segs = []
        for cls_id in range(labels.max()):
            mask = labels == (cls_id + 1)
            mask = mask.astype('uint8') * 255
            masks = [mask]
            boxes = [[0, 0, labels.shape[1], labels.shape[0], 1, cls_id]]
            segs = boxes_masks2yolosegments(boxes, masks)
            all_segs += segs
        return all_segs



def boxes_masks2yolosegments(boxes: np.ndarray, masks: np.ndarray):

    yolo_segments = []
    for i, mask in enumerate(masks):
        height, width = mask.shape[:2]
        conf, cls_id = boxes[i][4:6]
        contours, _ = cv2.findContours(mask.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            segment = cnt.astype('float64')
            segment[..., 0] /= width
            segment[..., 1] /= height
            segment = segment.reshape(-1).tolist()
            yolo_segments.append([int(cls_id)] + segment + [float(conf)])

    return yolo_segments


#####
# TODO: delete the above in the future


class InferenceAdapter:
    def __init__(
            self, 
            client: httpclient.InferenceServerClient, 
            model_sets: List[ModelSet],
            common_class_names: dict) -> None:
        
        self.client = client
        self.model_sets = model_sets
        self.common_class_names = common_class_names

    def __call__(self, imgs: List[np.ndarray], *args, **kwargs) -> List[List[float]]:
        results = []
        for img in imgs:
            res = self._inference_model_sets(
                img, 
                self.model_sets, 
                self.common_class_names, 
                self.client
            )
            results.append(res)
        return results

    def _inference_model_sets(
            self,
            img_in: np.ndarray,
            model_sets: List[ModelSet],
            common_class_names: dict,
            triton_client: httpclient.InferenceServerClient) -> List[dict]:

        objects_info_list = []

        for model_set in model_sets:
            inference_models = model_set.inference_models
            tile_size = model_set.tile_size
            overlap = model_set.overlap
            scale_factor = model_set.scale_factor

            # If scale factor less or equals zero, then we consider that
            # we need to rescale the input image to the tile size
            # and find actual scale factor.
            # Otherwise just resize image with required scale factor
            h, w = img_in.shape[:2]
            if scale_factor <= 0:
                scale_factor = min(tile_size / h, tile_size / w)
        
            img_resized = cv2.resize(img_in, (int(scale_factor * w), int(scale_factor * h)))

            # add padding to image to make it divisible by tile size
            img_padded = add_padding(img_resized, tile_size, overlap)

            # get tiles from image with overlap
            tiles = get_tiles(img_padded, tile_size, overlap)

            # Create tiles meta info from each tile using triton inference
            # tiles meta info contains class and polygon of each object
            tiles_meta = get_tiles_meta(
                tiles,
                common_class_names,
                tile_size,
                overlap,
                inference_models,
                triton_client,
            )

            # Resize tiles meta
            for tile_meta in tiles_meta:
                for obj in tile_meta:
                    obj['segment'] = obj['segment'].astype('float64')
                    obj['segment'] /= scale_factor
                    obj['segment'] = obj['segment'].astype('int32')
                
                objects_info_list += tile_meta
        
        yolo_labels = self._convert_to_yolo(objects_info_list, (w, h))
        return yolo_labels

    def _convert_to_yolo(self, objects_info_list: List[dict], imgsz: tuple):
        yolo_labels = []
        w, h = imgsz
        
        for obj in objects_info_list:
            segments = obj['segment'].astype('float64')
            segments[..., 0] /= w
            segments[..., 1] /= h
            
            segments = segments.reshape(-1).tolist()
            class_id = obj['class']
            confidence = obj['confidence']

            label = [class_id] + segments + [confidence]
            yolo_labels.append(label)
        
        return yolo_labels
    

def get_model_from_info_list(
        model_info_list: List[ModelInfo],
        client: httpclient.InferenceServerClient,
        common_class_names: dict) -> InferenceAdapter:
    
    model_sets = create_model_sets(model_info_list)
    model = InferenceAdapter(client, model_sets, common_class_names)
    return model


def get_image_segments(image_paths: List[str],
                       model: ModelEnsemble = None,
                       read_segments: bool = True,
                       save_segments: bool = True,
                       batch_size: int = 1):

    image_segments = {}
    for i in range(0, len(image_paths), batch_size):
        start_idx = i
        stop_idx = min(i + batch_size, len(image_paths))
        cur_img_paths = [image_paths[j] for j in range(start_idx, stop_idx)]
        batch_imgs = [cv2.imread(path) for path in cur_img_paths]

        cur_image_segments = {}

        # If we want to read complete segments, try to do it
        if read_segments:
            cur_image_segments = read_image_segments(cur_img_paths)

        # If we have model and we dont want to/cant read all images, do detection
        if model is not None and len(cur_image_segments) != len(cur_img_paths):
            segs = model(batch_imgs)

            for i in range(len(segs)):
                img_fn = os.path.basename(cur_img_paths[i])
                name, ext = os.path.splitext(img_fn)

                cur_image_segments[name] = segs[i]

        # If we want to save got results, save it in <scene_path>/segments/<image_name>.txt
        if save_segments:
            save_image_segments(cur_image_segments, cur_img_paths)

        for name in cur_image_segments:
            image_segments[name] = cur_image_segments[name]

    return image_segments


def read_image_segments(image_paths: List[str]) -> dict:

    image_segments = {}
    for image_path in image_paths:
        img_fn = os.path.basename(image_path)
        name, ext = os.path.splitext(img_fn)
        labels_dir = os.path.join(os.path.dirname(image_path), 'segments')
        labels_path = os.path.join(labels_dir, name + '.txt')

        if not os.path.exists(labels_path):
            continue

        with open(labels_path, 'r', encoding='utf-8') as f:
            rows = f.read().split('\n')

        image_segments[name] = []
        for row in rows:
            if row == '':
                continue

            row_data = list(map(float, row.split(' ')))
            if len(row_data) == 1:
                continue

            image_segments[name].append(row_data)

    return image_segments


def save_image_segments(image_segments: List[str], cur_image_paths: list):
    for image_path in cur_image_paths:
        name, _ = os.path.splitext(os.path.basename(image_path))

        if name not in image_segments:
            continue

        save_path = os.path.join(os.path.dirname(image_path), 'segments')
        os.makedirs(save_path, exist_ok=True)

        lines = []
        for segment in image_segments[name]:
            line = ' '.join(list(map(str, segment)))
            lines.append(line)
        text = '\n'.join(lines)

        txt_path = os.path.join(save_path, name + '.txt')
        with open(txt_path, 'w') as f:
            f.write(text)
