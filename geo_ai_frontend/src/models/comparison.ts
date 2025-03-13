import GroupLayer from "@arcgis/core/layers/GroupLayer";
import FeatureLayer from "@arcgis/core/layers/FeatureLayer";

import { PaginationData, Task } from "./common";
import { ProjectStatus, ProjectType } from "./project";
import { ERRORS } from "./error";

export interface Comparison {
  id: number;
  project_1: ComparisonProject;
  project_2: ComparisonProject;
  type: ProjectType;
  status: ProjectStatus;
  task_id: string;
  created_at: Date;
  error_code?: keyof typeof ERRORS;
  description?: string;
  task_result?: ComparisonResult;
  translatedInfo?: string;
}

interface ComparisonProject {
  name: string;
  date: Date;
}

export interface ComparisonTask extends Task {
  project_ids: number;
}

export interface ComparisonResult {
  layer_objects: {
    deleted: string;
    unchanged: string;
    changed: string;
    added: string;
  };
  project_ids: number[];
}

export interface GetComparisonsResponse extends PaginationData {
  projects: Comparison[];
}

export interface ComparisonStatusGroup {
  title: string;
  layer: GroupLayer;
  isVisible: boolean;
}

export interface ComparisonObjectGroup {
  title: string;
  total: number;
  layer: FeatureLayer;
  isVisible: boolean;
}
