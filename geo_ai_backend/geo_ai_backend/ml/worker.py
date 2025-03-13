import os
import time
import json
from typing import Any, Dict, List, Union
from geo_ai_backend.config import settings
from geo_ai_backend.arcgis.utils import merge_zips
from geo_ai_backend.database import get_db_iter
from geo_ai_backend.ml.exceptions import (
    InvalidDirectoryStructure,
    PathNotFoundException,
    NotTrainingTypeModel,
)
from geo_ai_backend.ml.schemas import (
    CropSizeEnum,
    ImageSizeEnum,
    StatusModelEnum,
    TypeMlModelTrainingEnum,
    CropSizeEnumDeeplab,
    ImageSizeEnumDeeplab,
    ScaleFactorYoloEnum,
    ScaleFactorDeeplabEnum, TypeMLModelEnum,
)
from geo_ai_backend.history.schemas import CreateActionHistorySchemas, CreateErrorHistorySchemas
from geo_ai_backend.history.service import create_action_history_service, create_error_history_service
from geo_ai_backend.ml.ml_models.aerial_satellite.inference.compare.merge_zips import (
    merge_files,
)
from geo_ai_backend.ml.schemas import Qualities
from geo_ai_backend.ml.service import (
    add_ml_flow_url_service,
    add_ml_model_experiment_name_service,
    add_ml_model_task_result_by_id_service,
    change_status_ml_model_service,
    create_notification_service,
    get_object_classes_service,
    get_result_task_service,
    load_ml_model_to_triton_service,
    send_super_resolution_service,
    send_aerial_service,
    send_360_service,
    launch_task_service,
    check_task_status_service,
    get_dataset_nextcloud_service,
    update_link_ml_model_service,
    add_ml_model_view_service,
    unload_ml_models_triton_service,
    add_ml_model_scale_factor_tile_size_service,
)
from geo_ai_backend.ml.utils import create_dir
from geo_ai_backend.project.schemas import StatusProjectEnum
from geo_ai_backend.project.service import (
    change_status_project_service,
    get_project_by_id_service,
    add_task_result,
    get_paths_superresolution_service,
    add_project_classes_sr_service,
)
from geo_ai_backend.utils import (
    change_resolution_jpg,
    delete_dir,
    delete_file,
    copy_dir,
    copy_file_from_dir,
)
from geo_ai_backend.worker import celery
from geo_ai_backend.arcgis.service import gis_service
import traceback


@celery.task(name="create_superresolution_detection_task")
def create_superresolution_detection_task(
    task_type: int,
    params: Dict[str, Any],
) -> Dict[str, Union[str, List[str]]]:
    db = get_db_iter()
    db_project = get_project_by_id_service(id=params["project_id"], db=db)
    status = StatusProjectEnum.completed
    try:
        classes = list(set(
            name for part in (params["ml_classes"] + params["deeplab_ml_classes"])
            for name in part
        ))

        add_project_classes_sr_service(
            id=db_project.id,
            classes=classes,
            super_resolution={v.value: v.name for v in Qualities}.get(params["quality"]),
            db=db
        )
        save_path_prepare = f'static/{task_type}/{params["project_type"]}/prepared'
        paths_tif_jpg = get_paths_superresolution_service(
            save_path_prepare=save_path_prepare,
            path_tif=params["paths"],
        )

        img_save_path = send_super_resolution_service(
            project_id=task_type,
            project_type=params["project_type"],
            quality=params["quality"],
            paths=paths_tif_jpg,
        )
        delete_dir(path=save_path_prepare)
        create_notification_service(data=params)

        path_detection = f"static/{params['project_id']}/{params['project_type']}/detection_result"
        create_dir(path=path_detection)
        copy_dir(
            origin=path_detection,
            target=f"static/nextcloud/Admin123/files/{params['link']}/detection_result",
        )
        if params["quality"] != Qualities.x1:
            copy_dir(
                origin=f"static/{params['project_id']}/{params['project_type']}/super_resolution/{params['quality']}",
                target=f"static/nextcloud/Admin123/files/{params['link']}/detection_result/super_resolution/{params['quality']}",
            )
        change_status_project_service(
            id=db_project.id,
            status=StatusProjectEnum.completed,
            db=db,
        )
    except Exception as e:
        status = StatusProjectEnum.error
        img_save_path = None
        print(f"Error: {e}")
        traceback.print_exc()
        change_status_project_service(
            id=db_project.id,
            status=StatusProjectEnum.error,
            db=db,
            description=e.__str__(),
            error_code="SUPER_RESOLUTION_FATAL_ERROR",
        )
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Super resolution without detection failed with an error",
                username=params["username"],
                project=db_project.name,
                description=e.__str__(),
                code="SUPER_RESOLUTION_FATAL_ERROR",
                project_id=db_project.id,
                project_type="PROJECT",
            ),
            owner_id=params["owner_id"],
            db=db,
        )

    change_status_project_service(
        id=db_project.id,
        status=status,
        db=db,
    )
    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action=f"End of super resolution without detection {db_project.type}",
            username=params["username"],
            project=db_project.name,
            description="Status change from 'In progress' to 'Completed'",
            project_id=db_project.id,
            project_type="PROJECT",
        ),
        owner_id=params["owner_id"],
        db=db,
    )

    if not img_save_path:
        add_task_result(id=db_project.id, task_result=None, db=db)
        raise Exception

    task_result = {
        "path_images": img_save_path,
        "layer_id": "",
        "project_id": params["project_id"],
    }

    add_task_result(id=db_project.id, task_result=task_result, db=db)

    unload_ml_models_triton_service(
        project_type=db_project.type,
        names=db_project.ml_model,
        names_deeplab=db_project.ml_model_deeplab,
        name_qualities=params["quality"],
        db=db
    )
    delete_dir(path=f"static/{params['project_id']}/{params['project_type']}/images")
    delete_dir(path=f"static/{params['project_id']}/{params['project_type']}/tif")

    return task_result


