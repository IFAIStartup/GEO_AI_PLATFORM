from typing import Dict, List, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from celery.result import AsyncResult
from geo_ai_backend.auth.permissions import get_current_user_from_access
from geo_ai_backend.auth.schemas import UserServiceSchemas
from geo_ai_backend.database import get_db
from geo_ai_backend.ml.schemas import (
    TaskIdsSchemas,
    GetTaskResultSchemas,
    GetFoldersNextcloudSchemas,
)
from geo_ai_backend.project.worker import (
    create_comparing_task,
    get_project_files_service_task,
)
from geo_ai_backend.project.utils import (
    check_folder_nextcloud_exists,
    validation_360,
    validation_aerial,
    validation_sattelite,
)
from geo_ai_backend.project.schemas import (
    CreateProjectSchemas,
    DeleteProjectSchemas,
    ProjectSchemas,
    ProjectsSchemas,
    SortKeyEnum,
    StatusProjectEnum,
    TypeProjectEnum,
    CompareProjectSchemas,
    SortCompareKeyEnum,
    CompareProjectsSchemas,
    CompareProjectObj,
)
from geo_ai_backend.project.service import (
    change_status_project_service,
    create_project_service,
    delete_project_by_id_service,
    get_project_by_id_service,
    get_projects_by_ids_service,
    get_project_by_name_service,
    get_projects_service,
    get_compare_projects_by_id_service,
    delete_compare_projects_by_id_service,
    change_status_compare_project_service,
    get_compare_projects_by_task_id_service,
    change_task_id_compare_projects_service,
    create_compare_project_service,
    add_task_result_compare_projects_service,
    get_all_compare_projects_service,
    get_nextcloud_folders_service,
    get_folders_by_type_service,
)
from geo_ai_backend.history.service import (
    create_action_history_service,
    create_error_history_service,
)
from geo_ai_backend.history.schemas import (
    CreateActionHistorySchemas,
    CreateErrorHistorySchemas,
)


router = APIRouter(
    prefix="/project",
    tags=["project"],
)


@router.get("/tasks/{task_id}", response_model=GetTaskResultSchemas)
async def get_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> GetTaskResultSchemas:
    task_result = AsyncResult(task_id)
    return GetTaskResultSchemas(
        task_id=task_result.task_id,
        task_status=task_result.status,
        task_result=task_result.result,
    )


@router.post(
    "/create-project",
    response_model=Dict[str, Union[ProjectSchemas, str]],
    responses={
        400: {
            "description": "Project name already exists",
            "content": {
                "application/json": {
                    "example": {"detail": "Project name already exists"}
                }
            },
        }
    },
)
async def create_project(
    params: CreateProjectSchemas,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> Dict[str, Union[ProjectSchemas, str]]:
    db_project = get_project_by_name_service(name=params.name, db=db)
    if db_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Project name already exist", "code": "PROJECT_EXIST"},
        )

    if not check_folder_nextcloud_exists(folder=params.link):
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Create project",
                username=current_user.username,
                project=params.name,
                description=f"Nextcloud folder '{params.link}' is not exist",
                code="FOLDER_NOT_EXIST",
                project_type="PROJECT",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"Nextcloud folder '{params.link}' is not exist",
                "code": "FOLDER_NOT_EXIST",
            },
        )
    if params.type == TypeProjectEnum.aerial_images:
        checked = validation_aerial(folder=params.link)
        if not checked[0]:
            create_error_history_service(
                error_history=CreateErrorHistorySchemas(
                    user_action="Create project",
                    username=current_user.username,
                    project=params.name,
                    description=checked[1]["message"],
                    code=checked[1]["code"],
                    project_type="PROJECT",
                ),
                owner_id=current_user.id,
                db=db,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": checked[1]["message"],
                    "code": checked[1]["code"],
                },
            )
    if params.type == TypeProjectEnum.satellite_images:
        checked = validation_sattelite(folder=params.link)
        if not checked[0]:
            create_error_history_service(
                error_history=CreateErrorHistorySchemas(
                    user_action="Create project",
                    username=current_user.username,
                    project=params.name,
                    description=checked[1]["message"],
                    code=checked[1]["code"],
                    project_type="PROJECT",
                ),
                owner_id=current_user.id,
                db=db,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": checked[1]["message"],
                    "code": checked[1]["code"],
                },
            )
    if params.type == TypeProjectEnum.panorama_360:
        checked = validation_360(folder=params.link)
        if not checked[0]:
            create_error_history_service(
                error_history=CreateErrorHistorySchemas(
                    user_action="Create project",
                    username=current_user.username,
                    project=params.name,
                    description=checked[1]["message"],
                    code=checked[1]["code"],
                    project_type="PROJECT",
                ),
                owner_id=current_user.id,
                db=db,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": checked[1]["message"],
                    "code": checked[1]["code"],
                },
            )
    project = create_project_service(
        project=params,
        username=current_user.username,
        owner_id=current_user.id,
        db=db,
    )
    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action="Create project",
            username=current_user.username,
            project=project.name,
            description=f"Type of project: {project.type}",
            project_id=project.id,
            project_type="PROJECT",
        ),
        owner_id=current_user.id,
        db=db,
    )
    task = get_project_files_service_task.apply_async(
        args=(
            project.id,
            project.type,
            project.link,
            project.name,
            current_user.username,
            current_user.id,
        )
    )
    return {"project": project, "task_id": task.id}


