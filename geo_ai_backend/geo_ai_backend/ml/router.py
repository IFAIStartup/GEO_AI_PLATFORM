from typing import Dict, List
from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from geo_ai_backend.database import get_db
from geo_ai_backend.config import settings
from geo_ai_backend.auth.permissions import get_current_user_from_access
from geo_ai_backend.auth.schemas import UserServiceSchemas
from geo_ai_backend.history.service import (
    create_error_history_service,
    create_action_history_service,
)
from geo_ai_backend.history.schemas import (
    CreateActionHistorySchemas,
    CreateErrorHistorySchemas,
)
from geo_ai_backend.project.schemas import StatusProjectEnum
from geo_ai_backend.project.service import (
    add_ml_models_deeplab_service,
    add_preview_selected_images,
    get_project_by_id_service,
    get_project_by_detection_id,
    change_status_project_service,
    change_detection_id_service,
    add_task_result,
    add_ml_models_service,
)
from geo_ai_backend.ml.schemas import (
    CreateMLModelSchemas,
    MLModelSchemas,
    MLModelsSchemas,
    GetTaskResultSchemas,
    Qualities,
    StatusModelEnum,
    TaskIdSchemas,
    SendDetectionSchemas,
    Send360Schemas,
    TrainMLModelSchemas,
    TypeMLModelEnum,
    SortKeyEnum,
    TypeMlModelTrainingEnum,
    ViewMLModelEnum,
)
from geo_ai_backend.ml.worker import (
    create_detection_task,
    create_360_task,
    create_ml_model_task,
    create_satellite_task,
    create_superresolution_detection_task,
    create_superresolution_satellite_task,
    train_ml_model_task,
    save_ml_model_task,
)
from geo_ai_backend.ml.service import (
    add_ml_model_task_id_service,
    change_ml_classes_by_id_service,
    change_status_ml_model_service,
    get_all_ml_models,
    get_ml_model_by_task_id_service,
    load_default_ml_model_triton_service,
    create_ml_model_service,
    get_ml_model_by_id_service,
    get_ml_model_by_name_service,
    delete_ml_model_by_id_service,
    unload_ml_model_triton_service,
    get_ml_classes_by_name_service,
    get_ml_model_by_type_of_data_service,
    update_type_of_objects_ml_model_service,
    load_ml_model_triton_service,
    get_ml_models_by_names_service,
)
from geo_ai_backend.auth.service import get_user_by_id_service

router = APIRouter(
    prefix="/ml",
    tags=["ml"],
)


