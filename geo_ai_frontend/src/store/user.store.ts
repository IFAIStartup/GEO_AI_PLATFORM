import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";

import {
  refresh,
  login,
  logout,
  changePassword,
  restoreAccess,
  checkRestoreKey,
  resetPassword,
} from "@services/auth";
import { handleError } from "@services/http";
import { useAlertStore } from "@store/alert.store";
import { MapFilesTogglePosition } from "@models/project";
import { TOKEN_KEY } from "@models/constants";
import {
  User,
  LoginParams,
  ChangePasswordParams,
  RestoreAccessParams,
  ResetPasswordParams,
} from "@models/user";
import { MLModelTypes } from "@models/ml";

interface UserState {
  user?: User;
  preferences: {
    mapFilesToggle: MapFilesTogglePosition;
    mlTab: MLModelTypes;
  };
  setMapFilesTogglePosition: (pos: MapFilesTogglePosition) => void;
  setMLTab: (pos: MLModelTypes) => void;
  login: (params: LoginParams) => Promise<void>;
  changePassword: (params: ChangePasswordParams) => Promise<void>;
  restoreAccess: (params: RestoreAccessParams) => Promise<void>;
  checkRestoreKey: (key: string) => Promise<boolean>;
  resetPassword: (params: ResetPasswordParams) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

const MAP_FILES_TOGGLE_KEY = "mapFilesToggle";
const ML_TAB_KEY = "mlTab";
const mapFilesToggle = localStorage.getItem(MAP_FILES_TOGGLE_KEY);
const mlTab = localStorage.getItem(ML_TAB_KEY);

export const useUserStore = create<UserState>()(
  immer(
    devtools(
      (set, get) => ({
        preferences: {
          mapFilesToggle: mapFilesToggle
            ? (mapFilesToggle as MapFilesTogglePosition)
            : MapFilesTogglePosition.BOTH,
          mlTab: mlTab ? (mlTab as MLModelTypes) : MLModelTypes.Default,
        },
        setMapFilesTogglePosition: (pos) => {
          localStorage.setItem(MAP_FILES_TOGGLE_KEY, pos);
          set({ preferences: { ...get().preferences, mapFilesToggle: pos } });
        },
        setMLTab: (tab) => {
          localStorage.setItem(ML_TAB_KEY, tab);
          set({ preferences: { ...get().preferences, mlTab: tab } });
        },
        login: async (params) => {
          params.email = params.email.replaceAll(/\\{1,2}/gm, "\\");
          const { data } = await login(params);
          localStorage.setItem(TOKEN_KEY, data.access_token);
          set({ user: data.user });
        },
        changePassword: async (params) => {
          await changePassword(params);
          useAlertStore.getState().setAlert({
            severity: "success",
            key: "alerts.changePasswordSuccess",
          });
        },
        restoreAccess: async (params) => {
          await restoreAccess(params);
        },
        checkRestoreKey: async (key) => {
          const { data } = await checkRestoreKey(key);
          return data;
        },
        resetPassword: async (params) => {
          await resetPassword(params);
        },
        logout: async () => {
          try {
            await logout();
            localStorage.removeItem(TOKEN_KEY);
            set((state) => {
              state.user = undefined;
            });
          } catch (e) {
            handleError(e);
          }
        },
        checkAuth: async () => {
          const { data } = await refresh();
          localStorage.setItem(TOKEN_KEY, data.access_token);
          set({ user: data.user });
        },
      }),
      {
        enabled: import.meta.env.DEV,
        store: "user-store",
      }
    )
  )
);