@router.post("/delete-project", response_model=DeleteProjectSchemas)
async def delete_project_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> DeleteProjectSchemas:
    db_project = get_project_by_id_service(id=id, db=db)
    if not db_project:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Delete project",
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
    if db_project.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Permission denied", "code": "PERMISSION_DENIED"},
        )
    db_project = delete_project_by_id_service(id=id, db=db)
    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action="Delete project",
            username=current_user.username,
            project=db_project.name,
            description=f"Type of project: {db_project.type}",
            project_type="PROJECT",
        ),
        owner_id=current_user.id,
        db=db,
    )
    return DeleteProjectSchemas(
        status=status.HTTP_200_OK,
        project=db_project,
    )


@router.post("/change-status-project", response_model=ProjectSchemas)
async def change_status_project(
    id: int,
    status_project: StatusProjectEnum,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> ProjectSchemas:
    db_project = get_project_by_id_service(id=id, db=db)
    if not db_project:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Change status project",
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
    if db_project.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Permission denied", "code": "PERMISSION_DENIED"},
        )
    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action="Change status project",
            username=current_user.username,
            project=db_project.name,
            description="",
            project_id=db_project.id,
            project_type="PROJECT",
        ),
        owner_id=current_user.id,
        db=db,
    )
    return change_status_project_service(id=id, status=status_project, db=db)


@router.get("/get-projects", response_model=ProjectsSchemas)
async def get_projects(
    search: str = "",
    filter: TypeProjectEnum = TypeProjectEnum.all,
    sort: SortKeyEnum = SortKeyEnum.date,
    reverse: bool = False,
    page: int = 1,
    limit: int = Query(default=10, lte=10),
    is_completed: bool = False,
    include_result: bool = False,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> ProjectsSchemas:
    return get_projects_service(
        search=search,
        filter=filter,
        sort=sort,
        reverse=reverse,
        page=page,
        limit=limit,
        is_completed=is_completed,
        include_result=include_result,
        owner_id=current_user.id,
        owner_role=current_user.role,
        db=db,
    )


@router.get("/get-project", response_model=ProjectSchemas)
async def get_project(
    id: int,
    db: Session = Depends(get_db),
    include_result: bool = False,
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> ProjectSchemas:
    db_project = get_project_by_id_service(id=id, db=db)
    if not db_project:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Get project",
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
    if db_project.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Permission denied", "code": "PERMISSION_DENIED"},
        )
    task_result = db_project.task_result
    if not include_result:
        task_result = None

    return ProjectSchemas(
        id=db_project.id,
        name=db_project.name,
        date=db_project.date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        link=db_project.link,
        type=db_project.type,
        status=db_project.status,
        created_at=db_project.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        detection_id=db_project.detection_id,
        preview_layer_id=db_project.preview_layer_id,
        task_result=task_result,
        input_files=db_project.input_files,
        ml_model=db_project.ml_model,
        ml_model_deeplab=db_project.ml_model_deeplab,
        created_by=db_project.created_by,
        error_code=db_project.error_code,
        description=db_project.description,
        classes=db_project.classes,
        super_resolution=db_project.super_resolution,
        owner_id=db_project.owner_id,
    )


@router.post("/compare-projects", response_model=TaskIdsSchemas)
async def comparison_projects(
    id: List[int],
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> TaskIdsSchemas:
    db_projects = get_projects_by_ids_service(ids=id, db=db)
    if not db_projects:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Compare projects",
                username=current_user.username,
                project=f"{db_projects[0].name} and {db_projects[1].name}",
                description="Project is not exist",
                code="PROJECT_NOT_EXIST",
                project_type="PROJECT_COMPARE",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Project is not exist", "code": "PROJECT_NOT_EXIST"},
        )
    if (
        db_projects[0].owner_id != current_user.id
        and db_projects[1].owner_id != current_user.id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Permission denied", "code": "PERMISSION_DENIED"},
        )
    elif len(db_projects) > 2:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Compare projects",
                username=current_user.username,
                project=f"{db_projects[0].name} and {db_projects[1].name}",
                description="Only 2 projects are involved in the comparison",
                code="TWO_PROJECTS_COMPARE",
                project_type="PROJECT_COMPARE",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Only 2 projects are involved in the comparison",
                "code": "TWO_PROJECTS_COMPARE",
            },
        )
    elif len(set([i.type for i in db_projects])) != 1:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Compare projects",
                username=current_user.username,
                project=f"{db_projects[0].name} and {db_projects[1].name}",
                description="Different types of projects",
                code="DIFFERENT_PROJECT_TYPES",
                project_type="PROJECT_COMPARE",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Different types of projects",
                "code": "DIFFERENT_PROJECT_TYPES",
            },
        )
    elif len(set([i.id for i in db_projects])) == 1:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Compare projects",
                username=current_user.username,
                project=f"{db_projects[0].name} and {db_projects[1].name}",
                description="Can't compare the same project",
                code="SAME_PROJECTS",
                project_type="PROJECT_COMPARE",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Can't compare the same project",
                "code": "SAME_PROJECTS",
            },
        )

    if db_projects[0].date > db_projects[1].date:
        db_projects[0], db_projects[1] = db_projects[1], db_projects[0]
        id[0], id[1] = id[1], id[0]

    paths_images = [
        db_projects[number].task_result["path_images"] for number in range(2)
    ]

    compare_projects = create_compare_project_service(
        project_1=db_projects[0].name,
        project_2=db_projects[1].name,
        shooting_date_1=db_projects[0].date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        shooting_date_2=db_projects[1].date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        type=db_projects[0].type,
        status=StatusProjectEnum.in_progress,
        owner_id=current_user.id,
        db=db,
    )

    task = create_comparing_task.apply_async(
        args=(
            paths_images,
            id,
            db_projects[0].type,
            compare_projects.id,
            current_user.username,
            current_user.id,
        )
    )
    change_task_id_compare_projects_service(
        id=compare_projects.id, task_id=task.id, db=db
    )

    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action="Start comparing of projects",
            username=current_user.username,
            project=", ".join(i.name for i in db_projects),
            description=f"comparison of two {db_projects[0].type}-type projects",
            project_id=compare_projects.id,
        ),
        owner_id=current_user.id,
        db=db,
    )

    return TaskIdsSchemas(
        task_id=task.id,
        project_ids=compare_projects.id,
        task_name="compare_task",
        task_status=task.status,
    )


