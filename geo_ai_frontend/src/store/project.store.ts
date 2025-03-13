import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import Graphic from "@arcgis/core/Graphic";
import PictureMarkerSymbol from "@arcgis/core/symbols/PictureMarkerSymbol";

import {
  ImageQualities,
  Project,
  ProjectFile,
  ProjectStatus,
  ProjectType,
  StartDetectionResponse,
} from "@models/project";
import {
  getImageQualities,
  getProject,
  getProjectFiles,
  start360,
  startAerial,
  startSatellite,
  updateNextcloudFolder,
} from "@services/project";
import { useMapStore } from "@store/map.store";
import { handleError } from "@services/http";
import { AdditionalMLDataType, MLModel, MLModelView } from "@models/ml";
import { getMLModelsByType } from "@services/ml";

import selectedFileIcon from "@assets/map_file_icon_selected.svg";

const selectedFileSymbol = new PictureMarkerSymbol({
  url: selectedFileIcon,
  width: "24px",
  height: "24px",
});

const initialProj: Project = {
  id: 0,
  name: "",
  created_at: new Date(),
  date: new Date(),
  link: "",
  status: ProjectStatus.Initial,
  type: ProjectType.Aerial,
  selectedModelTypes: [""],
  selectedModelViews: [""],
};

interface ProjectState {
  project: Project;
  imageQualities?: ImageQualities;
  availableModelTypes: MLModel[];
  availableModelViews: MLModel[];
  getProject: (id: number) => Promise<Project>;
  dropProjectData: () => void;
  getProjectFiles: () => Promise<void>;
  toggleImage: (path: string) => void;
  mapFeaturesToImages: (features: Graphic[]) => void;
  togglePointCloudGroup: (title: string) => void;
  mapFeaturesToPointCloudGroups: (features: Graphic[]) => void;
  toggleAllFiles: (newState: boolean) => void;
  setImageQuality: (quality: string) => void;
  selectMLModelType: (modelNames: string[]) => void;
  selectMLModelView: (modelNames: string[]) => void;
  startDetection: () => Promise<void>;
  getImageQualities: () => Promise<void>;
  getAvailableMLModelTypes: () => Promise<void>;
  getAvailableMLModelViews: () => Promise<void>;
}

