import os
import math
from typing import List, Dict, Any, Generator, Optional, Tuple
import re
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from collections import Counter
from geo_ai_backend.arcgis.service import gis_service
from geo_ai_backend.ml.exceptions import NextcloudNotFoundFolders
from geo_ai_backend.ml.ml_models.aerial_satellite.inference.get_geo_data import (
    get_all_geo_data,
    create_csv_file,
)
from geo_ai_backend.ml.ml_models.aerial_satellite.inference.jpg2geotif import (
    create_geotiff,
)
from geo_ai_backend.project.exceptions import (
    EmptyNextcloudFolderException,
    NotFoundFileNextcloudException,
    IncorrectFormatCsvOrJpgException,
)
from geo_ai_backend.project.models import Projects, CompareProjects
from geo_ai_backend.project.schemas import (
    FieldNameEnum,
    FieldNameInputEnum,
    CreateProjectSchemas,
    ProjectFilesSchemas,
    ProjectSchemas,
    ProjectsSchemas,
    TypeProjectEnum,
    AerialImagesFileSchemas,
    Panorama360FileSchemas,
    Panorama360FilesSchemas,
    CompareProjectSchemas,
    StatusProjectEnum,
    CompareProjectsSchemas,
    CompareProjectObj,
)
from geo_ai_backend.utils import (
    delete_file,
    delete_dir,
    create_dir,
    get_jpg_from_tif,
    CSVReader,
    CSVWriter,
)
from geo_ai_backend.project.utils import (
    download_files_from_nextcloud,
    prepare_data_for_csv,
)
import glob


def get_project_by_name_service(name: str, db: Session) -> Projects:
    db_project = db.query(Projects).filter(Projects.name == name).first()
    return db_project


def get_project_by_id_service(id: int, db: Session) -> Projects:
    db_project = db.query(Projects).filter(Projects.id == id).first()
    return db_project


def get_projects_by_ids_service(ids: List[int], db: Session) -> List[Projects]:
    db_project = db.query(Projects).filter(Projects.id.in_(ids)).all()
    return db_project


def get_project_by_detection_id(id: str, db: Session) -> Projects:
    db_project = db.query(Projects).filter(Projects.detection_id == id).first()
    return db_project


def get_project_by_preview_layer_id(id: str, db: Session) -> Projects:
    db_project = db.query(Projects).filter(Projects.preview_layer_id == id).first()
    return db_project


def get_projects_by_type_service(type: str, db: Session) -> List[Projects]:
    db_project = db.query(Projects).filter(Projects.type == type)
    return db_project


def get_projects_by_ids_limit(db: Session, limit: int = 15) -> List[Projects]:
    sort_field = Projects.id
    project_table = db.query(Projects)
    project_table = project_table.order_by(desc(sort_field))
    db_projects = project_table.limit(limit).all()
    return db_projects


def delete_project_by_id_service(id: int, db: Session) -> ProjectSchemas:
    db_project = db.query(Projects).filter(Projects.id == id).first()
    db.delete(db_project)
    db.commit()
    delete_dir(f"static/{id}")
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
        task_result=db_project.task_result,
        ml_model=db_project.ml_model,
        ml_model_deeplab=db_project.ml_model_deeplab,
        created_by=db_project.created_by,
        error_code=db_project.error_code,
        description=db_project.description,
        classes=db_project.classes,
        super_resolution=db_project.super_resolution,
        owner_id=db_project.owner_id,
    )


def change_status_project_service(
    id: int,
    status: str,
    db: Session,
    description: Optional[str] = None,
    error_code: Optional[str] = None,
) -> ProjectSchemas:
    db_project = db.query(Projects).filter(Projects.id == id).first()
    db_project.status = status
    if error_code:
        db_project.description = description
        db_project.error_code = error_code
    db.commit()
    db.refresh(db_project)
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
        task_result=db_project.task_result,
        ml_model=db_project.ml_model,
        ml_model_deeplab=db_project.ml_model_deeplab,
        created_by=db_project.created_by,
        error_code=db_project.error_code,
        description=db_project.description,
        classes=db_project.classes,
        super_resolution=db_project.super_resolution,
        owner_id=db_project.owner_id,
    )