@router.get(
    "/get-compare-projects",
    response_model=CompareProjectSchemas,
)
async def get_compare_projects(
    id: int,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> CompareProjectSchemas:
    db_compare_projects = get_compare_projects_by_id_service(id=id, db=db)
    if not db_compare_projects:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Get compare projects",
                username=current_user.username,
                project=f"{db_compare_projects.project_1} and {db_compare_projects.project_2}",
                description="Can't compare the same project",
                code="SAME_PROJECTS",
                project_type="PROJECT_COMPARE",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Project is not exist", "code": "PROJECT_NOT_EXIST"},
        )
    if db_compare_projects.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Permission denied", "code": "PERMISSION_DENIED"},
        )
    return CompareProjectSchemas(
        id=db_compare_projects.id,
        project_1=CompareProjectObj(
            name=db_compare_projects.project_1,
            date=db_compare_projects.shooting_date_1,
        ),
        project_2=CompareProjectObj(
            name=db_compare_projects.project_2,
            date=db_compare_projects.shooting_date_2,
        ),
        type=db_compare_projects.type,
        status=db_compare_projects.status,
        task_id=db_compare_projects.task_id,
        task_result=db_compare_projects.task_result,
        created_at=db_compare_projects.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        owner_id=db_compare_projects.owner_id
    )


@router.get("/get-all-compare-projects", response_model=CompareProjectsSchemas)
async def get_all_compare_projects_projects(
    search: str = "",
    filter: TypeProjectEnum = TypeProjectEnum.all,
    sort: SortCompareKeyEnum = SortCompareKeyEnum.default,
    reverse: bool = False,
    page: int = 1,
    limit: int = Query(default=10, lte=10),
    include_result: bool = False,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> CompareProjectsSchemas:
    return get_all_compare_projects_service(
        search=search,
        filter=filter,
        sort=sort,
        reverse=reverse,
        page=page,
        limit=limit,
        include_result=include_result,
        owner_id=current_user.id,
        owner_role=current_user.role,
        db=db,
    )


@router.post(
    "/delete-compare-projects",
    response_model=CompareProjectSchemas,
)
async def delete_compare_projects(
    id: int,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> CompareProjectSchemas:
    db_compare_projects = get_compare_projects_by_id_service(id=id, db=db)
    if not db_compare_projects:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Delete compare projects",
                username=current_user.username,
                project=f"{db_compare_projects.project_1} and {db_compare_projects.project_2}",
                description="Projects is not exists",
                code="PROJECTS_NOT_EXISTS",
                project_type="PROJECT_COMPARE",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Project is not exist", "code": "PROJECT_NOT_EXIST"},
        )
    if db_compare_projects.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Permission denied", "code": "PERMISSION_DENIED"},
        )
    db_compare_projects = delete_compare_projects_by_id_service(id=id, db=db)
    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action="Delete compare projects",
            username=current_user.username,
            project=f"{db_compare_projects.project_1} - {db_compare_projects.project_2}",
            description=f"Type of project: {db_compare_projects.type}",
            project_id=db_compare_projects.id,
            project_type="PROJECT_COMPARE",
        ),
        owner_id=current_user.id,
        db=db,
    )
    return db_compare_projects


