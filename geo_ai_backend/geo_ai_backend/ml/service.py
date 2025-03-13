from collections import Counter
import json
import os
import math
import requests
import shutil
from typing import Any, Dict, Generator, List, Tuple, Optional, Union
import glob

from geo_ai_backend.ml.ml_models.utils.model_info import (
    ModelInfo,
)
from geo_ai_backend.project.exceptions import EmptyNextcloudFolderException
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc

from geo_ai_backend.ml.ml_models.aerial_satellite.inference.compare.change_detection_360 import (
    change_detection_360,
)
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.object_localization_be_ocr import (
    get_pcd_localization_ocr,
    Config,
)
from geo_ai_backend.ml.ml_models.ai_360.inference.point_cloud.object_localization_be_wo_las import (
    get_pcd_localization_without_las,
)
from geo_ai_backend.project.schemas import TypeProjectEnum
from geo_ai_backend.ml.models import ML, MLClasses
from geo_ai_backend.ml.exceptions import (
    PathNotFoundException,
    FolderIsEmptyException,
    NotFoundConfigFileException,
    FolderWithMLIsNotExistsException,
    NextcloudIsNotResponding,
)
from geo_ai_backend.utils import copy_dir, copy_file_from_dir
from geo_ai_backend.ml.schemas import (
    Qualities,
    Result360Schemas,
    MLModelSchemas,
    MLModelsSchemas,
    TypeMLModelEnum,
    CreateMLModelSchemas,
)
from geo_ai_backend.ml.constants import API_PATH, BACKEND_HOST
from geo_ai_backend.ml.exceptions import NotFoundJson, NotFoundTfw
from geo_ai_backend.ml.ml_models.HAT.inference.triton_inference import (
    superresolution_image,
)
from geo_ai_backend.config import settings
from geo_ai_backend.ml.ml_models.aerial_satellite.inference.compare.change_detection import (
    change_detection,
)
from geo_ai_backend.ml.ml_models.ai_360.inference.triton_inference import get_360_images
from geo_ai_backend.ml.ml_models.aerial_satellite.inference.triton_inference import (
    get_aerial_satellite_image,
)
from geo_ai_backend.ml.utils import (
    create_dir,
    delete_dir,
    InferenceServerManager,
)
from geo_ai_backend.project.service import (
    get_projects_by_type_service,
    get_scene_img_nums_from_files_services, get_projects_by_ids_limit,
)
from geo_ai_backend.project.schemas import StatusProjectEnum


def get_ml_classes_by_name_service(name: str, db: Session) -> List[str]:
    db_ml_model = db.query(MLClasses).filter(MLClasses.name == name).first()
    return db_ml_model.type_of_objects


def get_ml_model_by_name_service(name: str, db: Session) -> ML:
    db_ml_model = db.query(ML).filter(ML.name == name).first()
    return db_ml_model


def get_ml_models_by_names_service(names: List[str], db: Session) -> List[ML]:
    db_ml_model = db.query(ML).filter(ML.name.in_(names)).all()
    return db_ml_model


def get_ml_model_by_link_service(link: str, db: Session) -> ML:
    db_ml_model = db.query(ML).filter(ML.link == link).first()
    return db_ml_model


def get_ml_model_by_id_service(id: int, db: Session) -> ML:
    db_ml_model = db.query(ML).filter(ML.id == id).first()
    return db_ml_model


def get_default_ml_models_service(db: Session) -> ML:
    return db.query(ML).filter(ML.default_model == True).all()


def get_default_constant_ml_models_service(db: Session, constant_model: bool = True) -> ML:
    return db.query(ML).filter(and_(ML.default_model == True, ML.constant == constant_model)).all()


def get_ml_model_by_type_of_data_service(type: str, view: str, db: Session) -> List[ML]:
    if type == TypeMLModelEnum.all:
        db_models = db.query(ML).filter(
            ML.constant == False,
        )
        return db_models.filter(ML.view == view).all()
    db_models = db.query(ML).filter(
        and_(
            ML.type_of_data.any(type),
            ML.constant == False,
        )
    )
    return db_models.filter(ML.view == view).all()


def update_type_of_objects_ml_model_service(
    id: int, type_of_objects: List[str], db: Session
) -> ML:
    db_ml_model = db.query(ML).filter(ML.id == id).first()
    db_ml_model.type_of_objects = type_of_objects
    db.commit()
    db.refresh(db_ml_model)
    return db_ml_model


def update_link_ml_model_service(id: int, link: str, db: Session) -> ML:
    db_ml_model = db.query(ML).filter(ML.id == id).first()
    db_ml_model.link = link
    db.commit()
    db.refresh(db_ml_model)
    return db_ml_model