@celery.task(name="create_detection_task")
def create_detection_task(
    task_type: int,
    params: Dict[str, Any],
) -> Dict[str, Union[str, List[str]]]:
    db = get_db_iter()
    db_project = get_project_by_id_service(id=params["project_id"], db=db)
    try:
        classes = list(set(
            name for part in (params["ml_classes"] + params["deeplab_ml_classes"])
            for name in part
        ))

        add_project_classes_sr_service(
            id=db_project.id,
            classes=classes,
            super_resolution={v.value: v.name for v in Qualities}.get(params["quality"]),
            db=db
        )

        img_save_path_aerial = send_aerial_service(
            project_id=task_type,
            project_type=params["project_type"],
            paths=params["paths"],
            save_image_flag=params["save_image_flag"],
            save_json_flag=params["save_json_flag"],
            ml_model=params["ml_model"],
            names_models_deeplab=params["deeplab_ml_model"],
            tile_size_yolo=params["tile_size_yolo"],
            tile_size_deeplab=params["tile_size_deeplab"],
            scale_factor_yolo=params["scale_factor_yolo"],
            scale_factor_deeplab=params["scale_factor_deeplab"],
            classes_yolo_model=params["ml_classes"],
            class_names_deeplab=params["deeplab_ml_classes"],
            view_yolo=params["view_yolo"],
            view_deeplab=params["view_deeplab"],
        )

        save_path_prepare = f'static/{task_type}/{params["project_type"]}/prepared'
        paths_tif_jpg = get_paths_superresolution_service(
            save_path_prepare=save_path_prepare,
            path_tif=params["paths"],
        )

        img_save_path = send_super_resolution_service(
            project_id=task_type,
            project_type=params["project_type"],
            quality=params["quality"],
            paths=paths_tif_jpg,
        )
        delete_dir(path=save_path_prepare)
        create_notification_service(data=params)

        list_paths_dirs = [os.path.dirname(p) for p in img_save_path_aerial]
        path_zip = os.path.dirname(list_paths_dirs[0])

        path = merge_files(
            list_paths_dirs=list_paths_dirs,
            save_to=path_zip,
            res_name=f"detection_result_project_id_{params['project_id']}",
            classes_list=classes
        )

        layer_id = gis_service.upload_shape_layer(shape_zip_path=path)
        delete_file(path)
        copy_dir(
            origin=f"static/{params['project_id']}/{params['project_type']}/detection_result",
            target=f"static/nextcloud/Admin123/files/{params['link']}/detection_result",
        )
        if params["quality"] != Qualities.x1:
            copy_file_from_dir(
                filename=os.path.basename(img_save_path_aerial[0].replace(".jpg", ".prj")),
                origin=os.path.dirname(img_save_path_aerial[0]),
                target=f"static/{params['project_id']}/{params['project_type']}/super_resolution/{params['quality']}"
            )
            copy_dir(
                origin=f"static/{params['project_id']}/{params['project_type']}/super_resolution/{params['quality']}",
                target=f"static/nextcloud/Admin123/files/{params['link']}/detection_result/super_resolution/{params['quality']}",
            )
        for i in img_save_path_aerial:
            change_resolution_jpg(path=i, save_path=i)

        change_status_project_service(
            id=db_project.id,
            status=StatusProjectEnum.completed,
            db=db,
        )
    except Exception as e:
        img_save_path_aerial = None
        layer_id = None
        print(f"Error: {e}")
        traceback.print_exc()
        change_status_project_service(
            id=db_project.id,
            status=StatusProjectEnum.error,
            db=db,
            description=e.__str__(),
            error_code="CREATE_DETECTION_TASK_FAILED",
        )
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Detection failed with an error",
                username=params["username"],
                project=db_project.name,
                description=e.__str__(),
                code="CREATE_DETECTION_TASK_FAILED",
                project_id=db_project.id,
                project_type="PROJECT",
            ),
            owner_id=params["owner_id"],
            db=db,
        )

    if not img_save_path_aerial:
        add_task_result(id=db_project.id, task_result=None, db=db)
        raise Exception

    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action=f"End of detection {db_project.type}",
            username=params["username"],
            project=db_project.name,
            description="Status change from 'In progress' to 'Completed'",
            project_id=db_project.id,
            project_type="PROJECT",
        ),
        owner_id=params["owner_id"],
        db=db,
    )

    task_result = {
        "path_images": img_save_path_aerial,
        "layer_id": layer_id,
        "project_id": params["project_id"],
    }

    add_task_result(id=db_project.id, task_result=task_result, db=db)

    unload_ml_models_triton_service(
        project_type=db_project.type,
        names=db_project.ml_model,
        names_deeplab=db_project.ml_model_deeplab,
        name_qualities=params["quality"],
        db=db
    )
    delete_dir(path=f"static/{params['project_id']}/{params['project_type']}/images")
    delete_dir(path=f"static/{params['project_id']}/{params['project_type']}/tif")

    return task_result


