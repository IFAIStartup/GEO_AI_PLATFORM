import React, { useEffect, useRef } from "react";
import i18n from "i18next";
import Map from "@arcgis/core/Map";
import Basemap from "@arcgis/core/Basemap";
import TileLayer from "@arcgis/core/layers/TileLayer";
import MapView from "@arcgis/core/views/MapView";
import Search from "@arcgis/core/widgets/Search";
import BasemapToggle from "@arcgis/core/widgets/BasemapToggle";
import config from "@arcgis/core/config";
import IdentityManager from "@arcgis/core/identity/IdentityManager";
import { Box } from "@mui/material";

import { useMapStore } from "@store/map.store";

import terrainThumbUrl from "@assets/terrain_thumb.png";
import satelliteThumbUrl from "@assets/satellite_thumb.jpg";

const PORTAL_URL = import.meta.env.VITE_ARCGIS_PORTAL_URL;
const CUSTOM_BASEMAP = import.meta.env.VITE_ARCGIS_BASEMAP;
const CUSTOM_BASEMAP_SECONDARY = import.meta.env.VITE_ARCGIS_BASEMAP_SECONDARY;

export const ArcGISMap: React.FC = () => {
  const mapDiv = useRef<HTMLDivElement | undefined>();

  const arcGISToken = useMapStore((state) => state.arcGISToken);
  const getToken = useMapStore((state) => state.getToken);
  const dropToken = useMapStore((state) => state.dropToken);
  const setMapView = useMapStore((state) => state.setMapView);

  useEffect(() => {
    let expiresTimer: NodeJS.Timeout;

    if (arcGISToken) {
      IdentityManager.registerToken({
        server: PORTAL_URL + "/sharing/rest",
        token: arcGISToken.token,
      });

      const expiresIn = +arcGISToken.expires - new Date().getTime();
      expiresTimer = setInterval(() => {
        dropToken();
      }, expiresIn);

      config.portalUrl = PORTAL_URL;

      // Map View
      const mapView = new MapView({
        container: mapDiv.current,
        map: new Map({
          basemap: getBasemap(),
        }),
        popup: {
          dockEnabled: true,
          dockOptions: {
            position: "bottom-right",
            breakpoint: false,
          },
        },
      });

      mapView.ui.move("zoom", "bottom-right");

      const search = new Search({ view: mapView });
      mapView.ui.add(search, "bottom-left");

      const toggle = new BasemapToggle({
        visibleElements: {
          title: true,
        },
        view: mapView,
        nextBasemap: getSecondaryBasemap(),
      });
      mapView.ui.add(toggle, {
        position: "top-right",
      });

      mapView.when(() => {
        mapView.goTo({
          center: [54.6, 25.3],
          zoom: 8,
        });
      });

      setMapView(mapView);
    } else {
      getToken();
    }

    return () => {
      if (expiresTimer) {
        clearInterval(expiresTimer);
      }
    };
  }, [arcGISToken]);

  return <Box component="div" sx={{ height: "100%" }} ref={mapDiv}></Box>;
};

const getBasemap = () => {
  let basemap: string | Basemap = "arcgis-topographic";

  if (CUSTOM_BASEMAP) {
    basemap = new Basemap({
      baseLayers: [
        new TileLayer({
          url: CUSTOM_BASEMAP,
        }),
      ],
      title: i18n.t("map.terrain"),
      id: "terrain",
      thumbnailUrl: terrainThumbUrl,
    });
  }

  return basemap;
};

const getSecondaryBasemap = () => {
  let basemap: string | Basemap = "satellite";

  if (CUSTOM_BASEMAP_SECONDARY) {
    basemap = new Basemap({
      baseLayers: [
        new TileLayer({
          url: CUSTOM_BASEMAP_SECONDARY,
        }),
      ],
      title: i18n.t("map.imagery"),
      id: "satellite",
      thumbnailUrl: satelliteThumbUrl,
    });
  }

  return basemap;
};