def get_all_ml_models(
    search: str,
    filter: str,
    sort: str,
    reverse: bool,
    limit: int,
    page: int,
    default: bool,
    db: Session,
) -> ML:
    ml_model_table = db.query(ML).filter(
        and_(
            ML.constant == False,
            ML.default_model == default,
        )
    )
    if search:
        ml_model_table = ml_model_table.filter(
            ML.name.like(f"%{search}%"),
        )

    if filter != TypeMLModelEnum.all:
        ml_model_table = ml_model_table.filter(
            and_(
                ML.type_of_data.any(filter),
                ML.constant == False,
            )
        )

    total = len(ml_model_table.all())
    offset = (page - 1) * limit
    pages = math.ceil(total / limit) if total else 0

    sort_field = ML.created_at
    if sort == "name":
        sort_field = ML.name

    if not reverse:
        ml_model_table = ml_model_table.order_by(desc(sort_field))
    else:
        ml_model_table = ml_model_table.order_by(asc(sort_field))

    db_ml_model = ml_model_table.offset(offset).limit(limit).all()

    if not db_ml_model:
        return MLModelsSchemas(
            models=[], page=page, pages=pages, total=total, limit=limit
        )

    ml_model_list = [
        {
            "id": i.id,
            "name": i.name,
            "type_of_data": i.type_of_data,
            "type_of_objects": i.type_of_objects,
            "default_model": i.default_model,
            "task_id": i.task_id,
            "task_result": i.task_result,
            "status": i.status,
            "created_at": i.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "mlflow_url": i.ml_flow_url,
            "created_by": i.created_by,
        }
        for i in db_ml_model
    ]

    models = [MLModelSchemas(**i) for i in ml_model_list]
    return MLModelsSchemas(
        models=models,
        page=page,
        pages=pages,
        total=total,
        limit=limit,
    )


def create_ml_model_service(
    ml_model: CreateMLModelSchemas, username: str, db: Session
) -> MLModelSchemas:
    db_ml_model = ML(
        name=ml_model.name,
        link=ml_model.link,
        type_of_data=[ml_model.type_of_data],
        type_of_objects=[],
        default_model=False,
        constant=False,
        created_by=username,
    )
    db.add(db_ml_model)
    db.commit()
    db.refresh(db_ml_model)
    return MLModelSchemas(
        id=db_ml_model.id,
        name=db_ml_model.name,
        type_of_data=db_ml_model.type_of_data,
        type_of_objects=db_ml_model.type_of_objects,
        default_model=db_ml_model.default_model,
        task_id=db_ml_model.task_id,
        task_result=db_ml_model.task_result,
        status=db_ml_model.status,
        created_at=db_ml_model.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        mlflow_url=db_ml_model.ml_flow_url,
        created_by=db_ml_model.created_by,
    )


def delete_ml_model_by_id_service(id: int, db: Session) -> ML:
    db_ml_model = db.query(ML).filter(ML.id == id).first()
    db.delete(db_ml_model)
    db.commit()
    return MLModelSchemas(
        id=db_ml_model.id,
        name=db_ml_model.name,
        type_of_data=db_ml_model.type_of_data,
        type_of_objects=db_ml_model.type_of_objects,
        default_model=db_ml_model.default_model,
        task_id=db_ml_model.task_id,
        task_result=db_ml_model.task_result,
        status=db_ml_model.status,
        created_at=db_ml_model.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        mlflow_url=db_ml_model.ml_flow_url,
        created_by=db_ml_model.created_by,
    )


def load_ml_model_service(folder: str) -> int:
    path = f"static/nextcloud/Admin123/files/ml_models/{folder}"
    if not os.path.exists(path):
        raise PathNotFoundException
    if not os.listdir(path):
        raise FolderIsEmptyException
    if not any(".pbtxt" in i for i in os.listdir(path)):
        raise NotFoundConfigFileException
    if "1" not in os.listdir(path):
        raise FolderWithMLIsNotExistsException
    copy_dir(origin=path, target=f"static/models/{folder}", dirs_exist_ok=True)
    status_code = load_ml_model_triton_service(name=folder)
    return status_code


def get_index_ml_models_triton_service() -> Optional[List[Dict[str, str]]]:
    url = f"http://{settings.TRITON_HOST}:{settings.TRITON_PORT}/v2/repository/index"
    response = requests.request("POST", url)
    if response and response.status_code == 200:
        return response.json()
    return None


def load_ml_model_triton_service(
    project_id: int, project_type: str, name: str, db: Session
) -> Optional[int]:
    url = f"http://{settings.TRITON_HOST}:{settings.TRITON_PORT}/v2/repository/models/{name}/load"
    response = requests.request("POST", url)
    return response.status_code


def get_unused_quality_models(quality: Union[str, None]):
    qualities_model = [enum.value for enum in Qualities]
    return [model for model in qualities_model if quality != model]