@router.get("/tasks/{task_id}", response_model=GetTaskResultSchemas)
async def get_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> GetTaskResultSchemas:
    task_result = AsyncResult(task_id)

    if task_result.name == "create_ml_model_task":
        ml_model = get_ml_model_by_task_id_service(task_id=task_result.task_id, db=db)
        result = task_result.result
        if task_result.successful():
            status = StatusModelEnum.not_trained
            create_action_history_service(
                action_history=CreateActionHistorySchemas(
                    user_action=f"The ml model '{ml_model.name}' has been successfully created.",
                    username=current_user.username,
                    project=ml_model.name,
                    description="Create ml model",
                ),
                owner_id=current_user.id,
                db=db,
            )
        elif task_result.failed():
            status = StatusModelEnum.error
            result = {
                "status": task_result.traceback.split("\n")[-2].strip().split(".")[-1],
            }
            create_error_history_service(
                error_history=CreateErrorHistorySchemas(
                    user_action=f"An error occurred during the creation of the ml model '{ml_model.name}'.",
                    username=current_user.username,
                    project=ml_model.name,
                    description="Create ml model",
                    code="CREATE_ML_MODEL_ERROR",
                ),
                owner_id=current_user.id,
                db=db,
            )
        change_status_ml_model_service(id=ml_model.id, status=status, db=db)
        return GetTaskResultSchemas(
            task_id=task_result.task_id,
            task_status=task_result.status,
            task_result=result,
        )
    if task_result.name == "traning_ml_model_task":
        ml_model = get_ml_model_by_task_id_service(task_id=task_result.task_id, db=db)
        if task_result.successful():
            create_action_history_service(
                action_history=CreateActionHistorySchemas(
                    user_action=f"The training of the ml model '{ml_model.name}' is completed successfully.",
                    username=current_user.username,
                    project=ml_model.name,
                    description="Traning ml model",
                ),
                owner_id=current_user.id,
                db=db,
            )
        elif task_result.failed():
            create_error_history_service(
                error_history=CreateErrorHistorySchemas(
                    user_action=f"Ml model '{ml_model.name}' training completed with an error.",
                    username=current_user.username,
                    project=ml_model.name,
                    description="Traning ml model",
                    code="TRANING_ML_MODEL_ERROR",
                ),
                owner_id=current_user.id,
                db=db,
            )
            change_status_ml_model_service(
                id=ml_model.id, status=StatusModelEnum.error, db=db
            )
        return GetTaskResultSchemas(
            task_id=task_result.task_id,
            task_status=task_result.status,
            task_result=task_result.result,
        )

    if task_result.name == "save_ml_model_task":
        ml_model = get_ml_model_by_task_id_service(task_id=task_result.task_id, db=db)
        if task_result.status == "SUCCESS":
            change_status_ml_model_service(
                id=ml_model.id, status=StatusModelEnum.ready_to_use, db=db
            )
        elif task_result.status == "FAILURE":
            change_status_ml_model_service(
                id=ml_model.id, status=StatusModelEnum.error, db=db
            )
            create_error_history_service(
                error_history=CreateErrorHistorySchemas(
                    user_action=f"Ml model '{ml_model.name}' cannot be saved.",
                    username=current_user.username,
                    project=ml_model.name,
                    description="Save ml model",
                    code="SAVE_ML_MODEL_ERROR",
                ),
                owner_id=current_user.id,
                db=db,
            )
        return GetTaskResultSchemas(
            task_id=task_result.task_id,
            task_status=task_result.status,
            task_result=task_result.result,
        )

    db_project = get_project_by_detection_id(id=task_id, db=db)

    if task_result.status == "SUCCESS":
        add_task_result(id=db_project.id, task_result=task_result.result, db=db)
        change_status_project_service(
            id=db_project.id,
            status=StatusProjectEnum.completed,
            db=db,
        )
        create_action_history_service(
            action_history=CreateActionHistorySchemas(
                user_action=f"End of detection {db_project.type}",
                username=current_user.username,
                project=db_project.name,
                description="Status change from 'In progress' to 'Completed'",
                project_id=db_project.id,
                project_type="PROJECT",
            ),
            owner_id=current_user.id,
            db=db,
        )
    if task_result.status == "FAILURE":
        add_task_result(id=db_project.id, task_result=None, db=db)

    return GetTaskResultSchemas(
        task_id=task_result.task_id,
        task_status=task_result.status,
        task_result=task_result.result,
    )


