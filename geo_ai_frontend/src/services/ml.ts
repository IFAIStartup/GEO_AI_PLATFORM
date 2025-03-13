import { AxiosResponse } from "axios";

import $api from "@services/http";
import { ProjectType, ProjectTypeWithAll } from "@models/project";
import { GetDataParams, GetFolderListResponse } from "@models/common";
import {
  CreateMLModelParams,
  MLModelTaskResponse,
  GetMLModelsResponse,
  MLModel,
  StartTrainingParams,
  MLModelView,
  AdditionalMLDataType,
} from "@models/ml";

export const getMLModels = (
  params: GetDataParams<ProjectTypeWithAll, MLModel>,
  isDefault: boolean
): Promise<AxiosResponse<GetMLModelsResponse>> => {
  return $api.get("/ml/get-ml-models", {
    params: {
      ...params,
      default: isDefault,
      filter: params.filter === "all" ? undefined : params.filter,
    },
  });
};

export const getMLModel = (id: number): Promise<AxiosResponse<MLModel>> => {
  return $api.get("/ml/get-ml-model", {
    params: { id },
  });
};

export const createMLModel = (
  params: CreateMLModelParams
): Promise<AxiosResponse<MLModelTaskResponse>> => {
  return $api.post("/ml/create-ml-model", params);
};

export const deleteMLModel = (id: number): Promise<AxiosResponse<unknown>> => {
  return $api.post("/ml/delete-ml-model", null, { params: { id } });
};

export const startTraining = (
  params: StartTrainingParams
): Promise<AxiosResponse<MLModelTaskResponse>> => {
  return $api.post("/ml/train", params);
};

export const finishTraining = (
  id: number
): Promise<AxiosResponse<MLModelTaskResponse>> => {
  return $api.post("/ml/save-ml-model", null, { params: { id } });
};

export const getMLModelsByType = (
  type: ProjectType | AdditionalMLDataType,
  view: MLModelView
): Promise<AxiosResponse<MLModel[]>> => {
  return $api.get("/ml/get-ml-models-by-types", {
    params: {
      type,
      view,
    },
  });
};

export const getMLFlowUrl = (): Promise<AxiosResponse<{ url: string }>> => {
  return $api.get("/mlget-mlflow-address");
};

export const getModelTypes = (): Promise<AxiosResponse<string[]>> => {
  return $api.get("/mlget-mlflow-type-model");
};

export const getNextcloudFolders = (): Promise<
  AxiosResponse<GetFolderListResponse>
> => {
  return $api.get("/project/folder_nextcloud_ml");
};