def load_default_ml_model_triton_service(
    project_type: str, db: Session, quality: Union[str, None] = None, constant_model = True
) -> None:
    index_models = get_index_ml_models_triton_service()
    unused_quality = get_unused_quality_models(quality=quality)
    # db_ml_models = [
    #     i
    #     for i in get_default_ml_models_service(db=db)
    #     if project_type in i.type_of_data and i.name not in unused_quality
    # ]
    db_ml_models = [
        i
        for i in get_default_constant_ml_models_service(db=db, constant_model=constant_model)
        if project_type in i.type_of_data and i.name not in unused_quality
    ]
    for ml_model in db_ml_models:
        index_model = [
            index_models.index(item)
            for item in filter(lambda n: n.get("name") == ml_model.name, index_models)
        ]
        if index_model:
            if (
                index_models[index_model[0]].get("reason")
                or index_models[index_model[0]].get("state")
            ) and index_models[index_model[0]].get("state") == "READY":
                continue

        url = f"http://{settings.TRITON_HOST}:{settings.TRITON_PORT}/v2/repository/models/{ml_model.name}/load"
        try:
            response = requests.request("POST", url)
        except requests.exceptions.ConnectionError:
            response = None


def unload_default_ml_models_by_type_service(project_type: str, db: Session) -> None:
    db_ml_models = [
        i
        for i in get_default_ml_models_service(db=db)
        if project_type in i.type_of_data
    ]
    for ml_model in db_ml_models:
        if "Aerial_HAT-L_SRx" in ml_model.name:
            continue
        url = f"http://{settings.TRITON_HOST}:{settings.TRITON_PORT}/v2/repository/models/{ml_model.name}/unload"
        try:
            response = requests.request("POST", url)
        except requests.exceptions.ConnectionError:
            response = None


def unload_default_constant_ml_models_by_type_service(
    project_type: str,
    db: Session,
    using_default_360_models: bool = False,
) -> None:
    db_ml_models = []
    for i in get_default_constant_ml_models_service(db=db):
        if project_type in i.type_of_data:
            if using_default_360_models and project_type == TypeProjectEnum.panorama_360.value:
                continue
            else:
                db_ml_models.append(i)

    for ml_model in db_ml_models:
        if "Aerial_HAT-L_SRx" in ml_model.name:
            continue
        url = f"http://{settings.TRITON_HOST}:{settings.TRITON_PORT}/v2/repository/models/{ml_model.name}/unload"
        try:
            response = requests.request("POST", url)
        except requests.exceptions.ConnectionError:
            response = None


def unload_ml_model_triton_service(
    project_type: str, name: str, db: Session, name_deeplab: Optional[str] = None
) -> Optional[Union[int, List[int]]]:
    db_projects = get_projects_by_type_service(type=project_type, db=db)
    pending_models = []
    for db_project in db_projects:
        if db_project.status == StatusProjectEnum.in_progress:
            pending_models.append(db_project.ml_model)
            pending_models.append(db_project.ml_model_deeplab)

    if name in pending_models or "Aerial_HAT-L_SRx" in name or name_deeplab in pending_models:
        return None
    url = f"http://{settings.TRITON_HOST}:{settings.TRITON_PORT}/v2/repository/models/{name}/unload"
    if name_deeplab:
        url2 = f"http://{settings.TRITON_HOST}:{settings.TRITON_PORT}/v2/repository/models/{name_deeplab}/unload"
    try:
        response = requests.request("POST", url)
        if name_deeplab:
            response2 = requests.request("POST", url2)
        unload_default_ml_models_by_type_service(project_type=project_type, db=db)
    except requests.exceptions.ConnectionError:
        return None
    if name_deeplab:
        return [response.status_code, response2.status_code]
    return response.status_code


def unload_ml_models_triton_service(
    project_type: str,
    names: List[str],
    db: Session,
    names_deeplab: Optional[List[str]] = None,
    name_qualities: Optional[str] = None
) -> Optional[List[int]]:

    db_projects = get_projects_by_ids_limit(db=db, limit=15)
    pending_models = []
    using_default_360_models = False
    for db_project in db_projects:
        if db_project.status == StatusProjectEnum.in_progress.value:
            if db_project.ml_model:
                for ml_model in db_project.ml_model:
                    pending_models.append(ml_model)
            if db_project.ml_model_deeplab:
                for ml_model_deeplab in db_project.ml_model_deeplab:
                    pending_models.append(ml_model_deeplab)
            if db_project.super_resolution == "x2":
                pending_models.append(Qualities.x2.value)
            if db_project.super_resolution == "x3":
                pending_models.append(Qualities.x3.value)
            if db_project.super_resolution == "x4":
                pending_models.append(Qualities.x4.value)
            if project_type == TypeProjectEnum.panorama_360.value:
                using_default_360_models = True
    check_yolo_model = None
    check_deeplab_model = None
    check_qualities_model = None
    if names:
        check_yolo_model = any(name in pending_models for name in names)
    if names_deeplab:
        check_deeplab_model = any(name_deeplab in pending_models for name_deeplab in names_deeplab)
    if name_qualities != Qualities.x1.value:
        check_qualities_model = name_qualities in pending_models
    urls = []
    if names and not check_yolo_model:
        for name in names:
            urls.append(f"http://{settings.TRITON_HOST}:{settings.TRITON_PORT}/v2/repository/models/{name}/unload")
    if names_deeplab and not check_deeplab_model:
        for name_deeplab in names_deeplab:
            urls.append(f"http://{settings.TRITON_HOST}:{settings.TRITON_PORT}/v2/repository/models/{name_deeplab}/unload")
    if name_qualities and not check_qualities_model:
        urls.append(f"http://{settings.TRITON_HOST}:{settings.TRITON_PORT}/v2/repository/models/{name_qualities}/unload")
    try:
        status_codes = []
        for url in urls:
            response = requests.request("POST", url)
            status_codes.append(response.status_code)
        unload_default_constant_ml_models_by_type_service(
            project_type=project_type,
            db=db,
            using_default_360_models=using_default_360_models
        )
    except requests.exceptions.ConnectionError:
        return None

    return status_codes


