import os
from typing import List, Dict, Any, Tuple
import re

from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.config import Config
from geo_ai_backend.project.schemas import (
    FieldNameInputEnum,
    Panorama360DataSchemas
)
from geo_ai_backend.utils import (
    create_dir,
    delete_dir,
    copy_file_from_dir,
)


def check_folder_nextcloud_exists(folder: str) -> bool:
    origin = f"static/nextcloud/Admin123/files/{folder}"
    if not os.path.exists(origin):
        return False
    return True


def validation_aerial(folder: str) -> Tuple[bool, Dict[str, str]]:
    origin = f"static/nextcloud/Admin123/files/{folder}"

    if not os.path.exists(origin) or not os.listdir(origin):
        return False, {"message": f"{folder} folder is empty or does not exist.", "code": "FOLDER_EMPTY_OR_NOT_EXIST"}

    tif_files = [f for f in os.listdir(origin) if f.endswith('.tif') or not f.endswith('.jpg')]
    if not tif_files:
        return False, {"message": f".tif files not found in {folder}.", "code": "TIF_FILES_NOT_FOUND"}

    return True, {}


def validation_sattelite(folder: str) -> Tuple[bool, Dict[str, str]]:
    origin = f"static/nextcloud/Admin123/files/{folder}"

    if not os.path.exists(origin) or not os.listdir(origin):
        return False, {"message": f"{folder} folder is empty or does not exist.", "code": "FOLDER_EMPTY_OR_NOT_EXIST"}

    tif_files = [f for f in os.listdir(origin) if f.endswith('.tif') or not f.endswith('.jpg')]
    if not tif_files:
        return False, {"message": f".tif files not found in {folder}.", "code": "TIF_OR_JPG_FILES_NOT_FOUND"}

    return True, {}


def validation_360(folder: str) -> Tuple[bool, Dict[str, str]]:

    path = f"static/nextcloud/Admin123/files/{folder}"

    if not os.path.exists(path) or not os.listdir(path):
        return False, {"message": f"{folder} folder is empty or does not exist.", "code": "FOLDER_EMPTY_OR_NOT_EXIST"}

    list_folder = [i for i in os.listdir(path) if "result" not in i and os.path.isdir(os.path.join(path, i))]
    if not list_folder:
        return False, {"message": f"invalid '{folder}' folder format", "code": "INVALID_FOLDER_FORMAT"}

    for subfolder in os.listdir(path):
        if "result" in subfolder:
            continue
        subfolder_path = os.path.join(path, subfolder)
        if os.path.isdir(subfolder_path) and not os.listdir(subfolder_path):
            return False, {"message": f"{subfolder} is empty", "code": "FOLDER_IS_EMPTY"}
        elif os.path.isdir(subfolder_path) and os.listdir(subfolder_path):
            las_files = [f for f in os.listdir(subfolder_path) if f.endswith('.las')]
            if len(las_files) > 1:
                return False, {"message": f"{subfolder} contains more or less than 1 las file", "code": "MORE_OR_LESS_THAN_ONE_LAS_FILE"}

            csv_files = [f for f in os.listdir(subfolder_path) if f.endswith('.csv')]
            if len(csv_files) != 1:
                return False, {"message": f"{subfolder} contains more or less than 1 csv file", "code": "MORE_OR_LESS_THAN_ONE_CSV_FILE"}

            jpg_files = [f for f in os.listdir(subfolder_path) if f.endswith('.jpg')]
            if len(jpg_files) < 1:
                return False, {"message": f"{subfolder} does not contain any jpg file", "code": "NO_JPG_FILES"}

    return True, {}



