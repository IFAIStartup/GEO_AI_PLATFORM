import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";

import { Alert } from "@models/common";

interface AlertState {
  alert?: Alert;
  setAlert: (alert: Alert) => void;
  dropAlert: () => void;
}

export const useAlertStore = create<AlertState>()(
  immer(
    devtools(
      (set) => ({
        setAlert: (alert) => {
          set((state) => {
            state.alert = alert;
          });
        },
        dropAlert: () => {
          set((state) => {
            state.alert = undefined;
          });
        },
      }),
      {
        enabled: import.meta.env.DEV,
        store: "alert-store",
      }
    )
  )
);