def unload_unused_ml_models_service(db: Session) -> None:
    project_types = [i.value for i in TypeProjectEnum if i.value != "all"]
    for project_type in project_types:
        db_projects = get_projects_by_type_service(type=project_type, db=db)
        pending_models = [
            db_project.ml_model
            for db_project in db_projects
            if db_project.status == StatusProjectEnum.in_progress
        ]
        ml_models = [
            db_project.ml_model
            for db_project in db_projects
            if db_project.status == StatusProjectEnum.completed
               or db_project.status == StatusProjectEnum.error
               or db_project.status == StatusProjectEnum.ready_to_start
        ]
        if (
            not ml_models
            or ml_models[0] in pending_models
            or "Aerial_HAT-L_SRx" in ml_models[0]
        ):
            continue
        url = f"http://{settings.TRITON_HOST}:{settings.TRITON_PORT}/v2/repository/models/{ml_models[0]}/unload"
        try:
            response = requests.request("POST", url)
        except requests.exceptions.ConnectionError:
            response = None


def get_quality_img(
    project_id: int, project_type: str, quality: str, paths: List[str]
) -> Generator:
    for path in paths:
        if quality == Qualities.x1:
            yield path
        else:
            filename = path.split("/")[-1]
            save_path = f"static/{project_id}/{project_type}/super_resolution/{quality}"
            create_dir(path=save_path)
            img_save_path = f"{save_path}/{filename}"
            with InferenceServerManager(
                url=settings.TRITON_HOST, port=settings.TRITON_PORT
            ) as inference:
                superresolution_image(
                    img_path=path,
                    img_save_path=img_save_path,
                    model_name=quality,
                    triton_client=inference,
                )
                yield img_save_path


def send_super_resolution_service(
    project_id: int, project_type: str, quality: str, paths: List[str]
) -> List[str]:
    result_paths = [
        i
        for i in get_quality_img(
            project_id=project_id,
            project_type=project_type,
            quality=quality,
            paths=paths,
        )
    ]
    return result_paths


def create_notification_service(data: Dict[str, Any]) -> None:
    if settings.NOTIFICATION_ON:
        # verify=False when self signed certificate
        requests.post(f"{BACKEND_HOST}{API_PATH}", json={"data": data}, verify=False)


def get_aerial_img(
    path: str,
    save_path: str,
    save_image_flag: bool,
    save_json_flag: bool,
    ml_model: List[str],
    names_models_deeplab: List[str],
    tile_size_yolo: List[int],
    tile_size_deeplab: List[int],
    scale_factor_yolo: List[float],
    scale_factor_deeplab: List[float],
    classes_yolo_model: List[str],
    class_names_deeplab: List[str],
    view_yolo: list[str],
    view_deeplab: list[str],
) -> str:
    filename = path.split("/")[-1]
    if filename.endswith(".tif") or filename.endswith(".png"):
        filename = filename.rsplit(".", 1)[0] + ".jpg"
    folder = filename.split(".")[0]
    create_dir(path=save_path)
    create_dir(path=f"{save_path}/{folder}")
    with InferenceServerManager(
        url=settings.TRITON_HOST, port=settings.TRITON_PORT
    ) as inference:
        model_info_list = get_model_info_list(
            ml_model=ml_model,
            names_models_deeplab=names_models_deeplab,
            tile_size_yolo=tile_size_yolo,
            tile_size_deeplab=tile_size_deeplab,
            scale_factor_yolo=scale_factor_yolo,
            scale_factor_deeplab=scale_factor_deeplab,
            classes_yolo_model=classes_yolo_model,
            class_names_deeplab=class_names_deeplab,
            view_yolo=view_yolo,
            view_deeplab=view_deeplab
        )

        get_aerial_satellite_image(
            triton_client=inference,
            img_path=path,
            save_dir=f"{save_path}/{folder}",
            save_image_flag=save_image_flag,
            save_json_flag=save_json_flag,
            model_info_list=model_info_list
        )

    return f"{save_path}/{folder}/{filename}"