@celery.task(name="create_satellite_task")
def create_satellite_task(
    task_type: int,
    params: Dict[str, Any],
) -> Dict[str, Union[str, List[str]]]:
    db = get_db_iter()
    db_project = get_project_by_id_service(id=params["project_id"], db=db)
    try:
        classes = list(set(
            name for part in (params["ml_classes"] + params["deeplab_ml_classes"])
            for name in part
        ))

        add_project_classes_sr_service(
            id=db_project.id,
            classes=classes,
            super_resolution={v.value: v.name for v in Qualities}.get(params["quality"]),
            db=db
        )

        img_save_path_aerial = send_aerial_service(
            project_id=task_type,
            project_type=params["project_type"],
            paths=params["paths"],
            save_image_flag=params["save_image_flag"],
            save_json_flag=params["save_json_flag"],
            ml_model=params["ml_model"],
            names_models_deeplab=params["deeplab_ml_model"],
            tile_size_yolo=params["tile_size_yolo"],
            tile_size_deeplab=params["tile_size_deeplab"],
            scale_factor_yolo=params["scale_factor_yolo"],
            scale_factor_deeplab=params["scale_factor_deeplab"],
            classes_yolo_model=params["ml_classes"],
            class_names_deeplab=params["deeplab_ml_classes"],
            view_yolo=params["view_yolo"],
            view_deeplab=params["view_deeplab"],
        )
        save_path_prepare = f'static/{task_type}/{params["project_type"]}/prepared'
        paths_tif_jpg = get_paths_superresolution_service(
            save_path_prepare=save_path_prepare,
            path_tif=params["paths"],
        )

        img_save_path = send_super_resolution_service(
            project_id=task_type,
            project_type=params["project_type"],
            quality=params["quality"],
            paths=paths_tif_jpg,
        )

        delete_dir(path=save_path_prepare)
        create_notification_service(data=params)

        list_paths_dirs = [os.path.dirname(p) for p in img_save_path_aerial]

        path_zip = os.path.dirname(list_paths_dirs[0])

        path = merge_files(
            list_paths_dirs=list_paths_dirs,
            save_to=path_zip,
            res_name=f"satellite_result_project_id_{params['project_id']}",
            classes_list=classes
        )

        layer_id = gis_service.upload_shape_layer(shape_zip_path=path)
        delete_file(path)
        copy_dir(
            origin=f"static/{params['project_id']}/{params['project_type']}/satellite_result",
            target=f"static/nextcloud/Admin123/files/{params['link']}/satellite_result",
        )
        if params["quality"] != Qualities.x1:
            copy_file_from_dir(
                filename=os.path.basename(img_save_path_aerial[0].replace(".jpg", ".prj")),
                origin=os.path.dirname(img_save_path_aerial[0]),
                target=f"static/{params['project_id']}/{params['project_type']}/super_resolution/{params['quality']}"
            )
            copy_dir(
                origin=f"static/{params['project_id']}/{params['project_type']}/super_resolution/{params['quality']}",
                target=f"static/nextcloud/Admin123/files/{params['link']}/satellite_result/super_resolution/{params['quality']}",
            )
        for i in img_save_path_aerial:
            change_resolution_jpg(path=i, save_path=i)

        change_status_project_service(
            id=db_project.id,
            status=StatusProjectEnum.completed,
            db=db,
        )
    except Exception as e:
        img_save_path_aerial = None
        layer_id = None
        print(f"Error: {e}")
        change_status_project_service(
            id=db_project.id,
            status=StatusProjectEnum.error,
            db=db,
            description=e.__str__(),
            error_code="CREATE_SATELLITE_TASK_FAILED",
        )
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Satellite failed with an error",
                username=params["username"],
                project=db_project.name,
                description=e.__str__(),
                code="CREATE_SATELLITE_TASK_FAILED",
                project_id=db_project.id,
                project_type="PROJECT",
            ),
            owner_id=params["owner_id"],
            db=db,
        )
        traceback.print_exc()

    if not img_save_path_aerial:
        add_task_result(id=db_project.id, task_result=None, db=db)
        raise Exception

    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action=f"End of satellite {db_project.type}",
            username=params["username"],
            project=db_project.name,
            description="Status change from 'In progress' to 'Completed'",
            project_id=db_project.id,
            project_type="PROJECT",
        ),
        owner_id=params["owner_id"],
        db=db,
    )

    task_result = {
        "path_images": img_save_path_aerial,
        "layer_id": layer_id,
        "project_id": params["project_id"],
    }

    add_task_result(id=db_project.id, task_result=task_result, db=db)

    unload_ml_models_triton_service(
        project_type=db_project.type,
        names=db_project.ml_model,
        names_deeplab=db_project.ml_model_deeplab,
        name_qualities=params["quality"],
        db=db
    )
    delete_dir(path=f"static/{params['project_id']}/{params['project_type']}/images")
    delete_dir(path=f"static/{params['project_id']}/{params['project_type']}/tif")

    return task_result


