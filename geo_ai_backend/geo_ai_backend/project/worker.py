from typing import Dict, List, Union
from pyproj.exceptions import ProjError
from geo_ai_backend.database import get_db_iter
from geo_ai_backend.project.exceptions import (
    EmptyNextcloudFolderException,
    NotFoundFileNextcloudException,
    CRSConversionException,
    IncorrectFormatCsvOrJpgException,
)
from geo_ai_backend.history.schemas import (
    CreateActionHistorySchemas,
    CreateErrorHistorySchemas,
)
from geo_ai_backend.history.service import (
    create_action_history_service,
    create_error_history_service,
)
from geo_ai_backend.ml.service import (
    compare_service,
    get_ml_model_by_link_service,
)
from geo_ai_backend.project.schemas import StatusProjectEnum
from geo_ai_backend.project.service import (
    change_status_compare_project_service,
    change_status_project_service,
    get_compare_projects_by_id_service,
    add_task_result_compare_projects_service,
    check_update_nextcloud_folder_service,
    get_project_files_service,
    add_input_files_service,
    get_project_by_name_service,
)
from geo_ai_backend.utils import (
    copy_dir,
)
from geo_ai_backend.worker import celery
from geo_ai_backend.arcgis.service import gis_service
import traceback


@celery.task(name="create_comparing_task")
def create_comparing_task(
    paths_images: List[str],
    id: List[int],
    project_type: str,
    id_compare: id,
    username: str,
    owner_id: int,
) -> Dict[str, Union[List[int], Dict[str, str]]]:
    db = get_db_iter()
    db_compare_projects = get_compare_projects_by_id_service(
        id=id_compare, db=db
    )
    db_project_1 = get_project_by_name_service(
        name=db_compare_projects.project_1, db=db
    )
    db_project_2 = get_project_by_name_service(
        name=db_compare_projects.project_2, db=db
    )

    classes_yolo_1 = {
        class_yolo
        for link_yolo in db_project_1.ml_model
        for class_yolo in
        get_ml_model_by_link_service(link=link_yolo, db=db).type_of_objects
    }

    classes_yolo_2 = {
        class_yolo
        for link_yolo in db_project_2.ml_model
        for class_yolo in
        get_ml_model_by_link_service(link=link_yolo, db=db).type_of_objects
    }

    classes_deeplab_1 = {
        class_deeplab
        for link_deeplab in db_project_1.ml_model_deeplab
        for class_deeplab in
        get_ml_model_by_link_service(link=link_deeplab, db=db).type_of_objects
    }

    classes_deeplab_2 = {
        class_deeplab
        for link_deeplab in db_project_2.ml_model_deeplab
        for class_deeplab in
        get_ml_model_by_link_service(link=link_deeplab, db=db).type_of_objects
    }

    classes_list = list(
        classes_yolo_1 | classes_yolo_2 | classes_deeplab_1 | classes_deeplab_2
    )

    status = StatusProjectEnum.completed
    try:
        result_compare = compare_service(
            paths_images=paths_images,
            id=id,
            project_type=project_type,
            classes_list=classes_list
        )

        paths_zips = result_compare[-1]
        action_name = result_compare[-2]
        layers_ids = [
            gis_service.upload_shape_layer(shape_zip_path=path) for path in paths_zips
        ]
        result_layers = dict(zip(action_name, layers_ids))
        copy_dir(
            origin="static/compare_result",
            target=f"static/nextcloud/Admin123/files/compare_result",
        )
        change_status_compare_project_service(
            id=db_compare_projects.id, status=status, db=db
        )
        create_action_history_service(
            action_history=CreateActionHistorySchemas(
                user_action="End of comparing",
                username=username,
                project=f"{db_compare_projects.project_1} - {db_compare_projects.project_2}",
                description="Status change from 'In progress' to 'Completed'",
                project_id=db_compare_projects.id,
                project_type="PROJECT_COMPARE",
            ),
            owner_id=owner_id,
            db=db,
        )
    except Exception as e:
        status = StatusProjectEnum.error
        result_compare = None
        result_layers = {}
        print(f"Error: {e}")
        change_status_compare_project_service(
            id=db_compare_projects.id,
            status=status,
            db=db,
            description=e.__str__(),
            error_code="CREATE_COMPARING_TASK_FAILED"
        )
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Comparing failed with an error",
                username=username,
                project=f"{db_compare_projects.project_1} and {db_compare_projects.project_2}",
                description=e.__str__(),
                code="CREATE_COMPARING_TASK_FAILED",
                project_id=db_compare_projects.id,
                project_type="PROJECT_COMPARE",
            ),
            owner_id=owner_id,
            db=db,
        )
        traceback.print_exc()

    if not result_compare:
        add_task_result_compare_projects_service(
            id=db_compare_projects.id, task_result=None, db=db
        )
        create_action_history_service(
            action_history=CreateActionHistorySchemas(
                user_action="Comparing failed with an error",
                username=username,
                project=f"{db_compare_projects.project_1} - {db_compare_projects.project_2}",
                description="Status change from 'In progress' to 'Ready to start'",
                project_type="PROJECT_COMPARE",
            ),
            owner_id=owner_id,
            db=db,
        )
        raise Exception

    task_result = {"layer_objects": result_layers, "project_ids": id}
    add_task_result_compare_projects_service(
        id=db_compare_projects.id, task_result=task_result, db=db
    )

    return task_result