@router.get("/image-quality", response_model=Dict[str, str])
async def get_image_quality(
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> Dict[str, str]:
    return {i.name: i.value for i in Qualities}


@router.post(
    "/aerial",
    response_model=TaskIdSchemas,
    responses={
        422: {
            "description": "Path cannot be empty",
            "content": {
                "application/json": {"example": {"detail": "Path cannot be empty"}}
            },
        },
    },
)
async def send_detection(
    project_id: int,
    params: SendDetectionSchemas,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> TaskIdSchemas:
    db_project = get_project_by_id_service(id=project_id, db=db)
    if not db_project:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Start detection",
                username=current_user.username,
                project=db_project.name,
                description="Project is not exist",
                code="PROJECT_NOT_EXIST",
                project_type="PROJECT",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Project is not exist", "code": "PROJECT_NOT_EXIST"},
        )
    add_preview_selected_images(id=db_project.id, images=params.paths, db=db)

    if not params.ml_model and not params.ml_model_deeplab:
        change_status_project_service(
            id=project_id,
            status=StatusProjectEnum.in_progress,
            db=db,
        )
        task = superresolution_detection(
            db_project=db_project,
            username=current_user.username,
            owner_id=current_user.id,
            params=params,
            db=db
        )
        return TaskIdSchemas(
            task_id=task.id,
            project_id=project_id,
            task_name="detection_task_task",
            task_status=task.status,
        )

    names_models = params.ml_model
    db_ml_models = get_ml_models_by_names_service(names=names_models, db=db)
    names_models_deeplab = params.ml_model_deeplab
    deeplab_db_ml_models = get_ml_models_by_names_service(
        names=names_models_deeplab, db=db
    )

    if (
        (params.ml_model and not db_ml_models)
        or (params.ml_model_deeplab and not deeplab_db_ml_models)
    ):
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Start detection",
                username=current_user.username,
                project=db_project.name,
                description="ML model is not exist",
                code="ML_MODEL_NOT_EXIST",
                project_id=db_project.id,
                project_type="PROJECT",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "ML model is not exist", "code": "ML_MODEL_NOT_EXIST"},
        )

    links_yolo = [db_ml_models[j].link for j in range(len(names_models))]
    links_deeplab = [
        deeplab_db_ml_models[j].link for j in range(len(names_models_deeplab))
    ]
    add_ml_models_service(id=project_id, ml_model=links_yolo, db=db)
    add_ml_models_deeplab_service(id=project_id, ml_model=links_deeplab, db=db)
    change_status_project_service(
        id=project_id,
        status=StatusProjectEnum.in_progress,
        db=db,
    )
    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action="Start detection",
            username=current_user.username,
            project=db_project.name,
            description="Status change from 'Ready to start' to 'In progress'",
            project_id=db_project.id,
            project_type="PROJECT",
        ),
        owner_id=current_user.id,
        db=db,
    )
    for link_yolo in links_yolo:
        load_ml_model_triton_service(
            project_id=project_id,
            project_type=db_project.type,
            name=link_yolo,
            db=db,
        )
    for link_deeplab in links_deeplab:
        load_ml_model_triton_service(
            project_id=project_id,
            project_type=db_project.type,
            name=link_deeplab,
            db=db,
        )
    load_default_ml_model_triton_service(
        project_type=db_project.type, db=db, quality=params.quality
    )

    data = params.dict()
    data["project_id"] = db_project.id
    data["project_type"] = db_project.type
    data["name"] = "detection_task_task"
    data["link"] = db_project.link
    data["ml_model"] = links_yolo
    data["username"] = current_user.username
    classes_yolo = [db_ml_models[j].type_of_objects for j in range(len(names_models))]
    data["ml_classes"] = classes_yolo
    tile_size_yolo = [db_ml_models[j].tile_size for j in range(len(names_models))]
    data["tile_size_yolo"] = tile_size_yolo
    scale_factor_yolo = [db_ml_models[j].scale_factor for j in range(len(names_models))]
    data["scale_factor_yolo"] = scale_factor_yolo
    data["view_yolo"] = [db_ml_models[j].view for j in range(len(names_models))]

    data["deeplab_ml_model"] = links_deeplab
    classes_deeplab = [
        deeplab_db_ml_models[j].type_of_objects
        for j in range(len(names_models_deeplab))
    ]
    data["deeplab_ml_classes"] = classes_deeplab
    tile_size_deeplab = [
        deeplab_db_ml_models[j].tile_size for j in range(len(names_models_deeplab))
    ]
    data["tile_size_deeplab"] = tile_size_deeplab
    scale_factor_deeplab = [
        deeplab_db_ml_models[j].scale_factor for j in range(len(names_models_deeplab))
    ]
    data["scale_factor_deeplab"] = scale_factor_deeplab
    data["view_deeplab"] = [
        deeplab_db_ml_models[j].view for j in range(len(names_models_deeplab))
    ]
    data["owner_id"] = current_user.id
    task = create_detection_task.apply_async(args=(project_id, data))
    change_detection_id_service(id=project_id, detection_id=task.id, db=db)
    return TaskIdSchemas(
        task_id=task.id,
        project_id=project_id,
        task_name="detection_task_task",
        task_status=task.status,
    )


