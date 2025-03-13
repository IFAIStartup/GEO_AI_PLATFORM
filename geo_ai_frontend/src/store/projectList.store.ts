import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";

import { handleError } from "@services/http";
import {
  CreateProjectParams,
  CreateProjectResponse,
  Project,
  ProjectType,
  ProjectTypeWithAll,
} from "@models/project";
import {
  createProject,
  deleteProject,
  getNextcloudFolders,
  getProjects,
} from "@services/project";
import { FilterSortData, PaginationData } from "@models/common";
import { useAlertStore } from "./alert.store";
import { ERRORS } from "@models/error";
import i18n from "../i18n";

interface ProjectListState {
  projects: Project[];
  paginationData: PaginationData;
  filterSortData: FilterSortData<ProjectTypeWithAll, Project>;
  folders: string[];
  getFolders: (type: ProjectType) => Promise<void>;
  setPaginationData: (paginationData: PaginationData) => Promise<void>;
  setFilterSortData: (
    filterSortData: FilterSortData<ProjectTypeWithAll, Project>
  ) => Promise<void>;
  getProjects: () => Promise<void>;
  createProject: (
    params: CreateProjectParams
  ) => Promise<CreateProjectResponse>;
  deleteProject: (id: number) => Promise<void>;
}

export const useProjectListStore = create<ProjectListState>()(
  immer(
    devtools(
      (set, get) => ({
        projects: [],
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
        folders: [],
        setPaginationData: async (paginationData) => {
          set((state) => {
            state.paginationData = paginationData;
          });
          await get().getProjects();
        },
        setFilterSortData: async (filterSortData) => {
          set((state) => {
            state.filterSortData = filterSortData;
          });
          await get().getProjects();
        },
        getProjects: async () => {
          try {
            const {
              data: { projects, ...paginationData },
            } = await getProjects({
              page: get().paginationData.page,
              limit: get().paginationData.limit,
              ...get().filterSortData,
              include_result: false,
            });
            set((state) => {
              state.projects = projects.map((p) => {
                const text =
                  p.error_code && ERRORS[p.error_code]
                    ? i18n.t(ERRORS[p.error_code])
                    : p.description;

                return { ...p, translatedInfo: text || i18n.t(ERRORS.OTHER) };
              });
              state.paginationData = paginationData;
            });
          } catch (e) {
            handleError(e);
          }
        },
        createProject: async (params) => {
          const { data } = await createProject(params);

          return data;
        },
        deleteProject: async (id) => {
          try {
            await deleteProject(id);
            get().getProjects();
            useAlertStore.getState().setAlert({
              severity: "success",
              key: "alerts.deleteProjectSuccess",
            });
          } catch (e) {
            handleError(e);
          }
        },
        getFolders: async (type) => {
          const { data } = await getNextcloudFolders(type);
          set({ folders: data.links });
        },
      }),
      {
        enabled: import.meta.env.DEV,
        store: "project-list-store",
      }
    )
  )
);
