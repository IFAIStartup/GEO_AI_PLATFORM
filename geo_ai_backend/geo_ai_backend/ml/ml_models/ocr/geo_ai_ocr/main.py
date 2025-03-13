import json
from pathlib import Path
import onnxruntime as ort
from easydict import EasyDict
import pickle
from geo_ai_backend.ml.ml_models.ocr.geo_ai_ocr.funcs import create_signboards_list, get_json_data, get_text, save_imgs
from geo_ai_backend.ml.ml_models.ocr.geo_ai_ocr.utils import load_models, check_save_dir

ROOT = Path().resolve()
SRC_DIR = r'D:\SKZ\GEO_AI\360\geo_ai_data\shots\4'


def OCR_inference(crops_list: list, models: EasyDict[str, ort.InferenceSession], src_dir: str) -> dict:
    signboards_list = create_signboards_list(crops_list, point_cloud=True)
    # print('signboards_list', len(signboards_list))
    get_text(signboards_list, models, src_dir)

    # check directory
    # save_imgs(signboards_list, SRC_DIR, save_dir)
    json_dist = get_json_data(signboards_list)
    return signboards_list, json_dist


if __name__ == '__main__':
    MODELS_DIR = ROOT / 'models'
    CLASSIFICATION_LANGUAGE_MODEL = 'effnetb0_051023.onnx'

    with open('crops_list.pkl', 'rb') as f:
        crops_list = pickle.load(f)

    for crop_info in crops_list:
        crop_info.img_name = crop_info.img_data['img_name']

    models = load_models(models_path=MODELS_DIR, classification_language_model_path=CLASSIFICATION_LANGUAGE_MODEL)
    results = OCR_inference(crops_list, models, SRC_DIR)
    # print(results)
