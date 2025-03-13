from geo_ai_backend.ml.ml_models.aerial_satellite.inference.compare.merge_zips import (
    merge_files
)
from geo_ai_backend.ml.ml_models.aerial_satellite.inference.triton_inference import (
    DEFAULT_CLASS_NAMES_YOLO,
    DEFAULT_CLASS_NAMES_DEEPLAB,
)


def main():
    
    list_paths_dirs = [
        '/home/student2/workspace/geo_ai_backend/geo_ai_backend/ml/ml_models/aerial_satellite/detection_result/True_1255',
        '/home/student2/workspace/geo_ai_backend/geo_ai_backend/ml/ml_models/aerial_satellite/detection_result/True_1256',
        '/home/student2/workspace/geo_ai_backend/geo_ai_backend/ml/ml_models/aerial_satellite/detection_result/True_1257',
        '/home/student2/workspace/geo_ai_backend/geo_ai_backend/ml/ml_models/aerial_satellite/detection_result/True_1258',
        '/home/student2/workspace/geo_ai_backend/geo_ai_backend/ml/ml_models/aerial_satellite/detection_result/True_1259',
    ]
    save_to = 'save_to'
    res_name = 'res_name'

    classes_list = DEFAULT_CLASS_NAMES_YOLO + DEFAULT_CLASS_NAMES_DEEPLAB
    
    merge_files(
        list_paths_dirs,
        save_to,
        res_name,
        classes_list,
        remove_res_dir=True,
    )


if __name__ == '__main__':
    main()