@celery.task(name="create_superresolution_satellite_task")
def create_superresolution_satellite_task(
    task_type: int,
    params: Dict[str, Any],
) -> Dict[str, Union[str, List[str]]]:
    db = get_db_iter()
    db_project = get_project_by_id_service(id=params["project_id"], db=db)
    status = StatusProjectEnum.completed
    try:
        classes = list(set(
            name for part in (params["ml_classes"] + params["deeplab_ml_classes"])
            for name in part
        ))

        add_project_classes_sr_service(
            id=db_project.id,
            classes=classes,
            super_resolution={v.value: v.name for v in Qualities}.get(params["quality"]),
            db=db
        )

        save_path_prepare = f'static/{task_type}/{params["project_type"]}/prepared'
        paths_tif_jpg = get_paths_superresolution_service(
            save_path_prepare=save_path_prepare,
            path_tif=params["paths"],
        )

        img_save_path = send_super_resolution_service(
            project_id=task_type,
            project_type=params["project_type"],
            quality=params["quality"],
            paths=paths_tif_jpg,
        )

        delete_dir(path=save_path_prepare)
        create_notification_service(data=params)

        path_satellite = f"static/{params['project_id']}/{params['project_type']}/satellite_result"
        create_dir(path=path_satellite)
        copy_dir(
            origin=path_satellite,
            target=f"static/nextcloud/Admin123/files/{params['link']}/satellite_result",
        )
        if params["quality"] != Qualities.x1:
            copy_dir(
                origin=f"static/{params['project_id']}/{params['project_type']}/super_resolution/{params['quality']}",
                target=f"static/nextcloud/Admin123/files/{params['link']}/satellite_result/super_resolution/{params['quality']}",
            )
    except Exception as e:
        status = StatusProjectEnum.error
        img_save_path = None
        print(f"Error: {e}")
        change_status_project_service(
            id=db_project.id,
            status=StatusProjectEnum.error,
            db=db,
            description=e.__str__(),
            error_code="SUPER_RESOLUTION_FATAL_ERROR",
        )
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Super resolution without satellite failed with an error",
                username=params["username"],
                project=db_project.name,
                description=e.__str__(),
                code="SUPER_RESOLUTION_FATAL_ERROR",
                project_id=db_project.id,
                project_type="PROJECT",
            ),
            owner_id=params["owner_id"],
            db=db,
        )
        traceback.print_exc()

    change_status_project_service(
        id=db_project.id,
        status=status,
        db=db,
    )

    if not img_save_path:
        add_task_result(id=db_project.id, task_result=None, db=db)
        raise Exception

    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action=f"End of super resolution without satellite {db_project.type}",
            username=params["username"],
            project=db_project.name,
            description="Status change from 'In progress' to 'Completed'",
            project_id=db_project.id,
            project_type="PROJECT",
        ),
        owner_id=params["owner_id"],
        db=db,
    )

    task_result = {
        "path_images": img_save_path,
        "layer_id": "",
        "project_id": params["project_id"],
    }

    add_task_result(id=db_project.id, task_result=task_result, db=db)

    unload_ml_models_triton_service(
        project_type=db_project.type,
        names=db_project.ml_model,
        names_deeplab=db_project.ml_model_deeplab,
        name_qualities=params["quality"],
        db=db
    )
    delete_dir(path=f"static/{params['project_id']}/{params['project_type']}/images")
    delete_dir(path=f"static/{params['project_id']}/{params['project_type']}/tif")

    return task_result