def send_aerial_service(
    project_id: int,
    project_type: str,
    paths: List[str],
    save_image_flag: bool,
    save_json_flag: bool,
    ml_model: List[str],
    names_models_deeplab: List[str],
    tile_size_yolo: List[int],
    tile_size_deeplab: List[int],
    scale_factor_yolo: List[float],
    scale_factor_deeplab: List[float],
    classes_yolo_model: List[str],
    class_names_deeplab: List[str],
    view_yolo: list[str],
    view_deeplab: list[str]
) -> List[str]:
    save_path = None
    if project_type == TypeProjectEnum.aerial_images:
        save_path = f"static/{project_id}/{project_type}/detection_result"
    elif project_type == TypeProjectEnum.satellite_images:
        save_path = f"static/{project_id}/{project_type}/satellite_result"
    else:
        ml_model = None
        names_models_deeplab = None

    delete_dir(path=save_path)
    result = []
    for path in paths:
        r = get_aerial_img(
            path=path,
            save_path=save_path,
            save_image_flag=save_image_flag,
            save_json_flag=save_json_flag,
            ml_model=ml_model,
            names_models_deeplab=names_models_deeplab,
            tile_size_yolo=tile_size_yolo,
            tile_size_deeplab=tile_size_deeplab,
            scale_factor_yolo=scale_factor_yolo,
            scale_factor_deeplab=scale_factor_deeplab,
            classes_yolo_model=classes_yolo_model,
            class_names_deeplab=class_names_deeplab,
            view_yolo=view_yolo,
            view_deeplab=view_deeplab,
        )
        result.append(r)
    return result


def send_360_service(
    project_id: int,
    project_type: str,
    paths: List[str],
    ml_model: List[str],
    names_models_deeplab: List[str],
    tile_size_yolo: List[int],
    tile_size_deeplab: List[int],
    scale_factor_yolo: List[float],
    scale_factor_deeplab: List[float],
    classes_yolo_model: List[str],
    class_names_deeplab: List[str],
    view_yolo: list[str],
    view_deeplab: list[str],
) -> Result360Schemas:
    save_path = f"static/{project_id}/{project_type}/360_result/{project_id}"
    delete_dir(path=save_path)

    image_list = []
    for path in paths:
        r = get_360_image(
            path=path,
            save_path=save_path,
            ml_model=ml_model,
            names_models_deeplab=names_models_deeplab,
            tile_size_yolo=tile_size_yolo,
            tile_size_deeplab=tile_size_deeplab,
            scale_factor_yolo=scale_factor_yolo,
            scale_factor_deeplab=scale_factor_deeplab,
            classes_yolo_model=classes_yolo_model,
            class_names_deeplab=class_names_deeplab,
            view_yolo=view_yolo,
            view_deeplab=view_deeplab,
        )
        image_list.append(r)

    pcd_path = get_point_cloud(
        img_paths=paths,
        save_pcd_path=save_path,
        ml_model=ml_model,
        names_models_deeplab=names_models_deeplab,
        tile_size_yolo=tile_size_yolo,
        tile_size_deeplab=tile_size_deeplab,
        scale_factor_yolo=scale_factor_yolo,
        scale_factor_deeplab=scale_factor_deeplab,
        classes_yolo_model=classes_yolo_model,
        class_names_deeplab=class_names_deeplab,
        view_yolo=view_yolo,
        view_deeplab=view_deeplab,
    )
    return Result360Schemas(image_list=image_list, pcd_path=pcd_path)


def get_360_image(
    path: str,
    save_path: str,
    ml_model: List[str],
    names_models_deeplab: List[str],
    tile_size_yolo: List[int],
    tile_size_deeplab: List[int],
    scale_factor_yolo: List[float],
    scale_factor_deeplab: List[float],
    classes_yolo_model: List[str],
    class_names_deeplab: List[str],
    view_yolo: list[str],
    view_deeplab: list[str]
) -> str:
    filename = path.split("/")[-1]
    folder = filename.split(".")[0]
    create_dir(path=save_path)
    create_dir(path=f"{save_path}/{folder}")

    model_info_list = get_model_info_list(
        ml_model=ml_model,
        names_models_deeplab=names_models_deeplab,
        tile_size_yolo=tile_size_yolo,
        tile_size_deeplab=tile_size_deeplab,
        scale_factor_yolo=scale_factor_yolo,
        scale_factor_deeplab=scale_factor_deeplab,
        classes_yolo_model=classes_yolo_model,
        class_names_deeplab=class_names_deeplab,
        view_yolo=view_yolo,
        view_deeplab=view_deeplab,
    )
    with InferenceServerManager(
        url=settings.TRITON_HOST, port=settings.TRITON_PORT
    ) as inference:
        get_360_images(
            triton_client=inference,
            model_info_list=model_info_list,
            img_path=path,
            res_save_path=f"{save_path}/{folder}",
        )
    return f"{save_path}/{folder}/{filename}"


