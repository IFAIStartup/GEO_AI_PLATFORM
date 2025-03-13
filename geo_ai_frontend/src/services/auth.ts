import axios, { AxiosResponse } from "axios";

import {
  ChangePasswordParams,
  LoginParams,
  ResetPasswordParams,
  RestoreAccessParams,
} from "@models/user";
import { ArcGISToken, AuthResponse } from "@models/auth";
import $api from "@services/http";

export const login = (
  params: LoginParams
): Promise<AxiosResponse<AuthResponse>> => {
  return axios.post<AuthResponse>(
    import.meta.env.VITE_SERVER_URL + "/api/auth/login",
    params
  );
};

export const changePassword = (
  params: ChangePasswordParams
): Promise<AxiosResponse> => {
  return $api.post("/auth/change-password", params);
};

export const restoreAccess = (
  params: RestoreAccessParams
): Promise<AxiosResponse> => {
  return $api.post("/auth/restore_access", params);
};

export const checkRestoreKey = (
  key: string
): Promise<AxiosResponse<boolean>> => {
  return $api.get("/auth/restore_access/status", { params: { key } });
};

export const resetPassword = ({
  key,
  ...params
}: ResetPasswordParams): Promise<AxiosResponse> => {
  return $api.post("/auth/restore_access/change-password", params, {
    params: { key },
  });
};

export const logout = (): Promise<AxiosResponse> => {
  return $api.get("/auth/logout");
};

export const refresh = (): Promise<AxiosResponse<AuthResponse>> => {
  return axios.get(`${import.meta.env.VITE_SERVER_URL}/api/auth/refresh`, {
    withCredentials: true,
  });
};

export const getArcGISToken = (): Promise<AxiosResponse<ArcGISToken>> => {
  return $api.get(`/arcgis/generate-arcgis-token`);
};
