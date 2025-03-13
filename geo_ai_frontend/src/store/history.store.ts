import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";

import { handleError } from "@services/http";
import { PaginationData } from "@models/common";
import {
  History,
  FilterSortHistoryData,
  HistoryType,
  ObjectHistory,
} from "@models/history";
import {
  getActionHistory,
  getErrorHistory,
  getObjectHistory,
} from "@services/history";

interface HistoryState {
  history: (History | ObjectHistory)[];
  historyType: HistoryType;
  paginationData: PaginationData;
  filterSortData: FilterSortHistoryData;
  setHistoryType: (type: HistoryType) => void;
  setPaginationData: (paginationData: PaginationData) => Promise<void>;
  setFilterSortData: (filterSortData: FilterSortHistoryData) => Promise<void>;
  getHistory: () => Promise<void>;
}

export const useHistoryStore = create<HistoryState>()(
  immer(
    devtools(
      (set, get) => ({
        history: [],
        historyType: HistoryType.Action,
        paginationData: {
          limit: 10,
          page: 1,
          pages: 1,
          total: 0,
        },
        filterSortData: {},
        setHistoryType: (type) => {
          set({ historyType: type, history: [] });
          get().getHistory();
        },
        setPaginationData: async (paginationData) => {
          set((state) => {
            state.paginationData = paginationData;
          });
          await get().getHistory();
        },
        setFilterSortData: async (filterSortData) => {
          set((state) => {
            state.filterSortData = filterSortData;
          });
          await get().getHistory();
        },
        getHistory: async () => {
          try {
            const { page, limit } = get().paginationData;
            const params = {
              page,
              limit,
              ...get().filterSortData,
            };
            const type = get().historyType;

            const {
              data: { histories, ...paginationData },
            } =
              type === "action"
                ? await getActionHistory(params)
                : type === "error"
                ? await getErrorHistory(params)
                : await getObjectHistory(params);

            set((state) => {
              state.history = histories;
              state.paginationData = paginationData;
            });
          } catch (e) {
            handleError(e);
          }
        },
      }),
      {
        enabled: import.meta.env.DEV,
        store: "history-store",
      }
    )
  )
);
