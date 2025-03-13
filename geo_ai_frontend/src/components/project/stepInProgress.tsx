import React, { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Box, Button, CircularProgress, Typography } from "@mui/material";
import { setIntervalAsync, clearIntervalAsync } from "set-interval-async";
import FeatureLayer from "@arcgis/core/layers/FeatureLayer";
import PictureMarkerSymbol from "@arcgis/core/symbols/PictureMarkerSymbol";
import SimpleRenderer from "@arcgis/core/renderers/SimpleRenderer";

import imageIcon from "@assets/map_image_icon.svg";
import pcdIcon from "@assets/map_pcd_icon.svg";

import { useProjectStore } from "@store/project.store";
import { useAlertStore } from "@store/alert.store";
import { ProjectStatus, ProjectType } from "@models/project";

const imageSymbol = new PictureMarkerSymbol({
  url: imageIcon,
  width: "24px",
  height: "24px",
});
const pcdSymbol = new PictureMarkerSymbol({
  url: pcdIcon,
  width: "24px",
  height: "24px",
});

export const ProjectInProgressStep: React.FC<{ mapView: __esri.MapView }> = ({
  mapView,
}) => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const getProject = useProjectStore((state) => state.getProject);
  const project = useProjectStore((state) => state.project);
  const { setAlert } = useAlertStore();

  const featureLayer = useRef<FeatureLayer>();

  useEffect(() => {
    const interval = setIntervalAsync(async () => {
      if (project.id) {
        const response = await getProject(project.id);
        if (response.status === ProjectStatus.Error) {
          setAlert({
            severity: "error",
            key: "general.error",
          });
        }
      }
    }, 10000);

    return () => {
      clearIntervalAsync(interval);
      const layersToRemove: __esri.Layer[] = [];
      featureLayer.current && layersToRemove.push(featureLayer.current);
      featureLayer.current = undefined;

      mapView.map.removeMany(layersToRemove);
    };
  }, []);

  useEffect(() => {
    if (project.preview_layer_id && !featureLayer.current) {
      const symbol =
        project.type === ProjectType.Panorama ? pcdSymbol : imageSymbol;
      const imageLayerRenderer = new SimpleRenderer({ symbol });
      const layer = new FeatureLayer({
        renderer: imageLayerRenderer,
        portalItem: {
          id: project.preview_layer_id,
        },
        outFields: ["*"],
      });
      featureLayer.current = layer;

      mapView.when(() => {
        mapView.map.add(layer);
      });
    }

    featureLayer.current?.when(async () => {
      if (!featureLayer.current) {
        return;
      }

      mapView.goTo(
        {
          center: featureLayer.current.fullExtent.center,
          zoom: 14,
        },
        { duration: 2000 }
      );
    });
  }, [project.preview_layer_id]);

  const onCancel = () => {
    navigate("/projects");
  };

  return (
    <Box
      component="div"
      sx={{ display: "flex", flexDirection: "column", flexGrow: 1, p: 2 }}
    >
      <Box
        component="div"
        sx={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: 4,
          flexGrow: 1,
        }}
      >
        <CircularProgress size={60} />
        <Typography
          variant="h6"
          sx={{ fontWeight: "bold", textAlign: "center" }}
        >
          {t("project.loading")}
        </Typography>
      </Box>
      <Button variant="outlined" fullWidth onClick={onCancel}>
        {t("general.cancel")}
      </Button>
    </Box>
  );
};