def get_point_cloud(
    img_paths: List[str],
    save_pcd_path: str,
    ml_model: List[str],
    names_models_deeplab: List[str],
    tile_size_yolo: List[int],
    tile_size_deeplab: List[int],
    scale_factor_yolo: List[float],
    scale_factor_deeplab: List[float],
    classes_yolo_model: List[str],
    class_names_deeplab: List[str],
    view_yolo: list[str],
    view_deeplab: list[str],
) -> str:
    with InferenceServerManager(
        url=settings.TRITON_HOST, port=settings.TRITON_PORT
    ) as inference:
        model_info_list = get_model_info_list(
            ml_model=ml_model,
            names_models_deeplab=names_models_deeplab,
            tile_size_yolo=tile_size_yolo,
            tile_size_deeplab=tile_size_deeplab,
            scale_factor_yolo=scale_factor_yolo,
            scale_factor_deeplab=scale_factor_deeplab,
            classes_yolo_model=classes_yolo_model,
            class_names_deeplab=class_names_deeplab,
            view_yolo=view_yolo,
            view_deeplab=view_deeplab,
        )

        all_classes = get_model_classes_list(
            classes_yolo_model=classes_yolo_model,
            class_names_deeplab=class_names_deeplab
        )
        cfg = Config()
        cfg.classes_pcd = all_classes

        scene_nums, img_nums = get_scene_img_nums_from_files_services(img_paths=img_paths)
        cfg.template_trajectory_point = set_random_scene_img_nums(
            scene_nums=scene_nums, img_nums=img_nums
        )
        if bool(glob.glob(os.path.join(os.path.dirname(img_paths[0]), "*.las"))):
            save_path = f"{save_pcd_path}/result.pcd"
            get_pcd_localization_ocr(
                image_paths=img_paths,
                model_info_list=model_info_list,
                triton_client=inference,
                save_pcd_path=save_path,
                save_shp_path=save_pcd_path,
                cfg=cfg
            )
        else:
            save_path = None
            get_pcd_localization_without_las(
                image_paths=img_paths,
                model_info_list=model_info_list,
                triton_client=inference,
                save_shp_path=save_pcd_path,
                cfg=cfg
            )
    return save_path


def get_model_info_list(
    ml_model: List[str],
    names_models_deeplab: List[str],
    tile_size_yolo: List[int],
    tile_size_deeplab: List[int],
    scale_factor_yolo: List[float],
    scale_factor_deeplab: List[float],
    classes_yolo_model: List[str],
    class_names_deeplab: List[str],
    view_yolo: list[str],
    view_deeplab: list[str],
) -> List[ModelInfo]:
    all_yolo_models_info = [ModelInfo(
        model_name=ml_model[i],
        model_type=view_yolo[i],
        class_names=classes_yolo_model[i],
        tile_size=tile_size_yolo[i],
        scale_factor=scale_factor_yolo[i],
    ) for i in range(len(ml_model))
    ]
    all_deeplab_models_info = [ModelInfo(
        model_name=names_models_deeplab[i],
        model_type=view_deeplab[i],
        class_names=class_names_deeplab[i],
        tile_size=tile_size_deeplab[i],
        scale_factor=scale_factor_deeplab[i],
    ) for i in range(len(names_models_deeplab))
    ]
    model_info_list = all_yolo_models_info + all_deeplab_models_info
    return model_info_list


def get_model_classes_list(
    classes_yolo_model: List[str],
    class_names_deeplab: List[str],
) -> List[str]:
    all_uniq_yolo_classes = list(set(
        item for i in range(len(classes_yolo_model)) for item in classes_yolo_model[i]
    ))
    all_uniq_deeplab_classes = list(set(
        item for i in range(len(class_names_deeplab)) for item in class_names_deeplab[i]
    ))
    return all_uniq_yolo_classes + all_uniq_deeplab_classes


def compare_service(
    paths_images: List[str], id: List[int], project_type: str, classes_list: List[str]
) -> Tuple[List[List[Tuple[Any, Any]]], List[str], List[str]]:
    list_path_json = []
    list_path_twf = []
    for number in range(2):
        path_dir = os.path.dirname(paths_images[number][0])
        path_dir_merge = os.path.dirname(path_dir)
        for file in os.listdir(path_dir_merge):
            if file.endswith(".json") and not file.endswith("_tfw.json"):
                list_path_json.append(os.path.join(path_dir_merge, file))
            if file.endswith("_tfw.json"):
                list_path_twf.append(os.path.join(path_dir_merge, file))

    name = f"projects_ids_{id[0]}_and_{id[1]}"
    save_path = f"static/compare_result/{project_type}/{name}"
    delete_dir(path=save_path)
    create_dir(path=save_path)
    if len(list_path_json) != 2:
        raise NotFoundJson

    result_compare = ()
    if (
        project_type == TypeProjectEnum.aerial_images
        or project_type == TypeProjectEnum.satellite_images
    ):
        if len(list_path_twf) != 2:
            raise NotFoundTfw
        result_compare = change_detection(
            save_to=save_path,
            name_zip=name,
            path_to_json_project_old=list_path_json[0],
            path_to_json_project_new=list_path_json[1],
            path_to_geo_file_project_old=list_path_twf[0],
            path_to_geo_file_project_new=list_path_twf[1],
            classes_list=classes_list,
        )

    elif project_type == TypeProjectEnum.panorama_360:
        result_compare = change_detection_360(
            save_to=save_path,
            name_zip=name,
            path_to_json_project_old=list_path_json[0],
            path_to_json_project_new=list_path_json[1],
            classes_list=classes_list,
        )

    return result_compare


