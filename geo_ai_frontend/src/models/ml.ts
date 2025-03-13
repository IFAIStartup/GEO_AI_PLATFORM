import { PaginationData, Task } from "./common";
import { ERRORS } from "./error";
import { ProjectType } from "./project";

export interface MLModel {
  id: number;
  name: string;
  status: MLStatus;
  type_of_data: (ProjectType | AdditionalMLDataType)[];
  type_of_objects: string[];
  created_at: Date;
  created_by?: string;
  default_model?: boolean;
  task_result?: {
    classes: string[];
    objects: string[];
  };
  mlflow_url?: string;
  error_code?: keyof typeof ERRORS;
  description?: string;
  translatedInfo?: string;
}

export enum MLStatus {
  Loading = "Preparing",
  NotTrained = "Not trained",
  InTraining = "In the training",
  Trained = "Trained",
  Ready = "Ready to use",
  Error = "Error",
}

export enum MLModelTypes {
  Default = "default",
  Created = "created",
}

export enum MLModelView {
  Yolo = "yolov8",
  YoloDet = "yolov8_det",
  Deeplab = "deeplabv3",
}

export interface GetMLModelsResponse extends PaginationData {
  models: MLModel[];
}

export interface CreateMLModelParams {
  name: string;
  link: string;
  type_of_data: ProjectType | AdditionalMLDataType;
}

export enum AdditionalMLDataType {
  Garbage = "garbage",
}

export interface MLModelTaskResponse extends Task {
  project_id: number;
}

export interface StartTrainingParams {
  id: number;
  type_model: string;
  epochs: number;
  scale_factor: number;
  classes: string[];
}