def superresolution_detection(db_project, username, owner_id, params, db):
    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action="Start detection",
            username=username,
            project=db_project.name,
            description="Status change from 'Ready to start' to 'In progress'",
            project_id=db_project.id,
        ),
        owner_id=owner_id,
        db=db,
    )
    load_default_ml_model_triton_service(
        project_type=db_project.type, db=db, quality=params.quality
    )
    data = params.dict()
    data["project_id"] = db_project.id
    data["project_type"] = db_project.type
    data["name"] = "detection_task_task"
    data["link"] = db_project.link
    data["ml_model"] = []
    data["username"] = username
    data["ml_classes"] = []
    data["tile_size_yolo"] = []
    data["scale_factor_yolo"] = []
    data["deeplab_ml_model"] = []
    data["deeplab_ml_classes"] = []
    data["tile_size_deeplab"] = []
    data["scale_factor_deeplab"] = []
    data["owner_id"] = owner_id
    task = create_superresolution_detection_task.apply_async(args=(db_project.id, data))
    change_detection_id_service(id=db_project.id, detection_id=task.id, db=db)
    return task


@router.post(
    "/satellite",
    response_model=TaskIdSchemas,
    responses={
        422: {
            "description": "Path cannot be empty",
            "content": {
                "application/json": {"example": {"detail": "Path cannot be empty"}}
            },
        },
    },
)
async def send_satellite(
    project_id: int,
    params: SendDetectionSchemas,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> TaskIdSchemas:
    db_project = get_project_by_id_service(id=project_id, db=db)
    if not db_project:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Start satellite",
                username=current_user.username,
                project=db_project.name,
                description="Project is not exist",
                code="PROJECT_NOT_EXIST",
                project_type="PROJECT",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Project is not exist", "code": "PROJECT_NOT_EXIST"},
        )
    add_preview_selected_images(id=db_project.id, images=params.paths, db=db)

    if not params.ml_model and not params.ml_model_deeplab:
        change_status_project_service(
            id=project_id,
            status=StatusProjectEnum.in_progress,
            db=db,
        )
        task = superresolution_satellite(
            db_project=db_project,
            username=current_user.username,
            params=params,
            owner_id=current_user.id,
            db=db
        )
        return TaskIdSchemas(
            task_id=task.id,
            project_id=project_id,
            task_name="satellite_task_task",
            task_status=task.status,
        )

    names_models = params.ml_model
    db_ml_models = get_ml_models_by_names_service(names=names_models, db=db)
    names_models_deeplab = params.ml_model_deeplab
    deeplab_db_ml_models = get_ml_models_by_names_service(
        names=names_models_deeplab, db=db
    )
    if (
        (params.ml_model and not db_ml_models)
        or (params.ml_model_deeplab and not deeplab_db_ml_models)
    ):
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Start satellite",
                username=current_user.username,
                project=db_project.name,
                description="ML model is not exist",
                code="ML_MODEL_NOT_EXIST",
                project_id=db_project.id,
                project_type="PROJECT",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "ML model is not exist", "code": "ML_MODEL_NOT_EXIST"},
        )
    links_yolo = [db_ml_models[j].link for j in range(len(names_models))]
    links_deeplab = [
        deeplab_db_ml_models[j].link for j in range(len(names_models_deeplab))
    ]
    add_ml_models_service(id=project_id, ml_model=links_yolo, db=db)
    add_ml_models_deeplab_service(id=project_id, ml_model=links_deeplab, db=db)

    change_status_project_service(
        id=project_id,
        status=StatusProjectEnum.in_progress,
        db=db,
    )

    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action="Start satellite",
            username=current_user.username,
            project=db_project.name,
            description="Status change from 'Ready to start' to 'In progress'",
            project_id=db_project.id,
            project_type="PROJECT",
        ),
        owner_id=current_user.id,
        db=db,
    )

    for link_yolo in links_yolo:
        load_ml_model_triton_service(
            project_id=project_id,
            project_type=db_project.type,
            name=link_yolo,
            db=db,
        )
    for link_deeplab in links_deeplab:
        load_ml_model_triton_service(
            project_id=project_id,
            project_type=db_project.type,
            name=link_deeplab,
            db=db,
        )
    load_default_ml_model_triton_service(
        project_type=db_project.type, db=db, quality=params.quality
    )

    data = params.dict()
    data["project_id"] = db_project.id
    data["project_type"] = db_project.type
    data["name"] = "satellite_task_task"
    data["link"] = db_project.link
    data["ml_model"] = links_yolo
    data["username"] = current_user.username
    classes_yolo = [db_ml_models[j].type_of_objects for j in range(len(names_models))]
    data["ml_classes"] = classes_yolo
    tile_size_yolo = [db_ml_models[j].tile_size for j in range(len(names_models))]
    data["tile_size_yolo"] = tile_size_yolo
    scale_factor_yolo = [db_ml_models[j].scale_factor for j in range(len(names_models))]
    data["scale_factor_yolo"] = scale_factor_yolo
    data["view_yolo"] = [db_ml_models[j].view for j in range(len(names_models))]

    data["deeplab_ml_model"] = links_deeplab
    classes_deeplab = [
        deeplab_db_ml_models[j].type_of_objects
        for j in range(len(names_models_deeplab))
    ]
    data["deeplab_ml_classes"] = classes_deeplab
    tile_size_deeplab = [
        deeplab_db_ml_models[j].tile_size for j in range(len(names_models_deeplab))
    ]
    data["tile_size_deeplab"] = tile_size_deeplab
    scale_factor_deeplab = [
        deeplab_db_ml_models[j].scale_factor for j in range(len(names_models_deeplab))
    ]
    data["scale_factor_deeplab"] = scale_factor_deeplab
    data["view_deeplab"] = [
        deeplab_db_ml_models[j].view for j in range(len(names_models_deeplab))
    ]
    data["owner_id"] = current_user.id
    task = create_satellite_task.apply_async(args=(project_id, data))
    change_detection_id_service(id=project_id, detection_id=task.id, db=db)
    return TaskIdSchemas(
        task_id=task.id,
        project_id=project_id,
        task_name="satellite_task_task",
        task_status=task.status,
    )