@celery.task(name="create_360_task")
def create_360_task(
    task_type: int,
    params: Dict[str, Any],
) -> Dict[str, Union[list[str], Any]]:
    db = get_db_iter()
    db_project = get_project_by_id_service(id=params["project_id"], db=db)
    try:
        classes = list(set(
            name for part in (params["ml_classes"] + params["deeplab_ml_classes"])
            for name in part
        )) + ["trajectory"]

        add_project_classes_sr_service(
            id=db_project.id,
            classes=classes,
            super_resolution='x1',
            db=db
        )

        result_360 = send_360_service(
            project_id=task_type,
            project_type=params["project_type"],
            paths=params["paths"],
            ml_model=params["ml_model"],
            names_models_deeplab=params["deeplab_ml_model"],
            tile_size_yolo=params["tile_size_yolo"],
            tile_size_deeplab=params["tile_size_deeplab"],
            scale_factor_yolo=params["scale_factor_yolo"],
            scale_factor_deeplab=params["scale_factor_deeplab"],
            classes_yolo_model=params["ml_classes"],
            class_names_deeplab=params["deeplab_ml_classes"],
            view_yolo=params["view_yolo"],
            view_deeplab=params["view_deeplab"],
        )
        path_shp_result = f"static/{params['project_id']}/{params['project_type']}/360_result/{params['project_id']}"
        path_dir_result = (
            f"static/{params['project_id']}/{params['project_type']}/360_result/"
        )

        path = merge_zips(
            list_paths_dirs=[path_shp_result],
            save_to=path_shp_result,
            name_zip=f"panorama_360_result_project_id_{params['project_id']}",
            classes_list=classes,
        )
        layer_id = gis_service.upload_shape_layer(shape_zip_path=path)
        delete_file(path)
        copy_dir(
            origin=path_dir_result,
            target=f"static/nextcloud/Admin123/files/{params['link']}/360_result",
        )
        change_status_project_service(
            id=db_project.id,
            status=StatusProjectEnum.completed,
            db=db,
        )
    except Exception as e:
        result_360 = None
        layer_id = None
        change_status_project_service(
            id=db_project.id,
            status=StatusProjectEnum.error,
            db=db,
            description=e.__str__(),
            error_code="CREATE_360_TASK_FAILED",
        )
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="360 failed with an error",
                username=params["username"],
                project=db_project.name,
                description=e.__str__(),
                code="CREATE_360_TASK_FAILED",
                project_id=db_project.id,
                project_type="PROJECT",
            ),
            owner_id=params["owner_id"],
            db=db,
        )
        print(f"Error: {e}")
        traceback.print_exc()

    if not result_360:
        add_task_result(id=db_project.id, task_result=None, db=db)
        raise Exception

    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action=f"End of 360 {db_project.type}",
            username=params["username"],
            project=db_project.name,
            description="Status change from 'In progress' to 'Completed'",
            project_id=db_project.id,
            project_type="PROJECT",
        ),
        owner_id=params["owner_id"],
        db=db,
    )

    task_result = {
        "path_images": result_360.image_list,
        "pcd_path": result_360.pcd_path,
        "layer_id": layer_id,
        "project_id": params["project_id"],
    }

    add_task_result(id=db_project.id, task_result=task_result, db=db)

    unload_ml_models_triton_service(
        project_type=db_project.type,
        names=db_project.ml_model,
        names_deeplab=db_project.ml_model_deeplab,
        db=db
    )
    folders = os.listdir(f"static/{params['project_id']}/{params['project_type']}")
    for folder in folders:
        if "result" in folder:
            continue
        delete_dir(
            path=f"static/{params['project_id']}/{params['project_type']}/{folder}"
        )

    return task_result