def change_detection_id_service(
    id: int, detection_id: str, db: Session
) -> ProjectSchemas:
    db_project = db.query(Projects).filter(Projects.id == id).first()
    db_project.detection_id = detection_id
    db.commit()
    db.refresh(db_project)
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
        task_result=db_project.task_result,
        ml_model=db_project.ml_model,
        ml_model_deeplab=db_project.ml_model_deeplab,
        created_by=db_project.created_by,
        error_code=db_project.error_code,
        description=db_project.description,
        classes=db_project.classes,
        super_resolution=db_project.super_resolution,
        owner_id=db_project.owner_id,
    )


def change_preview_layer_id(
    id: int, preview_layer_id: str, db: Session
) -> ProjectSchemas:
    db_project = db.query(Projects).filter(Projects.id == id).first()
    db_project.preview_layer_id = preview_layer_id
    db.commit()
    db.refresh(db_project)
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
        task_result=db_project.task_result,
        ml_model=db_project.ml_model,
        ml_model_deeplab=db_project.ml_model_deeplab,
        created_by=db_project.created_by,
        error_code=db_project.error_code,
        description=db_project.description,
        classes=db_project.classes,
        super_resolution=db_project.super_resolution,
        owner_id=db_project.owner_id,
    )


def create_project_service(
    project: CreateProjectSchemas, username: str, owner_id: int, db: Session
) -> ProjectSchemas:
    db_project = Projects(
        name=project.name,
        link=project.link,
        type=project.type,
        date=project.date,
        created_by=username,
        owner_id=owner_id,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return ProjectSchemas(
        id=db_project.id,
        name=db_project.name,
        link=db_project.link,
        type=db_project.type,
        status=db_project.status,
        date=db_project.date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        created_at=db_project.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        detection_id=db_project.detection_id,
        preview_layer_id=db_project.preview_layer_id,
        task_result=db_project.task_result,
        ml_model=db_project.ml_model,
        ml_model_deeplab=db_project.ml_model_deeplab,
        created_by=db_project.created_by,
        error_code=db_project.error_code,
        description=db_project.description,
        classes=db_project.classes,
        super_resolution=db_project.super_resolution,
        owner_id=db_project.owner_id,
    )


def get_projects_service(
    search: str,
    filter: str,
    sort: str,
    reverse: bool,
    page: int,
    limit: int,
    is_completed: bool,
    include_result: bool,
    owner_id: int,
    owner_role: str,
    db: Session,
) -> ProjectsSchemas:
    project_table = db.query(Projects)
    if owner_role != "admin":
        project_table = project_table.filter(Projects.owner_id == owner_id)

    if is_completed:
        project_table = project_table.filter(
            Projects.status == StatusProjectEnum.completed
        )

    if search:
        project_table = project_table.filter(Projects.name.like(f"%{search}%"))

    if filter != TypeProjectEnum.all:
        project_table = project_table.filter(Projects.type == filter)

    total = len(project_table.all())
    offset = (page - 1) * limit
    pages = math.ceil(total / limit) if total else 0

    sort_field = Projects.date
    if sort == "name":
        sort_field = Projects.name
    elif sort == "created_at":
        sort_field = Projects.created_at
    elif sort == "created_by":
        sort_field = Projects.created_by

    if not reverse:
        project_table = project_table.order_by(desc(sort_field))
    else:
        project_table = project_table.order_by(asc(sort_field))

    db_projects = project_table.offset(offset).limit(limit).all()

    if not db_projects:
        return ProjectsSchemas(
            projects=[], page=page, pages=pages, total=total, limit=limit
        )

    projects_list = [
        {
            "id": i.id,
            "name": i.name,
            "date": i.date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "link": i.link,
            "type": i.type,
            "status": i.status,
            "created_at": i.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "detection_id": i.detection_id,
            "preview_layer_id": i.preview_layer_id,
            "task_result": i.task_result if include_result else None,
            "ml_model": i.ml_model,
            "ml_model_deeplab": i.ml_model_deeplab,
            "created_by": i.created_by,
            "error_code": i.error_code,
            "description": i.description,
            "classes": i.classes,
            "super_resolution": i.super_resolution,
            "owner_id": i.owner_id,
        }
        for i in db_projects
    ]

    projects = [ProjectSchemas(**i) for i in projects_list]
    return ProjectsSchemas(
        projects=projects,
        page=page,
        pages=pages,
        total=total,
        limit=limit,
    )


def filter_files_aerial_satellite_service(
    names_files: List[str],
    prepared_files: List[str],
    filetypes: List[str],
) -> Tuple[List[str], List[str]]:
    unique_filtered_names_files = []
    unique_filtered_prepared_files = []

    counter = Counter(names_files)
    miss_files = check_missing_files_service(
        names_files=names_files,
        prepared_files=prepared_files,
        filetypes=filetypes,
        counter=counter,
    )

    if miss_files:
        raise NotFoundFileNextcloudException(filenames=miss_files)

    filtered_names_files = [item for item, count in counter.items() if count == 3]
    filtered_prepared_files = [
        prepared_files[i]
        for i in range(len(names_files))
        if counter[names_files[i]] == 3
    ]

    for i in range(len(filtered_names_files)):
        if filtered_names_files[i] not in unique_filtered_names_files:
            unique_filtered_names_files.append(filtered_names_files[i])

    for i in range(len(filtered_prepared_files)):
        if filtered_prepared_files[i] not in unique_filtered_prepared_files:
            unique_filtered_prepared_files.append(filtered_prepared_files[i])

    return unique_filtered_names_files, unique_filtered_prepared_files


def check_missing_files_service(
    names_files: List[str],
    prepared_files: List[str],
    filetypes: List[str],
    counter: Counter,
) -> str:

    filtered_names_files = [item for item, count in counter.items() if count != 3]
    filtered_prepared_files = [
        prepared_files[i]
        for i in range(len(names_files))
        if counter[names_files[i]] != 3
    ]
    miss_files = []
    for name in filtered_names_files:
        for my_type in filetypes[1:]:
            if name + my_type not in filtered_prepared_files:
                miss_files.append(name + my_type)
    result = ", ".join(miss_files)
    return result


def filter_filetypes_aerial_satellite_service(
    files: List[str], filetypes: List[str]
) -> Tuple[List[str], List[str]]:
    prepared_files = []
    names_files = []
    for file in files:
        for i in range(1, 4):
            if file.endswith(filetypes[i]):
                names_files.append(file.rsplit(filetypes[i])[0])
                prepared_files.append(file)
    return names_files, prepared_files


def get_paths_superresolution_service(
    save_path_prepare: str, path_tif: List[str]
) -> List[str]:
    if os.listdir(save_path_prepare):
        files = sorted(os.listdir(save_path_prepare))
        filetypes = [".tif", ".jpg", ".jgw", ".jpg.aux.xml"]
        (names_files, prepared_files) = filter_filetypes_aerial_satellite_service(
            files=files, filetypes=filetypes
        )
        names_files, prepared_files = filter_files_aerial_satellite_service(
            names_files=names_files, prepared_files=prepared_files, filetypes=filetypes
        )
        paths_jpg = []
        uniq_paths = []
        for path in path_tif:
            for name in names_files:
                if name not in os.path.basename(path.rsplit(".tif")[0]):
                    uniq_paths.append(path)
                else:
                    paths_jpg.append(
                        f"{os.path.dirname(os.path.dirname(path))}/prepared/{name}.jpg"
                    )

        return uniq_paths + paths_jpg
    return path_tif


def check_update_nextcloud_folder_service(
    project_id: int, project_type: str, folder: str
) -> None:
    path = f"static/{project_id}/{project_type}"
    filetypes = [None]
    folder_type = False
    save_path = path
    save_path_prepare = None
    if (
        project_type == TypeProjectEnum.aerial_images
        or project_type == TypeProjectEnum.satellite_images
    ):
        filetypes = [".tif", ".jpg", ".jgw", ".jpg.aux.xml"]
        save_path = f"{path}/tif"
        save_path_prepare = f"{path}/prepared"
    elif project_type == TypeProjectEnum.panorama_360:
        filetypes = [".csv"]
        folder_type = True
        save_path = path

    download_status = download_files_from_nextcloud(
        folder=folder,
        save_path=save_path,
        save_path_prepare=save_path_prepare,
        filetypes=filetypes,
        folder_type=folder_type,
    )

    if not download_status:
        raise EmptyNextcloudFolderException

    if (
        project_type == TypeProjectEnum.aerial_images
        or project_type == TypeProjectEnum.satellite_images
    ):
        if os.listdir(save_path_prepare):
            files = sorted(os.listdir(save_path_prepare))

            (names_files, prepared_files) = filter_filetypes_aerial_satellite_service(
                files=files, filetypes=filetypes
            )
            (names_files, prepared_files) = filter_files_aerial_satellite_service(
                names_files=names_files,
                prepared_files=prepared_files,
                filetypes=filetypes,
            )
            for i in range(len(prepared_files))[::3]:
                create_geotiff(
                    jpg_path=os.path.join(save_path_prepare, prepared_files[i + 1]),
                    jgw_path=os.path.join(save_path_prepare, prepared_files[i]),
                    aux_xml_path=os.path.join(save_path_prepare, prepared_files[i + 2]),
                    save_tif_path=f"{path}/tif/{names_files[i//3]}.tif",
                )

        path_img_dir = f"{path}/images"
        create_dir(path=path_img_dir)
        files = [
            os.path.join(save_path, i)
            for i in os.listdir(save_path)
            if os.path.splitext(i)[-1] == ".tif"
        ]
        for file in files:
            get_jpg_from_tif(
                path_tif=file,
                path_img_save=path_img_dir,
            )


def add_preview_selected_images(
    id: int, images: List[str], db: Session
) -> ProjectSchemas:
    db_project = db.query(Projects).filter(Projects.id == id).first()
    db_project.preview_selected_images = images
    db.commit()
    db.refresh(db_project)
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
        task_result=db_project.task_result,
        ml_model=db_project.ml_model,
        ml_model_deeplab=db_project.ml_model_deeplab,
        created_by=db_project.created_by,
        error_code=db_project.error_code,
        description=db_project.description,
        classes=db_project.classes,
        super_resolution=db_project.super_resolution,
    )