def superresolution_satellite(db_project, username, owner_id, params, db):
    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action="Start satellite",
            username=username,
            project=db_project.name,
            description="Status change from 'Ready to start' to 'In progress'",
            project_id=db_project.id,
            project_type="PROJECT",
        ),
        owner_id=owner_id,
        db=db,
    )
    load_default_ml_model_triton_service(
        project_type=db_project.type, db=db, quality=params.quality
    )
    data = params.dict()
    data["project_id"] = db_project.id
    data["project_type"] = db_project.type
    data["name"] = "detection_task_task"
    data["link"] = db_project.link
    data["ml_model"] = []
    data["username"] = username
    data["ml_classes"] = []
    data["tile_size_yolo"] = []
    data["scale_factor_yolo"] = []
    data["deeplab_ml_model"] = []
    data["deeplab_ml_classes"] = []
    data["tile_size_deeplab"] = []
    data["scale_factor_deeplab"] = []
    data["owner_id"] = owner_id
    task = create_superresolution_satellite_task.apply_async(args=(db_project.id, data))
    change_detection_id_service(id=db_project.id, detection_id=task.id, db=db)
    return task


@router.post(
    "/360",
    response_model=TaskIdSchemas,
    responses={
        422: {
            "description": "Path cannot be empty",
            "content": {
                "application/json": {"example": {"detail": "Path cannot be empty"}}
            },
        },
    },
)
async def send_360(
    project_id: int,
    params: Send360Schemas,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> TaskIdSchemas:
    db_project = get_project_by_id_service(id=project_id, db=db)
    if not db_project:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Start 360",
                username=current_user.username,
                project=db_project.name,
                description="Project is not exist",
                code="PROJECT_NOT_EXIST",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Project is not exist", "code": "PROJECT_NOT_EXIST"},
        )
    add_preview_selected_images(id=db_project.id, images=params.paths, db=db)
    names_models = params.ml_model
    db_ml_models = get_ml_models_by_names_service(names=names_models, db=db)
    names_models_deeplab = params.ml_model_deeplab
    deeplab_db_ml_models = get_ml_models_by_names_service(
        names=names_models_deeplab, db=db
    )
    if (
        (params.ml_model and not db_ml_models)
        or (params.ml_model_deeplab and not deeplab_db_ml_models)
    ):
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Start 360",
                username=current_user.username,
                project=db_project.name,
                description="Ml model is not exist",
                code="ML_MODEL_NOT_EXIST",
                project_id=db_project.id,
                project_type="PROJECT",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "ML model is not exist", "code": "ML_MODEL_NOT_EXIST"},
        )
    links_yolo = [db_ml_models[j].link for j in range(len(names_models))]
    links_deeplab = [deeplab_db_ml_models[j].link for j in range(len(deeplab_db_ml_models))]
    add_ml_models_service(id=project_id, ml_model=links_yolo, db=db)
    add_ml_models_deeplab_service(id=project_id, ml_model=links_deeplab, db=db)

    change_status_project_service(
        id=project_id,
        status=StatusProjectEnum.in_progress,
        db=db,
    )

    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action="Start panorama 360",
            username=current_user.username,
            project=db_project.name,
            description="Status change from 'Ready to start' to 'In progress'",
            project_id=db_project.id,
            project_type="PROJECT",
        ),
        owner_id=current_user.id,
        db=db,
    )

    for link_yolo in links_yolo:
        load_ml_model_triton_service(
            project_id=project_id,
            project_type=db_project.type,
            name=link_yolo,
            db=db,
        )
    for link_deeplab in links_deeplab:
        load_ml_model_triton_service(
            project_id=project_id,
            project_type=db_project.type,
            name=link_deeplab,
            db=db,
        )
    load_default_ml_model_triton_service(
        project_type=db_project.type,
        db=db,
    )

    data = params.dict()
    data["project_id"] = db_project.id
    data["project_type"] = db_project.type
    data["link"] = db_project.link
    data["ml_model"] = links_yolo
    data["username"] = current_user.username
    classes_yolo = [db_ml_models[j].type_of_objects for j in range(len(names_models))]
    data["ml_classes"] = classes_yolo
    tile_size_yolo = [db_ml_models[j].tile_size for j in range(len(names_models))]
    data["tile_size_yolo"] = tile_size_yolo
    scale_factor_yolo = [db_ml_models[j].scale_factor for j in range(len(names_models))]
    data["scale_factor_yolo"] = scale_factor_yolo
    data["view_yolo"] = [db_ml_models[j].view for j in range(len(names_models))]

    data["deeplab_ml_model"] = links_deeplab
    classes_deeplab = [
        deeplab_db_ml_models[j].type_of_objects
        for j in range(len(names_models_deeplab))
    ]
    data["deeplab_ml_classes"] = classes_deeplab
    tile_size_deeplab = [
        deeplab_db_ml_models[j].tile_size for j in range(len(names_models_deeplab))
    ]
    data["tile_size_deeplab"] = tile_size_deeplab
    scale_factor_deeplab = [
        deeplab_db_ml_models[j].scale_factor for j in range(len(names_models_deeplab))
    ]
    data["scale_factor_deeplab"] = scale_factor_deeplab
    data["view_deeplab"] = [
        deeplab_db_ml_models[j].view for j in range(len(names_models_deeplab))
    ]
    data["owner_id"] = current_user.id
    task = create_360_task.apply_async(args=(project_id, data))
    change_detection_id_service(id=project_id, detection_id=task.id, db=db)
    return TaskIdSchemas(
        task_id=task.id,
        project_id=project_id,
        task_name="360_task",
        task_status=task.status,
    )