def download_files_from_nextcloud(
    folder: str,
    save_path: str,
    filetypes: List[str],
    folder_type: bool,
    save_path_prepare: str = None
) -> bool:
    path_folder = os.path.dirname(save_path)
    delete_dir(path=path_folder)
    create_dir(path=save_path)
    if save_path_prepare:
        create_dir(path=save_path_prepare)
    origin = f"static/nextcloud/Admin123/files/{folder}"

    if not os.path.exists(origin):
        return False

    files = []
    files_360 = []
    for i in os.listdir(origin):
        if bool(re.search("result", i)):
            continue
        for filetype in filetypes:
            if i.endswith(filetype):
                files.append(i)
        if folder_type and os.path.isdir(f"{origin}/{i}"):
            files_360.append(i)

    tif_files, other_files = prepare_data_for_tif_jpg(files=files, filetypes=filetypes)

    files_to_copy = [
        (files_360, save_path),
        (tif_files, save_path),
        (other_files, save_path_prepare)
    ]

    for file_list, target_path in files_to_copy:
        if not bool(file_list):
            continue
        for file in file_list:
            copy_file_from_dir(filename=file, origin=origin, target=target_path)

    copy_result1 = True
    copy_result2 = True
    copy_result3 = True
    if tif_files:
        copy_result1 = bool(os.listdir(save_path))

    if other_files:
        copy_result2 = bool(os.listdir(save_path_prepare))

    if files_360:
        copy_result3 = bool(os.listdir(save_path))

    return all([copy_result1, copy_result2, copy_result3])


def prepare_data_for_tif_jpg(
    files: List[str], filetypes: List[str]
) -> Tuple[List[str], List[str]]:
    tif_files = []
    other_files = []
    base_names_with_tif = set()

    for file in files:
        if file.endswith('.tif'):
            base_name = file.rsplit('.', 1)[0]
            tif_files.append(file)
            base_names_with_tif.add(base_name)

    for file in files:
        base_name = [
            file.rsplit(filetype, 1)[0] for filetype in filetypes
            if file.endswith(filetype)
        ][0]
        if not file.endswith('.tif') and base_name not in base_names_with_tif:
            other_files.append(file)

    return tif_files, other_files


def prepare_data_for_csv(
    data: List[Dict[str, Any]], list_dir: List[str], sub_path: str,
) -> List[Panorama360DataSchemas]:
    schemas = []
    if all(["pano" in filename for filename in list_dir]):
        list_dir = rename_jpg_files_to_mask(list_dir=list_dir, sub_path=sub_path)
    for row in data:
        image_list = get_filename_from_csv_name(
            filename_from_csv=row[FieldNameInputEnum.name.value],
            list_dir=list_dir,
            sub_path=sub_path
        )
        if not image_list:
            continue

        panorama_schemas = create_panorama_360_schemas(names=image_list, row=row)
        for schema in panorama_schemas:
            schemas.append(schema)

    return schemas


def rename_jpg_files_to_mask(list_dir: list[str], sub_path: str) -> list[str]:
    cfg = Config()
    source_template = cfg.template_img_name_alternative
    target_template = cfg.template_img_name
    renamed_files = []

    for path_file in list_dir:
        filename = os.path.basename(path_file)
        match = re.match(source_template, filename)
        if match:
            part1, part2, part3 = match.groups()
            new_filename = target_template.format(int(part1), int(part2), int(part3))
            src = os.path.join(sub_path, filename)
            dst = os.path.join(sub_path, new_filename)
            os.rename(src, dst)
            renamed_files.append(dst)

    return renamed_files


def get_filename_from_csv_name(
    filename_from_csv: Dict[str, Any], list_dir: List[str], sub_path: str
) -> List[str]:
    filename_from_csv = filename_from_csv.split('_')
    name_scene_from_csv = int(filename_from_csv[1])
    name_photo_from_csv = int(filename_from_csv[2])
    image_list = []
    for i in list_dir:
        name_list = os.path.splitext(i)[0].split(' ')
        name_photo = int(name_list[-1].split('_')[1])
        name_scene = int([i for i in name_list if 'Camera' in i][0].split('_')[0])
        if (name_photo == name_photo_from_csv) and (name_scene == name_scene_from_csv):
            created_files_scene_img_nums(
                sub_path=sub_path,
                scene_num=len(filename_from_csv[1]),
                img_num=len(filename_from_csv[2]),
            )
            image_list.append(i)
    return image_list


def created_files_scene_img_nums(sub_path: str, scene_num: int, img_num: int) -> None:
    with open(os.path.join(sub_path, f"scene_num_{scene_num}"), "w"):
        pass
    with open(os.path.join(sub_path, f"img_num_{img_num}"), "w"):
        pass


def create_panorama_360_schemas(
    names: List[str], row: Dict[str, Any]
) -> List[Panorama360DataSchemas]:
    for name in names:
        yield Panorama360DataSchemas(
            name=os.path.splitext(name)[0],
            longitude=row[FieldNameInputEnum.longitude.value],
            latitude=row[FieldNameInputEnum.latitude.value],
        )