def add_task_result(
    id: int,
    task_result: Dict[str, Any],
    db: Session,
) -> ProjectSchemas:
    db_project = db.query(Projects).filter(Projects.id == id).first()
    db_project.task_result = task_result
    db.commit()
    db.refresh(db_project)
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
        task_result=db_project.task_result,
        ml_model=db_project.ml_model,
        ml_model_deeplab=db_project.ml_model_deeplab,
        created_by=db_project.created_by,
        error_code=db_project.error_code,
        description=db_project.description,
        classes=db_project.classes,
        super_resolution=db_project.super_resolution,
    )


def add_input_files_service(
    id: int,
    input_files: Dict[str, Any],
    db: Session,
) -> ProjectSchemas:
    db_project = db.query(Projects).filter(Projects.id == id).first()
    db_project.input_files = input_files
    db.commit()
    db.refresh(db_project)
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
        task_result=db_project.task_result,
        input_files=db_project.input_files,
        ml_model=db_project.ml_model,
        ml_model_deeplab=db_project.ml_model_deeplab,
        created_by=db_project.created_by,
        error_code=db_project.error_code,
        description=db_project.description,
        classes=db_project.classes,
        super_resolution=db_project.super_resolution,
    )


def add_project_classes_sr_service(
    id: int,
    classes: List[str],
    super_resolution: str,
    db: Session,
) -> ProjectSchemas:
    db_project = db.query(Projects).filter(Projects.id == id).first()
    db_project.classes = classes
    db_project.super_resolution = super_resolution
    db.commit()
    db.refresh(db_project)
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
        task_result=db_project.task_result,
        input_files=db_project.input_files,
        ml_model=db_project.ml_model,
        ml_model_deeplab=db_project.ml_model_deeplab,
        created_by=db_project.created_by,
        error_code=db_project.error_code,
        description=db_project.description,
        classes=db_project.classes,
        super_resolution=db_project.super_resolution,
    )


