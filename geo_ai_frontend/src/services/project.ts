import { AxiosResponse } from "axios";

import $api from "@services/http";
import {
  CreateProjectParams,
  ProjectFiles,
  GetProjectsParams,
  GetProjectsResponse,
  ImageQualities,
  Project,
  ProjectTypeWithAll,
  StartDetectionParams,
  StartDetectionResponse,
  CreateProjectResponse,
  ProjectType,
} from "@models/project";
import { GetFolderListResponse, Task } from "@models/common";

export const getProjects = (
  params: GetProjectsParams<ProjectTypeWithAll, Project>
): Promise<AxiosResponse<GetProjectsResponse>> => {
  return $api.get("/project/get-projects", {
    params: {
      ...params,
      filter: params.filter === "all" ? undefined : params.filter,
    },
  });
};

export const getProject = (id: number): Promise<AxiosResponse<Project>> => {
  return $api.get("/project/get-project", {
    params: {
      id,
      include_result: true,
    },
  });
};

export const createProject = (
  params: CreateProjectParams
): Promise<AxiosResponse<CreateProjectResponse>> => {
  return $api.post("/project/create-project", params);
};

export const deleteProject = (id: number): Promise<AxiosResponse<void>> => {
  return $api.post("/project/delete-project", null, { params: { id } });
};

export const updateNextcloudFolder = (
  project_id: number
): Promise<AxiosResponse<ProjectFiles>> => {
  return $api.get("/project/check-update-nextcloud-folder", {
    params: {
      project_id,
    },
  });
};

export const getProjectFiles = (
  project_id: number
): Promise<AxiosResponse<ProjectFiles>> => {
  return $api.get("/project/project-files", {
    params: {
      project_id,
    },
  });
};

export const getImageQualities = (): Promise<AxiosResponse<ImageQualities>> => {
  return $api.get("/ml/image-quality");
};

export const startAerial = ({
  project_id,
  ...params
}: StartDetectionParams): Promise<AxiosResponse<StartDetectionResponse>> => {
  return $api.post("/ml/aerial", params, {
    params: { project_id },
  });
};

export const startSatellite = ({
  project_id,
  ...params
}: StartDetectionParams): Promise<AxiosResponse<StartDetectionResponse>> => {
  return $api.post("/ml/satellite", params, {
    params: { project_id },
  });
};

export const start360 = ({
  project_id,
  ...params
}: Omit<
  StartDetectionParams,
  "quality" | "save_image_flag" | "save_json_flag"
>): Promise<AxiosResponse<StartDetectionResponse>> => {
  return $api.post("/ml/360", params, {
    params: { project_id },
  });
};

export const getTaskStatus = (taskId: string): Promise<AxiosResponse<Task>> => {
  return $api.get(`/project/tasks/${taskId}`);
};

export const getNextcloudFolders = (
  type: ProjectType
): Promise<AxiosResponse<GetFolderListResponse>> => {
  return $api.get("/project/folder_nextcloud_project", {
    params: {
      type_folder: type,
    },
  });
};