def get_object_classes_service(path: str) -> List[str]:
    if not os.path.exists(path):
        raise EmptyNextcloudFolderException

    dataset_categories = []
    for directory in glob.glob(f"{path}/*/annotations/*.json"):
        with open(directory) as f:
            data = json.load(f)
            if data.get("categories"):
                categories = [category["name"] for category in data["categories"]]
                dataset_categories.append(categories)

    if len(dataset_categories) == 0:
        return dataset_categories
    elif len(dataset_categories) == 1:
        repeated_arrays = dataset_categories
    else:
        array_counts = Counter(map(tuple, dataset_categories))
        repeated_arrays = [
            list(array) for array, count in array_counts.items() if count > 1
        ]
        if len(repeated_arrays) == 0:
            return max(
                (x) for x in [list(array) for array, count in array_counts.items()]
            )
    return repeated_arrays[0]


def add_ml_model_task_id_service(id: int, task_id: str, db: Session) -> MLModelSchemas:
    db_ml_model = db.query(ML).filter(ML.id == id).first()
    db_ml_model.task_id = task_id
    db.commit()
    db.refresh(db_ml_model)
    return MLModelSchemas(
        id=db_ml_model.id,
        name=db_ml_model.name,
        type_of_data=db_ml_model.type_of_data,
        type_of_objects=db_ml_model.type_of_objects,
        default_model=db_ml_model.default_model,
        task_id=db_ml_model.task_id,
        task_result=db_ml_model.task_result,
        status=db_ml_model.status,
        created_at=db_ml_model.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        mlflow_url=db_ml_model.ml_flow_url,
        created_by=db_ml_model.created_by,
    )


def add_ml_model_task_result_service(
    task_id: str, task_result: Dict[str, Any], db: Session
) -> MLModelSchemas:
    db_ml_model = db.query(ML).filter(ML.task_id == task_id).first()
    db_ml_model.task_result = task_result
    db.commit()
    db.refresh(db_ml_model)
    return MLModelSchemas(
        id=db_ml_model.id,
        name=db_ml_model.name,
        type_of_data=db_ml_model.type_of_data,
        type_of_objects=db_ml_model.type_of_objects,
        default_model=db_ml_model.default_model,
        task_id=db_ml_model.task_id,
        task_result=db_ml_model.task_result,
        status=db_ml_model.status,
        created_at=db_ml_model.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        mlflow_url=db_ml_model.ml_flow_url,
        created_by=db_ml_model.created_by,
    )


def add_ml_model_task_result_by_id_service(
    id: int, task_result: Dict[str, Any], db: Session
) -> MLModelSchemas:
    db_ml_model = db.query(ML).filter(ML.id == id).first()
    db_ml_model.task_result = task_result
    db.commit()
    db.refresh(db_ml_model)
    return MLModelSchemas(
        id=db_ml_model.id,
        name=db_ml_model.name,
        type_of_data=db_ml_model.type_of_data,
        type_of_objects=db_ml_model.type_of_objects,
        default_model=db_ml_model.default_model,
        task_id=db_ml_model.task_id,
        task_result=db_ml_model.task_result,
        status=db_ml_model.status,
        created_at=db_ml_model.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        mlflow_url=db_ml_model.ml_flow_url,
        created_by=db_ml_model.created_by,
    )


def add_ml_model_experiment_name_service(id: int, experiment_name: str, db: Session):
    db_ml_model = db.query(ML).filter(ML.id == id).first()
    db_ml_model.experiment_name = experiment_name
    db.commit()
    db.refresh(db_ml_model)


def add_ml_model_view_service(id: int, type_model: str, db: Session):
    db_ml_model = db.query(ML).filter(ML.id == id).first()
    db_ml_model.view = type_model
    db.commit()
    db.refresh(db_ml_model)


def add_ml_model_scale_factor_tile_size_service(
    id: int, scale_factor: float, tile_size: int, db: Session
):
    db_ml_model = db.query(ML).filter(ML.id == id).first()
    db_ml_model.scale_factor = scale_factor
    db_ml_model.tile_size = tile_size
    db.commit()
    db.refresh(db_ml_model)


def change_status_ml_model_service(id: int, status: str, db: Session) -> MLModelSchemas:
    db_ml_model = db.query(ML).filter(ML.id == id).first()
    db_ml_model.status = status
    db.commit()
    db.refresh(db_ml_model)
    return MLModelSchemas(
        id=db_ml_model.id,
        name=db_ml_model.name,
        type_of_data=db_ml_model.type_of_data,
        type_of_objects=db_ml_model.type_of_objects,
        default_model=db_ml_model.default_model,
        task_id=db_ml_model.task_id,
        task_result=db_ml_model.task_result,
        status=db_ml_model.status,
        created_at=db_ml_model.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        mlflow_url=db_ml_model.ml_flow_url,
        created_by=db_ml_model.created_by,
    )