def add_ml_models_service(
    id: int,
    ml_model: List[str],
    db: Session,
) -> ProjectSchemas:
    db_project = db.query(Projects).filter(Projects.id == id).first()
    db_project.ml_model = ml_model
    db.commit()
    db.refresh(db_project)
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
        task_result=db_project.task_result,
        input_files=db_project.input_files,
        ml_model=db_project.ml_model,
        ml_model_deeplab=db_project.ml_model_deeplab,
        created_by=db_project.created_by,
        error_code=db_project.error_code,
        description=db_project.description,
        classes=db_project.classes,
        super_resolution=db_project.super_resolution,
    )


def add_ml_models_deeplab_service(
    id: int,
    ml_model: List[str],
    db: Session,
) -> ProjectSchemas:
    db_project = db.query(Projects).filter(Projects.id == id).first()
    db_project.ml_model_deeplab = ml_model
    db.commit()
    db.refresh(db_project)
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
        task_result=db_project.task_result,
        input_files=db_project.input_files,
        ml_model=db_project.ml_model,
        ml_model_deeplab=db_project.ml_model_deeplab,
        created_by=db_project.created_by,
        error_code=db_project.error_code,
        description=db_project.description,
        classes=db_project.classes,
        super_resolution=db_project.super_resolution,
    )


