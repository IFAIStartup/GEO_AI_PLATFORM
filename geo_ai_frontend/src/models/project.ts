import Graphic from "@arcgis/core/Graphic";
import FeatureLayer from "@arcgis/core/layers/FeatureLayer";

import { GetDataParams, PaginationData, Task } from "./common";
import { ERRORS } from "./error";

export interface Project {
  id: number;
  name: string;
  date: Date;
  link: string;
  type: ProjectType;
  created_at: Date;
  created_by?: string;
  status: ProjectStatus;
  selectedModelTypes: string[];
  selectedModelViews: string[];
  error_code?: keyof typeof ERRORS;
  description?: string;
  input_files?: ProjectFiles;
  detection_id?: string;
  task_result?: DetectionResult;
  ml_model?: string[];
  ml_model_deeplab?: string[];
  preview_layer_id?: string;
  classes?: string[];
  super_resolution?: string;
  imageQuality?: string;
  images?: ProjectFile[];
  pointCloudGroups?: ProjectFileGroup[];
  areFilesLoading?: boolean;
  allFilesSelected?: boolean;
  translatedInfo?: string;
  someFilesSelected?: boolean;
}

export interface ProjectFileGroup {
  title: string;
  images: ProjectFile[];
  pcdPath?: string;
  selected?: boolean;
}

export interface ProjectFile {
  name: string;
  path: string;
  path_tif?: string;
  feature?: Graphic;
  graphic?: Graphic;
}

export enum ProjectStatus {
  Initial = "Ready to start",
  InProgress = "In progress",
  Finished = "Completed",
  Error = "Error",
}

export enum ProjectType {
  Aerial = "aerial_images",
  Satellite = "satellite_images",
  Panorama = "panorama_360",
}

export type ProjectTypeWithAll = ProjectType | "all";

export enum OverlayType {
  Detection = "detection",
  Segmentation = "segmentation",
}

export interface GetProjectsParams<Filter, Entity>
  extends GetDataParams<Filter, Entity> {
  include_result?: boolean;
  is_completed?: boolean;
}

export interface GetProjectsResponse extends PaginationData {
  projects: Project[];
}

export type CreateProjectParams = Omit<
  Project,
  "id" | "created_at" | "status" | "selectedModelTypes" | "selectedModelViews"
>;

export interface CreateProjectResponse {
  project: Project;
  task_id: string;
}

export interface ProjectFiles {
  layer_id: string;
  aerial_images?: ProjectFile[];
  panorama_360?: ProjectFileGroup[];
}

export type ImageQualities = {
  [key: string]: string;
};

export interface DetectionResult {
  path_images: string[];
  layer_id: string;
  pcd_path?: string;
}

export interface StartDetectionParams {
  project_id: number;
  paths: string[];
  quality: string;
  ml_model: string[];
  ml_model_deeplab: string[];
  save_image_flag: boolean;
  save_json_flag: boolean;
}

export interface StartDetectionResponse extends Task {
  project_id: number;
}

export interface DetectionResultGroup {
  title: string;
  total: number;
  layer: FeatureLayer;
  isVisible: boolean;
}

export enum MapFilesTogglePosition {
  IMAGES = "images",
  MAP = "map",
  BOTH = "both",
}