@celery.task(name="create_ml_model_task")
def create_ml_model_task(
    link: str, id: int, ml_classes: List[str], username: str, owner_id: str, ml_model_name
) -> Dict[str, str]:
    db = get_db_iter()
    origin = f"/geo_ai_backend/static/nextcloud/Admin123/files/{link}"
    print(f"checking path:(origin)")
    if not os.path.exists(origin) or not os.path.isdir(origin):
        create_action_history_service(
            action_history=CreateActionHistorySchemas(
                user_action="Create ml models",
                username=username,
                project=ml_model_name,
                description="Path not found",
            ),
            owner_id=owner_id,
            db=db,
        )
        change_status_ml_model_service(id=id, status=StatusModelEnum.error, db=db)
        raise PathNotFoundException

    object_classes = get_object_classes_service(path=origin)

    if not object_classes:
        create_action_history_service(
            action_history=CreateActionHistorySchemas(
                user_action="Create ml models",
                username=username,
                project=ml_model_name,
                description="Invalid directory structure",
            ),
            owner_id=owner_id,
            db=db,
        )
        change_status_ml_model_service(id=id, status=StatusModelEnum.error, db=db)
        raise InvalidDirectoryStructure

    ml_server_url = f"{settings.ML_SERVER_URL}:{settings.ML_SERVER_PORT}"

    task_id = None
    retry = 0
    while True:
        if retry >= 4:
            break

        task_result = launch_task_service(
            url=f"{ml_server_url}/api/pipline/upload-dataset?id={id}&path={link}"
        )
        if not task_result:
            retry += 1
            time.sleep(60)
        else:
            task_id = task_result.get("task_id")
            break


    if task_id:
        while True:
            status = check_task_status_service(
                url=f"{ml_server_url}/api/pipline/task-status/{task_id}"
            )
            if status == "SUCCESS":
                break
            elif status == "FAILURE":
                break
            else:
                time.sleep(60)
    change_status_ml_model_service(id=id, status=StatusModelEnum.not_trained, db=db)
    add_ml_model_task_result_by_id_service(
        id=id,
        task_result={
            "classes": ml_classes,
            "objects": object_classes,
        },
        db=db,
    )
    return {
        "classes": ml_classes,
        "objects": object_classes,
    }