def get_project_files_service(
    project_id: int, project_type: str, db: Session
) -> ProjectFilesSchemas:
    path = f"static/{project_id}/{project_type}"
    if project_type == TypeProjectEnum.aerial_images:
        return get_aerial_images_file(
            path=path,
            project_id=project_id,
            name="aerial_images_project_id",
            db=db,
        )
    elif project_type == TypeProjectEnum.panorama_360:
        return get_panorama_360_files(path=path, project_id=project_id, db=db)
    elif project_type == TypeProjectEnum.satellite_images:
        return get_aerial_images_file(
            path=path,
            project_id=project_id,
            name="satellite_images_project_id",
            db=db,
        )


def get_aerial_images_file(
    path: str, project_id: int, name: str, db: Session
) -> ProjectFilesSchemas:
    path_img_dir = f"{path}/images"
    path_img_tif = f"{path}/tif"
    layer_id = upload_map_tif_services(
        path_img_tif=path_img_tif, name=f"{name}_{project_id}"
    )
    change_preview_layer_id(id=project_id, preview_layer_id=layer_id, db=db)
    images = [
        AerialImagesFileSchemas(
            name=os.path.splitext(os.path.basename(i))[0],
            path=f"{path_img_dir}/{i}",
            path_tif=f"{path_img_tif}/{os.path.splitext(i)[0]}.tif",
        )
        for i in os.listdir(path_img_dir)
    ]
    return ProjectFilesSchemas(
        layer_id=layer_id,
        aerial_images=images,
    )


def get_panorama_360_files(
    path: str, project_id: int, db: Session
) -> ProjectFilesSchemas:
    try:
        panorama_object = create_panorama_360_object(path=path)
        panorama_360 = []
        data_csv = []
        for obj in panorama_object:
            file = obj["schema"]
            data = obj["data"]
            if not file and not file.images:
                continue

            k = [{**j.dict(), "title": file.title} for j in data]
            data_csv.extend(k)
            panorama_360.append(file)

        name_csv = f"{path}/panorama_360_project_id_{project_id}.csv"
        CSVWriter(
            path=name_csv, header=[i.value for i in FieldNameEnum], data=data_csv
        ).writer
    except Exception:
        raise IncorrectFormatCsvOrJpgException
    layer_id = gis_service.upload_layer(csv_file_path=name_csv)
    change_preview_layer_id(id=project_id, preview_layer_id=layer_id, db=db)
    delete_file(name_csv)
    return ProjectFilesSchemas(layer_id=layer_id, panorama_360=panorama_360)


def create_panorama_360_object(path: str) -> Generator:
    for name in os.listdir(path):
        sub_path = f"{path}/{name}"
        if not os.path.isdir(sub_path) or not os.listdir(sub_path):
            yield None
        else:
            path_csv = [i for i in os.listdir(sub_path) if i.endswith(".csv")][0]
            data = read_source_csv(path=f"{sub_path}/{path_csv}")
            list_dir = [i for i in os.listdir(sub_path) if i.endswith(".jpg")]
            result = prepare_data_for_csv(
                data=data, list_dir=list_dir, sub_path=sub_path
            )

            files = create_panorama_360_file(path=path, sub_path=sub_path, name=name)

            yield {
                "data": result,
                "schema": Panorama360FilesSchemas(
                    title=name,
                    images=[file for file in files if file],
                ),
            }


def read_source_csv(path: str) -> List[Dict[str, Any]]:
    columns = [i.value for i in FieldNameInputEnum]
    return CSVReader(path=path, columns=columns).get_dict


