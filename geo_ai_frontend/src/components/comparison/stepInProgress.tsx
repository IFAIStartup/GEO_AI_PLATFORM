import React, { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Box, Button, CircularProgress, Typography } from "@mui/material";
import { setIntervalAsync, clearIntervalAsync } from "set-interval-async";
import FeatureLayer from "@arcgis/core/layers/FeatureLayer";

import { useComparisonStore } from "@store/comparison.store";
import { useAlertStore } from "@store/alert.store";
import { addProjectFeatureLayer } from "@services/comparison";
import { ProjectStatus } from "@models/project";

export const ComparisonInProgressStep: React.FC<{
  mapView: __esri.MapView;
}> = ({ mapView }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const getComparison = useComparisonStore((state) => state.getComparison);
  const comparison = useComparisonStore((state) => state.comparison);
  const projects = useComparisonStore((state) => state.projects);
  const { setAlert } = useAlertStore();

  const projectFeatureLayers = useRef<FeatureLayer[]>([]);

  useEffect(() => {
    const interval = setIntervalAsync(async () => {
      if (comparison?.id) {
        const response = await getComparison(comparison.id);
        if (response.status === ProjectStatus.Error) {
          setAlert({
            severity: "error",
            key: "general.error",
          });
        }
      }
    }, 10000);

    return () => {
      const layersToRemove: __esri.Layer[] = [];
      projectFeatureLayers.current &&
        layersToRemove.push(
          ...projectFeatureLayers.current.filter((layer) => !!layer)
        );
      projectFeatureLayers.current = [];

      mapView.map.removeMany(layersToRemove);

      clearIntervalAsync(interval);
    };
  }, []);

  useEffect(() => {
    mapView.when(() => {
      mapView.map.removeAll();
    });

    projects
      .filter(
        (p) =>
          p.name === comparison?.project_1.name ||
          p.name === comparison?.project_2.name
      )
      .forEach((project, index) => {
        addProjectFeatureLayer(
          mapView,
          project,
          projectFeatureLayers,
          index === 0
        );
      });
  }, [projects]);

  const onCancel = () => {
    navigate("/projects/comparison");
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
          {t("comparison.loading")}
        </Typography>
      </Box>
      <Button variant="outlined" fullWidth onClick={onCancel}>
        {t("general.cancel")}
      </Button>
    </Box>
  );
};