@router.get("/get-ml-model")
async def get_ml_model(
    id: int,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> MLModelSchemas:
    db_ml_model = get_ml_model_by_id_service(id=id, db=db)
    if not db_ml_model:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Get ml model",
                username=current_user.username,
                project="",
                description="ML model is not exist",
                code="ML_MODEL_NOT_EXIST",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "ML model is not exist", "code": "ML_MODEL_NOT_EXIST"},
        )
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


@router.get("/get-ml-models")
async def get_ml_models(
    search: str = "",
    filter: TypeMLModelEnum = TypeMLModelEnum.all,
    sort: SortKeyEnum = SortKeyEnum.created_at,
    reverse: bool = False,
    page: int = 1,
    limit: int = Query(default=10, lte=10),
    default: bool = True,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> MLModelsSchemas:
    return get_all_ml_models(
        search=search,
        filter=filter,
        sort=sort,
        reverse=reverse,
        limit=limit,
        page=page,
        default=default,
        db=db,
    )


@router.post("/create-ml-model")
async def create_ml_model(
    params: CreateMLModelSchemas,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> TaskIdSchemas:
    db_ml_model = get_ml_model_by_name_service(name=params.name, db=db)
    if db_ml_model:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Create ml model",
                username=current_user.username,
                project="",
                description="ML model name already exist",
                code="ML_MODEL_NAME_ALREADY_EXIST",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "ML model name already exist",
                "code": "ML_MODEL_NAME_ALREADY_EXIST",
            },
        )
    db_ml_model = create_ml_model_service(
        ml_model=params, username=current_user.username, db=db
    )
    ml_classes = get_ml_classes_by_name_service(name=params.type_of_data, db=db)
    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action="Create ml models",
            username=current_user.username,
            project=params.name,
            description=f"Create {params.name}",
        ),
        owner_id=current_user.id,
        db=db,
    )
    classes = get_ml_classes_by_name_service(name=params.type_of_data, db=db)
    db_ml_model = update_type_of_objects_ml_model_service(
        id=db_ml_model.id, type_of_objects=classes, db=db
    )
    task = create_ml_model_task.apply_async(
        args=(
            params.link,
            db_ml_model.id,
            ml_classes,
            current_user.username,
            current_user.id,
            db_ml_model.name,
        )
    )
    add_ml_model_task_id_service(id=db_ml_model.id, task_id=task.id, db=db)
    change_status_ml_model_service(
        id=db_ml_model.id, status=StatusModelEnum.preparing, db=db
    )
    return TaskIdSchemas(
        task_id=task.id,
        project_id=db_ml_model.id,
        task_name="create_ml_model_task",
        task_status=task.status,
    )