def create_panorama_360_file(path: str, sub_path: str, name: str):
    if os.path.isdir(sub_path):
        for filename in os.listdir(sub_path):
            if not filename.endswith(".jpg"):
                yield None
            else:
                yield Panorama360FileSchemas(
                    name=os.path.splitext(filename)[0],
                    path=f"{path}/{name}/{filename}",
                )


def get_scene_img_nums_from_files_services(img_paths: list[str]) -> tuple[int, int]:
    paths_scene_num = glob.glob(
        os.path.join(os.path.dirname(img_paths[0]), "scene_num_*")
    )
    scene_nums = [int(os.path.basename(i).split("_")[-1]) for i in paths_scene_num]
    paths_img_num = glob.glob(os.path.join(os.path.dirname(img_paths[0]), "img_num*"))
    img_nums = [int(os.path.basename(i).split("_")[-1]) for i in paths_img_num]
    for path_file in paths_scene_num:
        delete_file(path=path_file)
    for path_file in paths_img_num:
        delete_file(path=path_file)
    return scene_nums[0], img_nums[0]


def upload_map_tif_services(path_img_tif: str, name: str) -> str:
    paths_tif_files = [
        os.path.join(path_img_tif, name_file) for name_file in os.listdir(path_img_tif)
    ]
    data_for_scv = get_all_geo_data(paths=paths_tif_files)
    csv_file_path = create_csv_file(data=data_for_scv, name_csv=name)
    layer_id = gis_service.upload_layer(csv_file_path=csv_file_path)
    delete_file(csv_file_path)
    return layer_id


def get_compare_projects_by_id_service(id: int, db: Session) -> CompareProjects:
    db_compare_projects = (
        db.query(CompareProjects).filter(CompareProjects.id == id).first()
    )
    return db_compare_projects


def get_compare_projects_by_task_id_service(
    task_id: str, db: Session
) -> CompareProjects:
    db_compare_projects = (
        db.query(CompareProjects).filter(CompareProjects.task_id == task_id).first()
    )
    return db_compare_projects


def get_all_compare_projects_service(
    search: str,
    filter: str,
    sort: str,
    reverse: bool,
    page: int,
    limit: int,
    include_result: bool,
    owner_id: int,
    owner_role: str,
    db: Session,
) -> CompareProjectsSchemas:
    db_compare_projects_table = db.query(CompareProjects)
    if owner_role != "admin":
        db_compare_projects_table = db_compare_projects_table.filter(
            CompareProjects.owner_id == owner_id
        )

    if search:
        db_compare_projects_table = db_compare_projects_table.filter(
            or_(
                CompareProjects.project_1.like(f"%{search}%"),
                CompareProjects.project_2.like(f"%{search}%"),
            )
        )

    if filter != TypeProjectEnum.all:
        db_compare_projects_table = db_compare_projects_table.filter(
            CompareProjects.type == filter
        )

    total = len(db_compare_projects_table.all())
    offset = (page - 1) * limit
    pages = math.ceil(total / limit) if total else 0

    sort_field = CompareProjects.created_at
    if sort == "project_1":
        sort_field = CompareProjects.project_1
    elif sort == "project_2":
        sort_field = CompareProjects.project_2

    if not reverse:
        db_compare_projects_table = db_compare_projects_table.order_by(desc(sort_field))
    else:
        db_compare_projects_table = db_compare_projects_table.order_by(asc(sort_field))

    db_compare_projects = db_compare_projects_table.offset(offset).limit(limit).all()

    if not db_compare_projects:
        return CompareProjectsSchemas(
            projects=[], page=page, pages=pages, total=total, limit=limit
        )

    projects_list = [
        {
            "id": i.id,
            "project_1": CompareProjectObj(
                name=i.project_1,
                date=i.shooting_date_1,
            ),
            "project_2": CompareProjectObj(
                name=i.project_2,
                date=i.shooting_date_2,
            ),
            "type": i.type,
            "status": i.status,
            "task_id": i.task_id,
            "task_result": i.task_result if include_result else None,
            "created_at": i.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "error_code": i.error_code,
            "description": i.description,
        }
        for i in db_compare_projects
    ]

    projects = [CompareProjectSchemas(**i) for i in projects_list]
    return CompareProjectsSchemas(
        projects=projects,
        page=page,
        pages=pages,
        total=total,
        limit=limit,
    )