@celery.task(name="check_update_nextcloud_folder_task")
def get_project_files_service_task(
    project_id: int,
    project_type: str,
    folder: str,
    project_name: str,
    username: str,
    owner_id: int,
) -> Dict[str, str]:
    db = get_db_iter()
    try:
        check_update_nextcloud_folder_service(
            project_id=project_id,
            project_type=project_type,
            folder=folder,
        )
    except EmptyNextcloudFolderException:
        change_status_project_service(
            id=project_id,
            status=StatusProjectEnum.error,
            db=db,
            description="Folder in nextcloud cannot be empty",
            error_code="NEXTCLOUD_EMPTY_FOLDER",
        )
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Create project",
                username=username,
                project=project_name,
                description="Folder in nextcloud cannot be empty",
                code="NEXTCLOUD_EMPTY_FOLDER",
                project_id=project_id,
                project_type="PROJECT",
            ),
            owner_id=owner_id,
            db=db,
        )
        return {"status": "not ok"}
    except NotFoundFileNextcloudException as e:
        change_status_project_service(
            id=project_id,
            status=StatusProjectEnum.error,
            db=db,
            description=e.__str__(),
            error_code="NEXTCLOUD_FILES_NOT_FOUND",
        )
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Create project",
                username=username,
                project=project_name,
                description=e.__str__(),
                code="NEXTCLOUD_FILES_NOT_FOUND",
                project_id=project_id,
                project_type="PROJECT",
            ),
            owner_id=owner_id,
            db=db,
        )
        return {"status": "not ok"}

    try:
        project_files = get_project_files_service(
            project_id=project_id, project_type=project_type, db=get_db_iter()
        )
    except ProjError:
        change_status_project_service(
            id=project_id,
            status=StatusProjectEnum.error,
            db=db,
            description="Error tif when trying to convert CRS.",
            error_code="INVALID_TIF_FILE",
        )
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Create project",
                username=username,
                project=project_name,
                description="Error tif when trying to convert CRS.",
                code="INVALID_TIF_FILE",
                project_id=project_id,
                project_type="PROJECT",
            ),
            owner_id=owner_id,
            db=db,
        )
        raise CRSConversionException
    except IncorrectFormatCsvOrJpgException as e:
        change_status_project_service(
            id=project_id,
            status=StatusProjectEnum.error,
            db=db,
            description=e.__class__.__doc__,
            error_code="INVALID_FORMAT_FILE",
        )
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Create project",
                username=username,
                project=project_name,
                description=e.__class__.__doc__,
                code="INVALID_FORMAT_JPG_CSV_FILE",
                project_id=project_id,
                project_type="PROJECT",
            ),
            owner_id=owner_id,
            db=db,
        )
        raise e
    except Exception as e:
        change_status_project_service(
            id=project_id,
            status=StatusProjectEnum.error,
            db=db,
            description=e.__str__(),
            error_code="SOURCE_DATA_FORMAT_ERROR",
        )
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Create project",
                username=username,
                project=project_name,
                description=e.__str__(),
                code="SOURCE_DATA_FORMAT_ERROR",
                project_id=project_id,
                project_type="PROJECT",
            ),
            owner_id=owner_id,
            db=db,
        )
        raise e
    add_input_files_service(
        id=project_id,
        input_files=project_files.dict(),
        db=get_db_iter(),
    )
    return {"status": "ok"}
