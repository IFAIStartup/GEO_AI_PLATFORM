import { Dayjs } from "dayjs";
import { PaginationData } from "./common";
import { ERRORS } from "./error";

export enum HistoryType {
  Action = "action",
  Object = "object",
  Error = "error",
}

export interface GetHistoryParams extends FilterSortHistoryData {
  page?: number;
  limit?: number;
}

export interface FilterSortHistoryData {
  from_date?: Dayjs | null;
  to_date?: Dayjs | null;
  search?: string;
  sort?: keyof (History | ObjectHistory);
  reverse?: boolean;
}

export interface History {
  id: number;
  date: Date;
  user_action: string;
  username: string;
  project: string;
  description: string;
  code?: keyof typeof ERRORS;
  project_id?: string;
  project_type?: "PROJECT" | "PROJECT_COMPARE";
}

export interface ObjectHistory {
  id: number;
  date: Date;
  object_name: string;
  action: string;
  username: string;
  project: string;
  description: string;
  project_id?: string;
}

export interface GetHistoryResponse extends PaginationData {
  histories: History[];
}

export interface GetObjectHistoryResponse extends PaginationData {
  histories: ObjectHistory[];
}