def delete_compare_projects_by_id_service(id: int, db: Session) -> CompareProjects:
    db_compare_projects = (
        db.query(CompareProjects).filter(CompareProjects.id == id).first()
    )
    db.delete(db_compare_projects)
    db.commit()
    # delete_dir(f"static/compare_result/{id}")
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
        error_code=db_compare_projects.error_code,
        description=db_compare_projects.description,
        owner_id=db_compare_projects.owner_id,
    )


def change_status_compare_project_service(
    id: int,
    status: str,
    db: Session,
    description: Optional[str] = None,
    error_code: Optional[str] = None,
) -> CompareProjectSchemas:
    db_compare_projects = (
        db.query(CompareProjects).filter(CompareProjects.id == id).first()
    )
    if error_code:
        db_compare_projects.description = description
        db_compare_projects.error_code = error_code
    db_compare_projects.status = status
    db.commit()
    db.refresh(db_compare_projects)
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
        error_code=db_compare_projects.error_code,
        description=db_compare_projects.description,
        owner_id=db_compare_projects.owner_id,
    )


def change_task_id_compare_projects_service(
    id: int, task_id: str, db: Session
) -> CompareProjectSchemas:
    db_compare_projects = (
        db.query(CompareProjects).filter(CompareProjects.id == id).first()
    )
    db_compare_projects.task_id = task_id
    db.commit()
    db.refresh(db_compare_projects)
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
        error_code=db_compare_projects.error_code,
        description=db_compare_projects.description,
        owner_id=db_compare_projects.owner_id,
    )


def add_task_result_compare_projects_service(
    id: int,
    task_result: Dict[str, Any],
    db: Session,
) -> CompareProjectSchemas:
    db_compare_projects = (
        db.query(CompareProjects).filter(CompareProjects.id == id).first()
    )
    db_compare_projects.task_result = task_result
    db.commit()
    db.refresh(db_compare_projects)
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
        error_code=db_compare_projects.error_code,
        description=db_compare_projects.description,
        owner_id=db_compare_projects.owner_id,
    )


def create_compare_project_service(
    project_1: str,
    project_2: str,
    shooting_date_1: str,
    shooting_date_2: str,
    type: str,
    status: str,
    owner_id: int,
    db: Session,
) -> CompareProjectSchemas:
    db_compare_projects = CompareProjects(
        project_1=project_1,
        project_2=project_2,
        shooting_date_1=shooting_date_1,
        shooting_date_2=shooting_date_2,
        status=status,
        type=type,
        owner_id=owner_id,
    )
    db.add(db_compare_projects)
    db.commit()
    db.refresh(db_compare_projects)
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
        created_at=db_compare_projects.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        error_code=db_compare_projects.error_code,
        description=db_compare_projects.description,
        owner_id=db_compare_projects.owner_id,
    )


def get_nextcloud_folders_service() -> List[str]:
    path = "static/nextcloud/Admin123/files/"
    subdirectories = [
        name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))
    ]
    if not subdirectories:
        raise NextcloudNotFoundFolders
    subdirectories = get_without_start_nextcloud_folders_service(
        subdirectories=subdirectories)
    sorted_subdirectories = sorted(subdirectories, key=str.casefold)
    return sorted_subdirectories


def get_without_start_nextcloud_folders_service(subdirectories: list[str]) -> list[str]:
    folders = ["Photos", "Templates", "Documents"]
    return list(set(subdirectories)-set(folders))


def get_folders_by_type_service(type_folder: str, names_folder: List[str]) -> List[str]:
    if type_folder == TypeProjectEnum.aerial_images:
        pattern = r"(\w*aer\w*)"
    elif type_folder == TypeProjectEnum.satellite_images:
        pattern = r"(\w*sat\w*)"
    elif type_folder == TypeProjectEnum.panorama_360:
        pattern = r"(\w*360\w*|\w*pan\w*)"
    elif type_folder == "ml":
        pattern = r"(\w*ml\w*)"
    else:
        pattern = None
    matches = []
    if pattern:
        for names_folder in names_folder:
            matches.extend(re.findall(pattern, names_folder, re.IGNORECASE))
        if type_folder != "ml":
            matches = [match for match in matches if "ml" not in match]
    return matches


def check_projects_service(id: int, db: Session) -> Optional[int]:
    if not id:
        return None

    db_project = get_project_by_id_service(id=id, db=db)
    return db_project.id if db_project else None
