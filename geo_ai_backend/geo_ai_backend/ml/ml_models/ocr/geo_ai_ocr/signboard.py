import os
import cv2
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import pyproj
from typing import List, Optional
import torch
import albumentations as A
import onnxruntime as ort
from geo_ai_backend.ml.ml_models.ocr.geo_ai_ocr.cropinfo import CropInfo
from geo_ai_backend.ml.ml_models.ocr.geo_ai_ocr.image_preproc import superresolution
from geo_ai_backend.ml.ml_models.ocr.geo_ai_ocr.reader import TritonEasyocrReader



class SignBoard:
    """
    Class for storing and processing information about each unique signboard in a scene.
    """

    def __init__(self, signboard_id: int, max_best_crops: int = -1):
        self.crops_info: List[CropInfo] = []  # Stores CropInfo objects
        self.max_best_crops = max_best_crops
        self.best_crops_info = []

        self.best_img_name: Optional[str] = None
        self.best_crop: Optional[np.ndarray] = None
        self.best_crop_info: Optional[CropInfo] = None
        self.best_crop_edited: Optional[np.ndarray] = None
        self.best_crop_text_bboxes: List[dict] = []  # Stores text bounding boxes info

        self.title: str = ''
        self.signboard_id: int = signboard_id
        self.geo_coords: Optional[Point] = None

    def add_crop(self, crop_info: CropInfo):
        """
        Add crop information to the signboard.
        """
        self.crops_info.append(crop_info)

    def choose_best_imgs(self, imgs_path: str, model_quality: torch.nn.Module = None):
        """
        Chooses the best image based on a weighted criteria.
        """
        self.__choose_best_imgs_weight(imgs_path, model_quality)

    #########################################

    def __preproc(self, ort_session: ort.InferenceSession = None):
        """
        Preprocess the best crop image. Enhance, binarize, and apply superresolution if needed.
        """
        img = self.best_crop.copy()
        # img = enhance_image(img)
        # img = binarize_image(img)

        if ort_session is not None:
            h, w = img.shape[:2]
            if h <= 256 or w <= 256:
                img = superresolution(img, ort_session)

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.best_crop_edited = img

    def get_text(
            self,
            reader_det: TritonEasyocrReader,
            reader_eng: TritonEasyocrReader,
            reader_ara: TritonEasyocrReader,
            classification_model=None,
    ):
        """
        Extracts text from the best crop of the signboard using OCR.
        """
        for crop in self.best_crops_info:
            self.best_crop = crop['crop_img']
            self.best_crop_info = crop['crop_info']

            self.__preproc()
            self.__get_coords()

            # find all words in the crop of the signboard
            det_res = self.find_text(reader_det)

            if det_res is None:
                return

            h, w = self.best_crop_edited.shape[:2]

            # recognize every word in the crop
            for det_type, dets in det_res.items():
                for det in dets:
                    bbox, text_img = self.__process_detection(det_type, det, w, h)
                    if text_img is None:
                        continue

                    lang = self.__get_lang_efnet(text_img, classification_model)
                    if lang not in ['eng', 'ara']:
                        continue

                    reader = reader_eng if lang == 'eng' else reader_ara

                    self.__recognize_and_store_text(reader, bbox, text_img, lang)

            if self.title.strip():
                break

    def find_text(self, reader: TritonEasyocrReader):
        img_crop = self.best_crop_edited

        try:
            res = reader(img_crop)
        except:
            return None

        det = {
            'horizontal_list': [],
            'free_list': []
        }

        horizontal_list = res[0][0]
        free_list = res[1][0]

        for bbox in horizontal_list:
            det['horizontal_list'].append(bbox)

        for poly in free_list:
            det['free_list'].append(poly)

        return det

    def __process_detection(self, det_type, det, w, h):
        if det_type == 'horizontal_list':
            bbox = det
            x1, x2, y1, y2 = bbox
            x1, x2, y1, y2 = max(0, x1), min(w, x2), max(0, y1), min(h, y2)
            bbox = x1, x2, y1, y2

            text_img = self.best_crop_edited[y1:y2, x1:x2]

        elif det_type == 'free_list':
            text_row_poly = np.array(det).reshape(-1, 2).astype(np.int32)
            bbox = cv2.boundingRect(text_row_poly)

            mask = np.zeros_like(self.best_crop_edited)

            cv2.fillPoly(mask, [text_row_poly], (255, 255, 255))
            text_img = cv2.bitwise_and(self.best_crop_edited, mask)

            x1, y1, w, h = bbox

            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = x1 + w, y1 + h

            bbox = x1, x2, y1, y2

            text_img = text_img[y1:y2, x1:x2]

        else:
            return None, None

        return bbox, text_img

    def __recognize_and_store_text(self, reader: TritonEasyocrReader, bbox, img: np.ndarray, lang: str):
        """
        Recognizes text from the given image and stores the results.
        """
        recog_result = reader(img)
        text_row = [recog_result[0][1]]
        confidence = recog_result[0][2]

        threshold = 0.1
        if confidence < threshold:
            return

        self.best_crop_text_bboxes.append({'bbox': bbox, 'lang': lang, 'text': text_row})
        res_str = ' '.join(text_row)
        self.title += res_str + ' '

    # TODO: fix bug with empty centers
    def __get_coords(self):
        """
        Calculates the geographical coordinates of the signboard.
        """
        if self.best_crop_info.target_ids is None:
            return

        points = self.best_crop_info.target_ids
        centers = np.expand_dims(self.best_crop_info.center, axis=0)

        geo_coords = get_gis_positions(points, centers)
        self.geo_coords = geo_coords

    #########################################

    def __choose_best_img_by_property(self, imgs_path: str, property: str, reverse: bool = False):
        """
        Generic method to choose the best crop based on a specific property.

        Parameters:
        imgs_path (str): Path to the images directory.
        property (str): The property to sort the crops by (e.g., 'quality', 'distance', 'area').
        reverse (bool): Whether to sort in reverse order (higher values are better).
        """
        if not self.crops_info:
            raise ValueError("No crops information available")

        sorted_crops = sorted(self.crops_info, key=lambda k: getattr(k, property, 0), reverse=reverse)
        best_crop_info = sorted_crops[0] if sorted_crops else None

        if best_crop_info:
            self.__set_best_crop(imgs_path, best_crop_info)

    def __choose_best_img_quality(self, imgs_path: str):
        """
        Choose the best crop based on the highest quality score.
        """
        self.__choose_best_img_by_property(imgs_path, 'quality', reverse=True)

    def __choose_best_img_distance(self, imgs_path: str):
        """
        Choose the best crop based on the closest distance.
        """
        self.__choose_best_img_by_property(imgs_path, 'distance')

    def __choose_best_img_area(self, imgs_path: str):
        """
        Choose the best crop based on the largest area.
        """
        self.__choose_best_img_by_property(imgs_path, 'area', reverse=True)

    def __choose_best_imgs_weight(self, imgs_path: str, model_quality):
        """
        Internal method to choose the best image based on weighted properties.
        """
        weights = {
            'angle': 0.8,
            'distance': 0.3,
            'area': 0.0,
            'iou': 1.0,
        }

        properties = self.__calculate_properties_scores()
        max_best_crops = self.max_best_crops if self.max_best_crops != -1 else len(self.crops_info)

        selected_crops = self.__find_best_crops_by_scores(
            properties,
            weights,
            max_best_crops
        )

        for crop_info in selected_crops:
            img_name = crop_info.img_name
            bbox = crop_info.bbox
            crop_img = self.__read_crop_image(imgs_path, img_name, bbox)

            if crop_img is not None:
                self.best_crops_info.append({
                    'img_name': img_name,
                    'crop_img': crop_img,
                    'crop_info': crop_info
                })

    def __get_score(self, property: str):
        score = []
        if property == 'angle':
            max_angle = 90.0
            score = [crop_info.angle / max_angle for crop_info in self.crops_info]

        elif property == 'quality':
            # score = [np.exp(-crop_info.quality) for crop_info in self.crops_info]
            score = [0 for crop_info in self.crops_info]

        elif property == 'distance':
            lambda_dist = 50
            score = [
                np.exp(-crop_info.distance / lambda_dist) for crop_info in self.crops_info
            ]

        elif property == 'area':
            lambda_area = 50000
            score = [
                1 - np.exp(-crop_info.area / lambda_area) for crop_info in self.crops_info
            ]

        elif property == 'iou':
            score = [crop_info.iou for crop_info in self.crops_info]

        else:
            raise ValueError(f'Unknown property: {property}')

        score = np.array(score)

        # set to 0 if score is too low
        score[score < 0.1] = 0

        return score

    def __calculate_properties_scores(self):
        """
        Calculates scores for each property of the crops.
        """
        properties = {'angle': [], 'quality': [], 'distance': [], 'area': [], 'iou': []}
        for prop in properties.keys():
            properties[prop] = self.__get_score(prop)
        return properties

    def __find_best_crops_by_scores(self, properties: dict, weights: dict, max_crops: int):
        """
        Finds the best crops based on the calculated scores and weights for each property.
        """
        scores = []
        for crop_info in self.crops_info:
            score = 0
            for prop, prop_scores in properties.items():
                crop_index = self.crops_info.index(crop_info)
                score += weights.get(prop, 0) * prop_scores[crop_index]
            scores.append((score, crop_info))

        scores.sort(reverse=True, key=lambda x: x[0])
        return [crop_info for score, crop_info in scores[:max_crops]]

    def __check_crop_quality(self, img: np.ndarray, model_quality: torch.nn.Module):
        res = model_quality.predict(img)

        classes = res[0].names
        probs = res[0].probs.data.tolist()

        qual = classes[np.argmax(probs)]
        return qual

    def __set_best_crops(self, imgs_path: str, best_crops_info: List[CropInfo]):
        """
        Sets the best crops based on the given list of CropInfo objects.
        """
        self.best_crops_info = []
        for crop_info in best_crops_info:
            img_name = crop_info.img_name
            bbox = crop_info.bbox

            crop_img = self.__read_crop_image(imgs_path, img_name, bbox)
            if crop_img is not None:
                self.best_crops_info.append({
                    'img_name': img_name,
                    'crop_img': crop_img,
                    'crop_info': crop_info
                })

    def __read_crop_image(self, imgs_path: str, img_name: str, bbox: np.ndarray):
        """
        Reads and returns the cropped image from the file system.
        """
        try:
            crop_img = cv2.imread(os.path.join(imgs_path, img_name))
            if crop_img is not None:
                x1, y1, x2, y2 = map(int, bbox)
                return crop_img[y1:y2, x1:x2]
        except Exception as e:
            print(f"Error reading image: {e}")
        return None

    # def _choose_best_img_(self, imgs_path: str):
    #     if self.signboard_id in [1, 19, 13, 6, 3, 4, 21, 26, 10, 29, 11, 7, 8, 9, 17, 32, 14, 2]:
    #         self._from_csv(imgs_path)
    #     else:
    #         self._choose_best_img_quality(imgs_path)

    # def _from_csv(self, imgs_path: str):
    #     csv_file = r'D:\SKZ\GEO_AI\geo_ai_ocr\best_images.csv'
    #     df = pd.read_csv(csv_file, sep=';')
    #
    #     self.best_img_name = df[df['signboard_id'] == self.signboard_id]['best_img'].values[0]
    #     self.best_img_name += '.jpg'
    #
    #     # choose best crop
    #     for crop_info in self.crops_info:
    #         if crop_info.img_name == self.best_img_name:
    #             best_crop_info = crop_info
    #             break
    #
    #     crop_img = cv2.imread(os.path.join(imgs_path, best_crop_info.img_name))
    #     bbox = best_crop_info.bbox
    #     crop = crop_img[bbox[1]:bbox[3], bbox[0]:bbox[2]]
    #
    #     self.best_crop = crop
    #     self.best_crop_info = best_crop_info

    # def _get_first(self, imgs_path: str):
    #     best_crop_info = self.crops_info[0]
    #
    #     crop_img = cv2.imread(os.path.join(imgs_path, best_crop_info.img_name))
    #     bbox = best_crop_info.bbox
    #     crop = crop_img[bbox[1]:bbox[3], bbox[0]:bbox[2]]
    #
    #     self.best_crop = crop
    #     self.best_crop_info = best_crop_info

    # def _get_lang_resnet(self, img: np.ndarray, model: torch.nn.Module) -> str:
    #     classes = {
    #         0: 'eng',
    #         1: 'ara',
    #     }
    #
    #     text_img_tensor = resnet_inference.preproc(img)
    #     text_img_tensor = text_img_tensor.cuda()
    #
    #     # classification
    #     with torch.no_grad():
    #         out = model(text_img_tensor)
    #         output = torch.argmax(out, dim=1)
    #         output = output.cpu().numpy()
    #         lang = classes[output.item()]
    #
    #     return lang
    #
    # def _get_lang_yolo(self, img: np.ndarray, model: torch.nn.Module) -> str:
    #     res = model.predict(img)
    #
    #     classes = res[0].names
    #     probs = res[0].probs.data.tolist()
    #
    #     lang = classes[np.argmax(probs)]
    #
    #     return lang

    #########################################

    def __get_lang_efnet(self, img: np.ndarray, model) -> str:
        """
        Detects the language of the given image using an EfficientNet model.
        """
        classes = ['ara', 'eng']

        img = add_padding(image=img)['image']

        img = img.astype(np.float32)
        img /= 255.0
        img = img.transpose(2, 0, 1)
        img = np.expand_dims(img, axis=0)

        # input_name = model.get_inputs()[0].name
        # output_name = model.get_outputs()[0].name

        # res = model.run([output_name], {input_name: img})
        # res = res[0]

        # (1, 3, 224, 224)
        # (1, 2)

        res = model([img])[0]

        res = np.argmax(res)
        lang = classes[res]

        return lang


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


add_padding = A.Compose([
    A.LongestMaxSize(max_size=224, always_apply=True),
    A.PadIfNeeded(min_height=224, min_width=224, always_apply=True, border_mode=0)
])
