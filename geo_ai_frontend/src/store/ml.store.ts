import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";

import { handleError } from "@services/http";
import { ProjectTypeWithAll } from "@models/project";
import { FilterSortData, PaginationData } from "@models/common";
import { useAlertStore } from "./alert.store";
import {
  CreateMLModelParams,
  MLModel,
  MLModelTypes,
  MLStatus,
  StartTrainingParams,
} from "@models/ml";
import {
  createMLModel,
  deleteMLModel,
  finishTraining,
  getMLFlowUrl,
  getMLModel,
  getMLModels,
  getModelTypes,
  getNextcloudFolders,
  startTraining,
} from "@services/ml";
import { useUserStore } from "./user.store";
import { ERRORS } from "@models/error";
import i18n from "../i18n";

interface MLState {
  mlFlowURL: string;
  getMLFlowURL: () => Promise<void>;
  modelTypes: string[];
  getModelTypes: () => Promise<void>;
  folders: string[];
  getFolders: () => Promise<void>;

  model?: MLModel;
  setModel: (model: MLModel) => void;
  getModel: (modelId: number) => Promise<void>;
  resetModel: () => void;
  startTraining: (params: StartTrainingParams) => Promise<void>;
  finishTraining: (id: number) => Promise<void>;
  createModel: (params: CreateMLModelParams) => Promise<number>;
  deleteModel: (id: number) => Promise<void>;

  defaultModels: MLModel[];
  defaultModelsPaginationData: PaginationData;
  defaultModelsFilterSortData: FilterSortData<ProjectTypeWithAll, MLModel>;

  createdModels: MLModel[];
  createdModelsPaginationData: PaginationData;
  createdModelsFilterSortData: FilterSortData<ProjectTypeWithAll, MLModel>;

  getModels: () => Promise<void>;
  setPaginationData: (
    paginationData: PaginationData,
    type: MLModelTypes
  ) => Promise<void>;
  setFilterSortData: (
    filterSortData: FilterSortData<ProjectTypeWithAll, MLModel>,
    type: MLModelTypes
  ) => Promise<void>;
}

export const useMLStore = create<MLState>()(
  immer(
    devtools(
      (set, get) => ({
        mlFlowURL: "",
        modelTypes: [],
        defaultModels: [],
        defaultModelsPaginationData: {
          limit: 10,
          page: 1,
          pages: 1,
          total: 0,
        },
        defaultModelsFilterSortData: {
          filter: "all",
          sort: "created_at",
        },
        createdModels: [],
        createdModelsPaginationData: {
          limit: 10,
          page: 1,
          pages: 1,
          total: 0,
        },
        createdModelsFilterSortData: {
          filter: "all",
          sort: "created_at",
        },
        folders: [],
        setModel: (model) => {
          set({ model });
        },
        getModel: async (modelId) => {
          try {
            const { data } = await getMLModel(modelId);
            set({ model: data });
            if (data.status === MLStatus.Error) {
              useAlertStore.getState().setAlert({
                severity: "error",
                key: "general.error",
              });
            }
          } catch (e) {
            handleError(e);
            set({
              model: {
                id: 0,
                name: "",
                status: MLStatus.Error,
                created_at: new Date(),
                type_of_data: [],
                type_of_objects: [],
              },
            });
          }
        },
        resetModel: () => {
          set({ model: undefined });
        },
        startTraining: async (params) => {
          await startTraining(params);
          set((state) => {
            if (state.model) {
              state.model.status = MLStatus.Trained;
            }
          });
        },
        finishTraining: async (id) => {
          await finishTraining(id);
          set((state) => {
            if (state.model) {
              state.model.status = MLStatus.Ready;
            }
          });
        },
        getModels: async () => {
          const mlTab = useUserStore.getState().preferences.mlTab;
          if (mlTab === MLModelTypes.Created) {
            try {
              const {
                data: { models, ...paginationData },
              } = await getMLModels(
                {
                  page: get().createdModelsPaginationData.page,
                  limit: get().createdModelsPaginationData.limit,
                  ...get().createdModelsFilterSortData,
                },
                false
              );
              set((state) => {
                state.createdModels = models.map((m) => {
                  const text =
                    m.error_code && ERRORS[m.error_code]
                      ? i18n.t(ERRORS[m.error_code])
                      : m.description;

                  return { ...m, translatedInfo: text || i18n.t(ERRORS.OTHER) };
                });
                state.createdModelsPaginationData = paginationData;
              });
            } catch (e) {
              handleError(e);
            }
          } else {
            try {
              const {
                data: { models, ...paginationData },
              } = await getMLModels(
                {
                  page: get().defaultModelsPaginationData.page,
                  limit: get().defaultModelsPaginationData.limit,
                  ...get().defaultModelsFilterSortData,
                },
                true
              );
              set((state) => {
                state.defaultModels = models;
                state.defaultModelsPaginationData = paginationData;
              });
            } catch (e) {
              handleError(e);
            }
          }
        },
        setPaginationData: async (paginationData, type) => {
          if (type === MLModelTypes.Default) {
            set((state) => {
              state.defaultModelsPaginationData = paginationData;
            });
          } else if (type === MLModelTypes.Created) {
            set((state) => {
              state.createdModelsPaginationData = paginationData;
            });
          }
          await get().getModels();
        },
        setFilterSortData: async (filterSortData, type) => {
          if (type === MLModelTypes.Default) {
            set((state) => {
              state.defaultModelsFilterSortData = filterSortData;
            });
          } else if (type === MLModelTypes.Created) {
            set((state) => {
              state.createdModelsFilterSortData = filterSortData;
            });
          }
          await get().getModels();
        },
        createModel: async (params) => {
          const { data: model } = await createMLModel(params);

          useAlertStore.getState().setAlert({
            severity: "success",
            key: "alerts.createModelSuccess",
          });

          return model.project_id;
        },
        deleteModel: async (id) => {
          await deleteMLModel(id);
          get().getModels();

          useAlertStore.getState().setAlert({
            severity: "success",
            key: "alerts.deleteModelSuccess",
          });
        },
        getMLFlowURL: async () => {
          const { data } = await getMLFlowUrl();
          set({ mlFlowURL: data.url });
        },
        getModelTypes: async () => {
          const { data } = await getModelTypes();
          set({ modelTypes: data });
        },
        getFolders: async () => {
          const { data } = await getNextcloudFolders();
          set({ folders: data.links });
        },
      }),
      {
        enabled: import.meta.env.DEV,
        store: "ml-store",
      }
    )
  )
);