@router.post("/change-status-compare-project", response_model=CompareProjectSchemas)
async def change_status_compare_projects(
    id: int,
    status_compare: StatusProjectEnum,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> CompareProjectSchemas:
    db_compare_projects = get_compare_projects_by_id_service(id=id, db=db)
    if not db_compare_projects:
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Change status compare projects",
                username=current_user.username,
                project=f"{db_compare_projects.project_1} and {db_compare_projects.project_2}",
                description="Project is not exist",
                code="PROJECT_NOT_EXIST",
                project_type="PROJECT_COMPARE",
            ),
            owner_id=current_user.id,
            db=db,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Project is not exist", "code": "PROJECT_NOT_EXIST"},
        )
    if db_compare_projects.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Permission denied", "code": "PERMISSION_DENIED"},
        )
    create_action_history_service(
        action_history=CreateActionHistorySchemas(
            user_action="Change status project",
            username=current_user.username,
            project=f"{db_compare_projects.project_1} - {db_compare_projects.project_2}",
            description="",
            project_id=db_compare_projects.id,
            project_type="PROJECT_COMPARE",
        ),
        owner_id=current_user.id,
        db=db,
    )
    return change_status_compare_project_service(id=id, status=status_compare, db=db)


@router.get("/tasks_compare/{task_id}", response_model=GetTaskResultSchemas)
async def get_status_compare(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> GetTaskResultSchemas:
    task_result = AsyncResult(task_id)
    db_compare_projects = get_compare_projects_by_task_id_service(
        task_id=task_id, db=db
    )
    if task_result.status == "SUCCESS":
        add_task_result_compare_projects_service(
            id=db_compare_projects.id, task_result=task_result.result, db=db
        )
        change_status_compare_project_service(
            id=db_compare_projects.id, status=StatusProjectEnum.completed, db=db
        )
        create_action_history_service(
            action_history=CreateActionHistorySchemas(
                user_action="End of comparing",
                username=current_user.username,
                project=f"{db_compare_projects.project_1} - {db_compare_projects.project_2}",
                description="Status change from 'In progress' to 'Completed'",
                project_id=db_compare_projects.id,
                project_type="PROJECT_COMPARE",
            ),
            owner_id=current_user.id,
            db=db,
        )

    if task_result.status == "FAILURE":
        add_task_result_compare_projects_service(
            id=db_compare_projects.id, task_result=None, db=db
        )
        change_status_compare_project_service(
            id=db_compare_projects.id,
            status=StatusProjectEnum.error,
            db=db,
            description="Comparing failed with an error",
            error_code="TASK_COMPARE_FAILED",
        )
        create_error_history_service(
            error_history=CreateErrorHistorySchemas(
                user_action="Comparing failed with an error",
                username=current_user.username,
                project=f"{db_compare_projects.project_1} and {db_compare_projects.project_2}",
                description="Status change from 'In progress' to 'Error'",
                code="TASK_COMPARE_FAILED",
                project_id=db_compare_projects.id,
                project_type="PROJECT_COMPARE",
            ),
            owner_id=current_user.id,
            db=db,
        )

    return GetTaskResultSchemas(
        task_id=task_result.task_id,
        task_status=task_result.status,
        task_result=task_result.result,
    )


@router.get("/folder_nextcloud_project", response_model=GetFoldersNextcloudSchemas)
async def get_nextcloud_folders_project(
    type_folder: TypeProjectEnum,
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> GetFoldersNextcloudSchemas:
    names_folder = get_nextcloud_folders_service()
    return GetFoldersNextcloudSchemas(links=names_folder)


@router.get("/folder_nextcloud_ml", response_model=GetFoldersNextcloudSchemas)
async def get_nextcloud_folders_ml(
    db: Session = Depends(get_db),
    current_user: UserServiceSchemas = Depends(get_current_user_from_access),
) -> GetFoldersNextcloudSchemas:
    names_folder = get_nextcloud_folders_service()
    return GetFoldersNextcloudSchemas(links=names_folder)