@router.post("/delete-ml-model")
async def delete_ml_model(
    id: int,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> Dict[str, str]:
    db_ml_model = get_ml_model_by_id_service(id=id, db=db)
    if not db_ml_model:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Delete ml model",
                username=current_user.username,
                project="",
                description="Ml model is not exist",
                code="ML_MODEL_NOT_EXIST",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "ML model is not exist", "code": "ML_MODEL_NOT_EXIST"},
        )

    if db_ml_model.default_model:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Delete ml model",
                username=current_user.username,
                project="",
                description="The default ML model cannot be deleted",
                code="DEFAULT_ML_MODEL_CANNOT_BE_DELETED",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "The default ML model cannot be deleted",
                "code": "DEFAULT_ML_MODEL_CANNOT_BE_DELETED",
            },
        )

    status_code = unload_ml_model_triton_service(
        project_type=db_ml_model.type_of_data[0], name=db_ml_model.link, db=db
    )

    if not status_code or status_code != 200:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Delete ml model",
                username=current_user.username,
                project="",
                description=f"Failed to unload the {db_ml_model.name} model from the triton server",
                code="UNLOAD_MODEL_ERROR",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"Failed to unload the {db_ml_model.name} model from the triton server",
                "code": "UNLOAD_MODEL_ERROR",
            },
        )
    db_ml_model = delete_ml_model_by_id_service(id=db_ml_model.id, db=db)
    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action="Delete ml models",
            username=current_user.username,
            project=db_ml_model.name,
            description=f"Deleted {db_ml_model.name}",
        ),
        owner_id=current_user.id,
        db=db,
    )
    return {"status": "ok"}


@router.post("/create-ml-classes")
def create_ml_classes(
    id: int,
    type: TypeMLModelEnum,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> MLModelSchemas:
    db_ml_model = get_ml_model_by_id_service(id=id, db=db)
    if not db_ml_model:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Create ml classes",
                username=current_user.username,
                project="",
                description="ML model is not exist",
                code="ML_MODEL_NOT_EXIST",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "ML model is not exist", "code": "ML_MODEL_NOT_EXIST"},
        )

    classes = get_ml_classes_by_name_service(name=type, db=db)
    db_ml_model = update_type_of_objects_ml_model_service(
        id=db_ml_model.id, type_of_objects=classes, db=db
    )
    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action=f"Added classes for {db_ml_model.name}",
            username=current_user.username,
            project=db_ml_model.name,
            description="",
        ),
        owner_id=current_user.id,
        db=db,
    )
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