export const useProjectStore = create<ProjectState>()(
  immer(
    devtools(
      (set, get) => ({
        project: { ...initialProj },
        availableModelTypes: [],
        availableModelViews: [],
        getProject: async (id) => {
          const { data } = await getProject(id);

          if (data.status === ProjectStatus.Finished) {
            set((state) => {
              if (!data.task_result) {
                return;
              }

              state.project = { ...state.project, ...data };
              const { path_images, pcd_path } = data.task_result;
              if (state.project.type === ProjectType.Panorama) {
                state.project.pointCloudGroups = [
                  {
                    title: "Result",
                    images: path_images.map((p, i) => ({
                      name: i.toString(),
                      path: p,
                    })),
                    pcdPath: pcd_path,
                  },
                ];
              } else {
                state.project.images = path_images.map((p, i) => ({
                  name: i.toString(),
                  path: p,
                }));
              }
            });
          } else {
            set((state) => {
              state.project = {
                ...state.project,
                ...data,
                images: data.input_files?.aerial_images || [],
                pointCloudGroups: data.input_files?.panorama_360 || [],
                preview_layer_id: data.input_files?.layer_id,
                areFilesLoading: !data.input_files,
              };
            });
          }

          return get().project;
        },
        dropProjectData: () => {
          set({
            project: { ...initialProj },
            availableModelTypes: [],
            availableModelViews: [],
          });
        },
        getProjectFiles: async () => {
          set((state) => {
            state.project.images = [];
            state.project.pointCloudGroups = [];
            state.project.areFilesLoading = true;
            state.project.someFilesSelected = false;
            state.project.allFilesSelected = false;
          });
          const projectId = get().project.id;
          if (projectId) {
            try {
              await updateNextcloudFolder(projectId);
              const { data } = await getProjectFiles(projectId);

              set((state) => {
                state.project.images = data.aerial_images || [];
                state.project.pointCloudGroups = data.panorama_360 || [];
                state.project.preview_layer_id = data.layer_id;
                state.project.areFilesLoading = false;
              });
            } catch (e) {
              set((state) => {
                state.project.areFilesLoading = false;
              });
              handleError(e);
            }
          }
        },
        toggleImage: (path) => {
          const imageIndex = get().project.images?.findIndex(
            (img) => img.path === path
          );
          if (imageIndex == null) {
            return;
          }
          const image = get().project.images?.[imageIndex];
          const mapView = useMapStore.getState().mapView;

          if (image) {
            let graphic: Graphic | undefined;
            if (image.graphic) {
              mapView?.graphics.remove(image.graphic);
              graphic = undefined;
            } else {
              const selectedPoint = new Graphic({
                geometry: image.feature?.geometry,
                symbol: selectedFileSymbol,
              });
              mapView?.graphics.add(selectedPoint);
              graphic = selectedPoint;
            }

            set((state) => {
              if (state.project.images) {
                state.project.images[imageIndex].graphic = graphic;
                const selected = state.project.images.filter((i) => i.graphic);
                state.project.someFilesSelected = selected.length > 0;
                state.project.allFilesSelected =
                  selected.length === state.project.images.length;
              }
            });
          }
        },
        mapFeaturesToImages: (features) => {
          set((state) => {
            state.project.images?.forEach((image) => {
              image.feature = features.find(
                (f) => f.getAttribute("name") == image.name
              );
            });
          });
        },
        togglePointCloudGroup: (title) => {
          const groupIndex = get().project.pointCloudGroups?.findIndex(
            (group) => group.title === title
          );
          if (groupIndex == null) {
            return;
          }
          const mapView = useMapStore.getState().mapView;
          const group = get().project.pointCloudGroups?.[groupIndex];
          const groupImages = group?.images || [];

          if (groupImages.length) {
            let images: ProjectFile[];
            const isSelected = !!groupImages[0].graphic;
            if (isSelected) {
              mapView?.graphics.removeMany(
                groupImages.map((i) => i.graphic) as Graphic[]
              );
              images = groupImages.map((i) => ({
                ...i,
                graphic: undefined,
              }));
            } else {
              images = groupImages.map((i) => {
                const graphic = new Graphic({
                  geometry: i.feature?.geometry,
                  symbol: selectedFileSymbol,
                });

                return {
                  ...i,
                  graphic,
                };
              });
              mapView?.graphics.addMany(
                images.map((i) => i.graphic) as Graphic[]
              );
            }
            set((state) => {
              if (state.project.pointCloudGroups) {
                state.project.pointCloudGroups[groupIndex].selected =
                  !isSelected;
                state.project.pointCloudGroups[groupIndex].images = images;
                const selected = state.project.pointCloudGroups.filter(
                  (g) => g.selected
                );
                state.project.someFilesSelected = selected.length > 0;
                state.project.allFilesSelected =
                  selected.length === state.project.pointCloudGroups.length;
              }
            });
          }
        },
        mapFeaturesToPointCloudGroups: (features) => {
          set((state) => {
            state.project.pointCloudGroups?.forEach((group) => {
              group.images?.forEach((img) => {
                img.feature = features.find(
                  (f) =>
                    f.getAttribute("title") == group.title &&
                    f.getAttribute("name") == img.name
                );
              });
            });
          });
        },
        toggleAllFiles: (newState) => {
          get().project.images?.forEach((img) => {
            if (!!img.graphic !== newState) {
              get().toggleImage(img.path);
            }
          });
          get().project.pointCloudGroups?.forEach((group) => {
            if (group.selected !== newState) {
              get().togglePointCloudGroup(group.title);
            }
          });
          set((state) => {
            state.project.someFilesSelected = newState;
            state.project.allFilesSelected = newState;
          });
        },
        setImageQuality: (quality) => {
          set((state) => {
            state.project.imageQuality = quality;
          });
        },
        startDetection: async () => {
          const project = get().project;
          if (project.id) {
            let data: StartDetectionResponse;

            if (project.type === ProjectType.Panorama) {
              const paths =
                project.pointCloudGroups
                  ?.filter((g) => g.selected)
                  .map((g) => g.images.map((img) => img.path))
                  .reduce((a, v) => a.concat(v), []) || [];

              data = (
                await start360({
                  project_id: project.id,
                  paths,
                  ml_model: project.selectedModelTypes,
                  ml_model_deeplab: project.selectedModelViews,
                })
              ).data;
            } else if (project.type === ProjectType.Aerial) {
              const paths =
                (project.images
                  ?.filter((img) => !!img.path_tif && !!img.graphic)
                  .map((img) => img.path_tif) as string[]) || [];

              data = (
                await startAerial({
                  project_id: project.id,
                  paths,
                  ml_model: project.selectedModelTypes,
                  ml_model_deeplab: project.selectedModelViews,
                  quality: project.imageQuality || "",
                  save_image_flag: true,
                  save_json_flag: true,
                })
              ).data;
            } else {
              const paths =
                (project.images
                  ?.filter((img) => !!img.path_tif && !!img.graphic)
                  .map((img) => img.path_tif) as string[]) || [];

              data = (
                await startSatellite({
                  project_id: project.id,
                  paths,
                  ml_model: project.selectedModelTypes,
                  ml_model_deeplab: project.selectedModelViews,
                  quality: project.imageQuality || "",
                  save_image_flag: true,
                  save_json_flag: true,
                })
              ).data;
            }

            set((state) => {
              state.project.status = ProjectStatus.InProgress;
              state.project.detection_id = data.task_id;
            });
          }
        },
        getImageQualities: async () => {
          const { data } = await getImageQualities();

          set((state) => {
            state.imageQualities = data;
            state.project.imageQuality = Object.values(data)[0];
          });
        },
        getAvailableMLModelTypes: async () => {
          const projType = get().project.type;
          const { data: mainData } = await getMLModelsByType(
            projType,
            MLModelView.Yolo
          );

          let additionalData: MLModel[] = [];
          if (projType === ProjectType.Panorama) {
            const { data } = await getMLModelsByType(
              AdditionalMLDataType.Garbage,
              MLModelView.YoloDet
            );
            additionalData = data;
          }

          const defaultModel = mainData.find((model) => model.default_model);
          set((state) => {
            state.availableModelTypes = [...mainData, ...additionalData];
            if (defaultModel) {
              state.project.selectedModelTypes = [defaultModel.name];
            }
          });
        },
        getAvailableMLModelViews: async () => {
          const { data } = await getMLModelsByType(
            get().project.type,
            MLModelView.Deeplab
          );
          const defaultModel = data.find((model) => model.default_model);
          set((state) => {
            state.availableModelViews = data;
            if (defaultModel) {
              state.project.selectedModelViews = [defaultModel.name];
            }
          });
        },
        selectMLModelType: (modelNames: string[]) => {
          set((state) => {
            state.project.selectedModelTypes = modelNames;
          });
        },
        selectMLModelView: (modelNames: string[]) => {
          set((state) => {
            state.project.selectedModelViews = modelNames;
          });
        },
      }),
      {
        enabled: import.meta.env.DEV,
        store: "project-store",
      }
    )
  )
);