@celery.task(name="traning_ml_model_task")
def train_ml_model_task(
    id: int,
    epochs: int,
    scale_factor: float,
    type_model: str,
    type_of_data: str,
    classes: List[str],
    data_path: str,
) -> Dict[str, str]:

    if type_model == TypeMlModelTrainingEnum.deeplab.value:
        # crop_size = CropSizeEnumDeeplab[type_of_data].value
        img_size = ImageSizeEnumDeeplab[type_of_data].value
        if type_of_data == TypeMLModelEnum.panorama_360.value:
            scale_factor = ScaleFactorDeeplabEnum[type_of_data].value

    elif type_model == TypeMlModelTrainingEnum.yolov.value:
        # crop_size = CropSizeEnum[type_of_data].value
        img_size = ImageSizeEnum[type_of_data].value
        if type_of_data == TypeMLModelEnum.panorama_360.value or type_of_data == TypeMLModelEnum.garbage.value:
            scale_factor = ScaleFactorYoloEnum[type_of_data].value

    elif type_model == TypeMlModelTrainingEnum.yolov_det.value:
        # crop_size = CropSizeEnum[type_of_data].value
        img_size = ImageSizeEnum[type_of_data].value
        if type_of_data == TypeMLModelEnum.panorama_360.value or type_of_data == TypeMLModelEnum.garbage.value:
            scale_factor = ScaleFactorYoloEnum[type_of_data].value

    else:
        raise NotTrainingTypeModel

    if scale_factor != 0:
        crop_size = int(img_size / scale_factor)
    else:
        crop_size = 0

    runs_info = [
        {
            "data_path": data_path,
            "classes": classes,
            "crop_size": crop_size,
            "ml_model_type": type_model,
            "img_size": img_size,
            "epochs": epochs,
            "registered_model_name": "",
            "config": {},
        }
    ]
    creds = {"user": "admin", "password": "password"}
    ml_server_url = f"{settings.ML_SERVER_URL}:{settings.ML_SERVER_PORT}"
    task_result = launch_task_service(
        url=f"{ml_server_url}/api/pipline/train",
        data=json.dumps({"creds": creds, "runs_info": runs_info}),
    )
    print("DEBUG :task_result=",task_result)
    task_id = task_result.get("task_id")
    if task_id:
        while True:
            status = check_task_status_service(
                url=f"{ml_server_url}/api/pipline/task-status/{task_id}"
            )
            if status in {"PROGRESS", "SUCCESS", "FAILURE"}:
                break
            else:
                time.sleep(10)
    db = get_db_iter()
    add_ml_model_experiment_name_service(
        id=id, experiment_name=task_result.get("experiment_name"), db=db
    )
    add_ml_model_view_service(
        id=id, type_model=type_model, db=db
    )
    add_ml_model_scale_factor_tile_size_service(
        id=id, scale_factor=scale_factor, tile_size=img_size, db=db
    )
    add_ml_flow_url_service(
        id=id,
        experiment_value=task_result.get("experiment_value"),
        run_id=task_result.get("experiment_id"),
        db=db,
    )
    task_id = task_result.get("task_id")
    if task_id:
        while True:
            status = check_task_status_service(
                url=f"{ml_server_url}/api/pipline/task-status/{task_id}"
            )
            if status == "SUCCESS":
                get_result_task_service(
                    url=f"{ml_server_url}/api/pipline/task-status/{task_id}"
                )
                break
            elif status == "FAILURE":
                break
            else:
                time.sleep(60)
    change_status_ml_model_service(id=id, status=StatusModelEnum.trained, db=db)
    return task_result


@celery.task(name="save_ml_model_task")
def save_ml_model_task(id: int, experiment_name: str) -> None:
    db = get_db_iter()
    ml_server_url = f"{settings.ML_SERVER_URL}:{settings.ML_SERVER_PORT}"

    task_id = None
    retry = 0
    while True:
        if retry >= 4:
            break

        task_result = launch_task_service(
            url=f"{ml_server_url}/api/pipline/save-ml-model?id={id}&experiment_name={experiment_name}",
        )
        if not task_result:
            retry += 1
            time.sleep(60)
        else:
            task_id = task_result.get("task_id")
            break

    if task_id:
        while True:
            status = check_task_status_service(
                url=f"{ml_server_url}/api/pipline/task-status/{task_id}"
            )
            if status == "SUCCESS":
                break
            elif status == "FAILURE":
                break
            else:
                time.sleep(60)
    print(f"debug:received experiment_name={experiment_name}")
    get_dataset_nextcloud_service(id=id, path=experiment_name)
    delete_dir(path=f"static/nextcloud/Admin123/files/{experiment_name}.zip")
    link_model = load_ml_model_to_triton_service(id=id, experiment_name=experiment_name)
    update_link_ml_model_service(id=id, link=link_model, db=db)
    change_status_ml_model_service(id=id, status=StatusModelEnum.ready_to_use, db=db)
