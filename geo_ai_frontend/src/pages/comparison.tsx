import React, { useEffect } from "react";
import { Navigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Box, Grid, Typography } from "@mui/material";

import { useComparisonStore } from "@store/comparison.store";
import { useMapStore } from "@store/map.store";
import { ProjectStatus } from "@models/project";
import { ArcGISMap } from "@components/map/map";
import { ComparisonInitialStep } from "@components/comparison/stepInitial";
import { ComparisonInProgressStep } from "@components/comparison/stepInProgress";
import { ComparisonResultStep } from "@components/comparison/stepResult";

export const ComparisonPage: React.FC = () => {
  const { comparisonId } = useParams();
  const { t } = useTranslation();

  const { setMapView, mapView } = useMapStore();
  const comparison = useComparisonStore((state) => state.comparison);
  const dropComparisonData = useComparisonStore(
    (state) => state.dropComparisonData
  );
  const getFinishedProjects = useComparisonStore(
    (state) => state.getFinishedProjects
  );
  const getComparison = useComparisonStore((state) => state.getComparison);

  useEffect(() => {
    getFinishedProjects();

    return () => {
      dropComparisonData();
      setMapView();
    };
  }, []);

  useEffect(() => {
    if (comparisonId && comparisonId !== "0") {
      getComparison(+comparisonId);
    }
  }, [comparisonId]);

  return (
    <Grid container sx={{ height: "calc(100vh - 64px)" }} dir="ltr">
      <Grid
        item
        xs={3}
        sx={{
          display: "flex",
          flexDirection: "column",
          borderRight: "1px solid rgba(0, 0, 0, 0.12)",
          height: "100%",
        }}
      >
        {mapView && (
          <>
            {(!comparison || comparison.status === ProjectStatus.Initial) && (
              <ComparisonInitialStep mapView={mapView} />
            )}
            {comparison?.status === ProjectStatus.InProgress && (
              <ComparisonInProgressStep mapView={mapView} />
            )}
            {comparison?.status === ProjectStatus.Finished && (
              <ComparisonResultStep mapView={mapView} />
            )}
            {comparison?.status === ProjectStatus.Error && (
              <Navigate to="/projects/comparison" replace />
            )}
          </>
        )}
      </Grid>
      <Grid item xs={9} sx={{ display: "flex", flexDirection: "column" }}>
        <Box
          component="div"
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            px: 3,
            py: 2,
            borderBottom: "1px solid rgba(0, 0, 0, 0.12)",
          }}
        >
          <Typography variant="h6" sx={{ fontWeight: "bold" }}>
            {comparison && (
              <>
                {comparison.project_1.name} {t("comparison.titleJoin")}{" "}
                {comparison.project_2.name}
              </>
            )}{" "}
            {t("comparison.title")}
          </Typography>
        </Box>
        <Box component="div" sx={{ flexGrow: 1 }}>
          <ArcGISMap />
        </Box>
      </Grid>
    </Grid>
  );
};
