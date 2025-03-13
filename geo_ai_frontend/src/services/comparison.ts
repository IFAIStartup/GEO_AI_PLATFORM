import { AxiosResponse } from "axios";
import FeatureLayer from "@arcgis/core/layers/FeatureLayer";
import PictureMarkerSymbol from "@arcgis/core/symbols/PictureMarkerSymbol";
import SimpleRenderer from "@arcgis/core/renderers/SimpleRenderer";

import imageIcon from "@assets/map_image_icon.svg";

import $api from "@services/http";
import { Project, ProjectTypeWithAll } from "@models/project";
import { GetDataParams } from "@models/common";
import {
  Comparison,
  ComparisonTask,
  GetComparisonsResponse,
} from "@models/comparison";

export const getComparisons = (
  params: GetDataParams<ProjectTypeWithAll, Comparison>
): Promise<AxiosResponse<GetComparisonsResponse>> => {
  return $api.get("/project/get-all-compare-projects", {
    params: {
      ...params,
      filter: params.filter === "all" ? undefined : params.filter,
    },
  });
};

export const getComparison = (
  id: number
): Promise<AxiosResponse<Comparison>> => {
  return $api.get("/project/get-compare-projects", {
    params: {
      id,
    },
  });
};

export const startComparison = (
  params: number[]
): Promise<AxiosResponse<ComparisonTask>> => {
  return $api.post("/project/compare-projects", params);
};

export const deleteComparison = (id: number): Promise<AxiosResponse<void>> => {
  return $api.post("/project/delete-compare-projects", null, {
    params: { id },
  });
};

const projSymbol = new PictureMarkerSymbol({
  url: imageIcon,
  width: "24px",
  height: "24px",
});

export const addProjectFeatureLayer = (
  mapView: __esri.MapView,
  project: Project,
  layersRef: React.MutableRefObject<FeatureLayer[]>,
  isFirst: boolean
) => {
  const imageLayerRenderer = new SimpleRenderer({ symbol: projSymbol });
  const newLayer = new FeatureLayer({
    renderer: imageLayerRenderer,
    portalItem: {
      id: project.preview_layer_id,
    },
    outFields: ["*"],
  });
  layersRef.current[project.id] = newLayer;
  mapView.when(() => {
    mapView.map.add(newLayer);
  });

  if (isFirst) {
    newLayer.when(() => {
      mapView.goTo(
        {
          center: newLayer.fullExtent.center,
          zoom: 14,
        },
        { duration: 2000 }
      );
    });
  }
};
