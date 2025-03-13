import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import MapView from "@arcgis/core/views/MapView";

import { ArcGISToken } from "@models/auth";
import { getArcGISToken } from "@services/auth";

interface MapState {
  mapView?: MapView;
  arcGISToken?: ArcGISToken;
  highlightHandle?: __esri.Handle;
  setMapView: (mapView?: MapView) => void;
  setHighlightHandle: (highlightHandle?: __esri.Handle) => void;
  getToken: () => Promise<void>;
  dropToken: () => void;
}

export const useMapStore = create<MapState>()(
  immer((set, get) => ({
    setMapView: (mapView) => {
      set({ mapView });
    },
    setHighlightHandle: (highlightHandle) => {
      const oldHandle = get().highlightHandle;
      if (oldHandle) {
        oldHandle.remove();
      }
      set({ highlightHandle });
    },
    getToken: async () => {
      const { data } = await getArcGISToken();
      set({ arcGISToken: data });
    },
    dropToken: () => {
      set({ arcGISToken: undefined, mapView: undefined });
    },
  }))
);
