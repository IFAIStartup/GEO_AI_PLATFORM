import axios from "axios";
import i18n from "i18next";

import { AuthResponse } from "@models/auth";
import { TOKEN_KEY } from "@models/constants";
import { ApiError } from "@models/common";
import { useAlertStore } from "@store/alert.store";

const $api = axios.create({
  withCredentials: true,
  baseURL: import.meta.env.VITE_SERVER_URL + "/api",
});

$api.interceptors.request.use((config) => {
  config.headers.Authorization = `Bearer ${localStorage.getItem(TOKEN_KEY)}`;
  return config;
});

$api.interceptors.response.use(
  (config) => config,
  async (error) => {
    const originalRequest = error.config;

    try {
      if (
        error.response?.status == 401 &&
        error.config &&
        !error.config._isRetry
      ) {
        originalRequest._isRetry = true;
        const { data } = await axios.get<AuthResponse>(
          `${import.meta.env.VITE_SERVER_URL}/api/auth/refresh`,
          {
            withCredentials: true,
          }
        );
        localStorage.setItem(TOKEN_KEY, data.access_token);
        return $api.request(originalRequest);
      }
    } catch (e) {
      window.location.href = "/login";
    }

    throw error;
  }
);

export default $api;

export const handleError = (e: unknown) => {
  const err = e as ApiError;
  const msg = err.response?.data?.detail?.message || i18n.t("general.error");
  useAlertStore.getState().setAlert({ severity: "error", key: msg });
};
