import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";

import { handleError } from "@services/http";
import { Project, ProjectTypeWithAll } from "@models/project";
import { FilterSortData, PaginationData } from "@models/common";
import { useAlertStore } from "./alert.store";
import { Comparison } from "@models/comparison";
import {
  deleteComparison,
  getComparison,
  getComparisons,
  startComparison,
} from "@services/comparison";
import { getProjects } from "@services/project";
import { ERRORS } from "@models/error";
import i18n from "../i18n";

interface ComparisonState {
  comparisons: Comparison[];
  paginationData: PaginationData;
  filterSortData: FilterSortData<ProjectTypeWithAll, Comparison>;
  setPaginationData: (paginationData: PaginationData) => Promise<void>;
  setFilterSortData: (
    filterSortData: FilterSortData<ProjectTypeWithAll, Comparison>
  ) => Promise<void>;
  getComparisons: () => Promise<void>;
  deleteComparison: (id: number) => Promise<void>;

  comparison?: Comparison;
  dropComparisonData: () => void;
  getComparison: (id: number) => Promise<Comparison>;
  startComparison: (params: number[]) => Promise<number>;

  projects: Project[];
  getFinishedProjects: () => Promise<void>;
}

export const useComparisonStore = create<ComparisonState>()(
  immer(
    devtools(
      (set, get) => ({
        comparisons: [],
        paginationData: {
          limit: 10,
          page: 1,
          pages: 1,
          total: 0,
        },
        filterSortData: {
          filter: "all",
          sort: "created_at",
        },
        setPaginationData: async (paginationData) => {
          set((state) => {
            state.paginationData = paginationData;
          });
          await get().getComparisons();
        },
        setFilterSortData: async (filterSortData) => {
          set((state) => {
            state.filterSortData = filterSortData;
          });
          await get().getComparisons();
        },
        getComparisons: async () => {
          try {
            const {
              data: { projects, ...paginationData },
            } = await getComparisons({
              page: get().paginationData.page,
              limit: get().paginationData.limit,
              ...get().filterSortData,
            });
            const comparisons: Comparison[] = projects
              ? projects.map((c) => {
                  const text =
                    c.error_code && ERRORS[c.error_code]
                      ? i18n.t(ERRORS[c.error_code])
                      : c.description;

                  return { ...c, translatedInfo: text || i18n.t(ERRORS.OTHER) };
                })
              : [];
            set((state) => {
              state.comparisons = comparisons;
              state.paginationData = paginationData;
            });
          } catch (e) {
            handleError(e);
          }
        },
        dropComparisonData: () => {
          set({ comparison: undefined });
        },
        getComparison: async (id) => {
          const { data: comparison } = await getComparison(id);
          set({ comparison });
          return comparison;
        },
        startComparison: async (params) => {
          const { data } = await startComparison(params);
          useAlertStore.getState().setAlert({
            severity: "success",
            key: "alerts.startComparisonSuccess",
          });

          return data.project_ids;
        },
        deleteComparison: async (id) => {
          try {
            await deleteComparison(id);
            get().getComparisons();
            useAlertStore.getState().setAlert({
              severity: "success",
              key: "alerts.deleteComparisonSuccess",
            });
          } catch (e) {
            handleError(e);
          }
        },
        projects: [],
        getFinishedProjects: async () => {
          const { data } = await getProjects({
            filter: "all",
            include_result: true,
            is_completed: true,
            limit: 1000,
          });
          set({ projects: data.projects });
        },
      }),
      {
        enabled: import.meta.env.DEV,
        store: "comparison-store",
      }
    )
  )
);
