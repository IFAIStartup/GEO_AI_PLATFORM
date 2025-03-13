import { AxiosResponse } from "axios";

import $api from "@services/http";
import {
  GetHistoryResponse,
  GetHistoryParams,
  GetObjectHistoryResponse,
} from "@models/history";

export const getActionHistory = (
  params: GetHistoryParams
): Promise<AxiosResponse<GetHistoryResponse>> => {
  return $api.get("/history/get-all-action-history", {
    params: {
      ...params,
      from_date: params.from_date?.toISOString(),
      to_date: params.to_date?.add(1, "day").toISOString(),
    },
  });
};

export const getObjectHistory = (
  params: GetHistoryParams
): Promise<AxiosResponse<GetObjectHistoryResponse>> => {
  return $api.get("/history/get-all-object-history", {
    params: {
      ...params,
      from_date: params.from_date?.toISOString(),
      to_date: params.to_date?.add(1, "day").toISOString(),
    },
  });
};

export const getErrorHistory = (
  params: GetHistoryParams
): Promise<AxiosResponse<GetHistoryResponse>> => {
  return $api.get("/history/get-all-error-history", {
    params: {
      ...params,
      from_date: params.from_date?.toISOString(),
      to_date: params.to_date?.add(1, "day").toISOString(),
    },
  });
};
