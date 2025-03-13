import { AxiosError } from "axios";
import { Dayjs } from "dayjs";
import { AlertColor } from "@mui/material";
import { ERRORS } from "./error";

export interface Alert {
  severity: AlertColor;
  key: string;
}

export interface PaginationData {
  page: number;
  pages: number;
  total: number;
  limit: number;
}

export interface FilterSortData<Filter, Entity> {
  filter: Filter;
  search?: string;
  sort?: keyof Entity;
  reverse?: boolean;
}

export interface GetDataParams<Filter, Entity>
  extends FilterSortData<Filter, Entity> {
  page?: number;
  limit?: number;
}

export type ApiError = AxiosError<{
  detail: { message: string; code: keyof typeof ERRORS };
}>;

export interface DateFilter {
  from: Dayjs | null;
  to: Dayjs | null;
}

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export enum TaskStatus {
  Success = "SUCCESS",
  Pending = "PENDING",
  Failure = "FAILURE",
}

export interface Task {
  task_id: string;
  task_status: TaskStatus;
  task_result: string;
}

export type GetFolderListResponse = {
  links: string[];
};