@router.get("/get-ml-models-by-types")
def get_ml_models_by_types(
    type: TypeMLModelEnum,
    view: ViewMLModelEnum,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> List[MLModelSchemas]:
    if type not in [i.value for i in TypeMLModelEnum]:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Get ml model by types",
                username=current_user.username,
                project="",
                description="ML type is not exist",
                code="ML_TYPE_NOT_EXIST",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "ML type is not exist", "code": "ML_TYPE_NOT_EXIST"},
        )
    db_ml_model = get_ml_model_by_type_of_data_service(type=type, view=view, db=db)
    return [
        MLModelSchemas(
            id=i.id,
            name=i.name,
            type_of_data=i.type_of_data,
            type_of_objects=i.type_of_objects,
            default_model=i.default_model,
            task_id=i.task_id,
            task_result=i.task_result,
            status=i.status,
            created_at=i.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            mlflow_url=i.ml_flow_url,
            created_by=i.created_by,
        )
        for i in db_ml_model
        if i.status == StatusModelEnum.ready_to_use
    ]


@router.post("/train")
def train_model(
    params: TrainMLModelSchemas,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> TaskIdSchemas:
    db_ml_model = get_ml_model_by_id_service(id=params.id, db=db)
    if not db_ml_model:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Train",
                username=current_user.username,
                project="",
                description="ML model is not exist",
                code="ML_MODEL_NOT_EXIST",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "ML model is not exist", "code": "ML_MODEL_NOT_EXIST"},
        )
    change_status_ml_model_service(
        id=db_ml_model.id, status=StatusModelEnum.in_the_training, db=db
    )
    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action=f"Train ml model type of {params.type_model}",
            username=current_user.username,
            project=db_ml_model.name,
            description="",
        ),
        owner_id=current_user.id,
        db=db,
    )
    change_ml_classes_by_id_service(id=db_ml_model.id, classes=params.classes, db=db)
    # get_user_by_id_service(id=current_user.id)
    task = train_ml_model_task.apply_async(
        args=(
            params.id,
            params.epochs,
            params.scale_factor,
            params.type_model,
            db_ml_model.type_of_data[0],
            params.classes,
            f"{db_ml_model.id}/{db_ml_model.link}",
        )
    )
    add_ml_model_task_id_service(id=db_ml_model.id, task_id=task.id, db=db)
    return TaskIdSchemas(
        task_id=task.id,
        project_id=db_ml_model.id,
        task_name="traning_ml_model_task",
        task_status=task.status,
    )


@router.post("/save-ml-model")
def save_ml_models(
    id: int,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> TaskIdSchemas:
    db_ml_model = get_ml_model_by_id_service(id=id, db=db)

    if not db_ml_model:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Save ml model",
                username=current_user.username,
                project="",
                description="ML model is not exist",
                code="ML_MODEL_NOT_EXIST",
            ),
            owner_id=current_user.id,
            db=db,
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "ML model is not exist", "code": "ML_MODEL_NOT_EXIST"},
        )
    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action="Finish training ml model",
            username=current_user.username,
            project=db_ml_model.name,
            description="",
        ),
        owner_id=current_user.id,
        db=db,
    )
    task = save_ml_model_task.apply_async(args=(id, db_ml_model.experiment_name))
    add_ml_model_task_id_service(id=db_ml_model.id, task_id=task.id, db=db)

    return TaskIdSchemas(
        task_id=task.id,
        project_id=db_ml_model.id,
        task_name="save_ml_model_task",
        task_status=task.status,
    )


@router.get("get-mlflow-address")
def get_mlflow_address(
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> Dict[str, str]:
    if settings.MLFLOW_PROD:
        url = settings.MLFLOW_PROD_URL
    else:
        url = f"{settings.ML_SERVER_URL}:{settings.ML_MLFLOW_PORT}"
    return {"url": url}


@router.get("get-mlflow-type-model")
def get_mlflow_type_model(
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> List[str]:
    return [i.value for i in TypeMlModelTrainingEnum]