def get_ml_model_by_task_id_service(task_id: str, db: Session) -> MLModelSchemas:
    db_ml_model = db.query(ML).filter(ML.task_id == task_id).first()
    return MLModelSchemas(
        id=db_ml_model.id,
        name=db_ml_model.name,
        type_of_data=db_ml_model.type_of_data,
        type_of_objects=db_ml_model.type_of_objects,
        default_model=db_ml_model.default_model,
        task_id=db_ml_model.task_id,
        task_result=db_ml_model.task_result,
        status=db_ml_model.status,
        created_at=db_ml_model.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        mlflow_url=db_ml_model.ml_flow_url,
        created_by=db_ml_model.created_by,
    )


def change_ml_classes_by_id_service(
    id: int, classes: List[str], db: Session
) -> MLModelSchemas:
    db_ml_model = db.query(ML).filter(ML.id == id).first()
    db_ml_model.type_of_objects = classes
    db.commit()
    db.refresh(db_ml_model)
    return MLModelSchemas(
        id=db_ml_model.id,
        name=db_ml_model.name,
        type_of_data=db_ml_model.type_of_data,
        type_of_objects=db_ml_model.type_of_objects,
        default_model=db_ml_model.default_model,
        task_id=db_ml_model.task_id,
        task_result=db_ml_model.task_result,
        status=db_ml_model.status,
        created_at=db_ml_model.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        mlflow_url=db_ml_model.ml_flow_url,
        created_by=db_ml_model.created_by,
    )


def launch_task_service(
    url: str, data: Dict[str, Any] = {}, json: Dict[str, Any] = {}
) -> Optional[Dict[str, str]]:
    response = requests.post(url, data=data, json=json)
    if response.status_code == 200:
        task_id = response.json()
        return task_id
    return None


def check_task_status_service(url: str) -> Optional[str]:
    response = requests.get(url)
    if response.status_code == 200:
        status = response.json().get("task_status")
        return status
    return None


def get_result_task_service(url: str) -> Optional[Dict[str, Any]]:
    response = requests.get(url)
    if response.status_code == 200:
        result = response.json().get("task_result")
        return result
    return None


def add_ml_flow_url_service(id: int, experiment_value: str, run_id: str, db: Session):
    if settings.MLFLOW_PROD:
        url_mlflow = settings.MLFLOW_PROD_URL
    else:
        url_mlflow = f"{settings.ML_SERVER_URL}:{settings.ML_MLFLOW_PORT}/"
    url = f"{url_mlflow}#/experiments/{run_id}/runs/{experiment_value}"
    db_ml_model = db.query(ML).filter(ML.id == id).first()
    db_ml_model.ml_flow_url = url
    db.commit()
    db.refresh(db_ml_model)


def get_dataset_nextcloud_service(id: str, path: str) -> Union[None, Exception]:
    os.makedirs(f"static/models/{id}", mode=0o777, exist_ok=True)

    copy_file_from_dir(
        filename=f"{path}.zip",
        origin="static/nextcloud/Admin123/files",
        target=f"static/models/{id}",
    )

    shutil.unpack_archive(f"static/models/{id}/{path}.zip", f"static/models/{id}/")

    os.remove(f"static/nextcloud/Admin123/files/{path}.zip")
    os.remove(f"static/models/{id}/{path}.zip")


def delete_ml_model_nextcloud_service(path: str) -> Union[None, Exception]:
    url = f"{settings.URL_NEXTCLOUD}/index.php/apps/files/api/v1/file={path}"
    response = requests.delete(
        url, auth=(settings.LOGIN_NEXTCLOUD, settings.PASSWORD_NEXTCLOUD)
    )
    if response.status_code != 200:
        raise NextcloudIsNotResponding


def load_ml_model_to_triton_service(id: int, experiment_name: str) -> str:
    path = f"static/models/{id}/static/{id}/{experiment_name}"

    models = glob.glob(f"{path}/yolov8*")
    if not models:
        return load_deeplab_model_service(path=path)
    models.sort()
    model = models[-1]

    copy_dir(
        origin=model,
        target=f"static/models/{model.split('/')[-1]}",
        dirs_exist_ok=True,
    )
    delete_dir(f"static/models/{id}")
    return model.split("/")[-1]


def load_deeplab_model_service(path: str) -> str:
    models = glob.glob(f"{path}/deeplabv3*")
    models.sort()
    model = models[-1]

    copy_dir(
        origin=model,
        target=f"static/models/{model.split('/')[-1]}",
        dirs_exist_ok=True,
    )
    delete_dir(f"static/models/{id}")
    return model.split("/")[-1]


def set_random_scene_img_nums(scene_nums: int, img_nums: int) -> str:
    return f'pano_{{0:0{scene_nums}d}}_{{1:0{img_nums}d}}'
