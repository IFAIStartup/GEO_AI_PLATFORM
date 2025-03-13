import React, { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import { Grid, Box, CircularProgress, Typography, Button } from "@mui/material";

import { useMapStore } from "@store/map.store";
import { useProjectStore } from "@store/project.store";
import {
  MapFilesTogglePosition,
  ProjectStatus,
  ProjectType,
} from "@models/project";
import { ArcGISMap } from "@components/map/map";
import { ProjectImageList } from "@components/project/projectImageList";
import { ProjectPointCloudGroupList } from "@components/project/projectPointCloudGroupList";
import { ProjectInitialStep } from "@components/project/stepInitial";
import { ProjectInProgressStep } from "@components/project/stepInProgress";
import { ProjectResultStep } from "@components/project/stepResult";
import { MapFilesToggle } from "@components/project/mapToggle";
import { useUserStore } from "@store/user.store";

export const ProjectPage: React.FC = () => {
  const { t } = useTranslation();
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { mapView, setMapView } = useMapStore();
  const mapFilesToggle = useUserStore(
    (state) => state.preferences.mapFilesToggle
  );
  const project = useProjectStore((state) => state.project);
  const getProject = useProjectStore((state) => state.getProject);
  const dropProjectData = useProjectStore((state) => state.dropProjectData);

  useEffect(() => {
    return () => {
      dropProjectData();
      setMapView();
    };
  }, []);

  useEffect(() => {
    if (projectId) {
      getProject(+projectId).catch(() => {
        navigate("/not-found");
      });
    }
  }, [projectId]);

  if (!project.id) {
    return (
      <Box
        component="div"
        sx={{ display: "flex", justifyContent: "center", pt: 12 }}
      >
        <CircularProgress size="60px" />
      </Box>
    );
  }

  const getArcGISUrl = () => {
    let url = import.meta.env.VITE_ARCGIS_PORTAL_URL + "/home/item.html?id=";

    if (project.status === ProjectStatus.Finished) {
      url += project.task_result?.layer_id;
    } else {
      url += project.preview_layer_id;
    }

    return url;
  };

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
            {project.status === ProjectStatus.Initial && (
              <ProjectInitialStep mapView={mapView} />
            )}
            {project.status === ProjectStatus.InProgress && (
              <ProjectInProgressStep mapView={mapView} />
            )}
            {project.status === ProjectStatus.Finished && (
              <ProjectResultStep mapView={mapView} />
            )}
            {project.status === ProjectStatus.Error && (
              <Navigate to="/projects" replace />
            )}
          </>
        )}
      </Grid>
      <Grid
        item
        xs={9}
        sx={{
          display: "flex",
          flexDirection: "column",
          height: "100%",
        }}
      >
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
          <Box
            component="div"
            sx={{
              display: "flex",
              alignItems: "baseline",
              flexWrap: "wrap",
              gap: 2,
            }}
          >
            <Typography variant="h6" sx={{ fontWeight: "bold" }}>
              {project.name}
            </Typography>
            <Button
              variant="text"
              href={getArcGISUrl()}
              target="_blank"
              size="small"
            >
              {t("project.arcGISLink")}
            </Button>
          </Box>
          <MapFilesToggle />
        </Box>
        <Box
          component="div"
          sx={{
            display: "flex",
            flexDirection: "column",
            flexGrow: 1,
            overflow: "hidden",
          }}
        >
          <Box
            component="div"
            sx={{
              p: mapFilesToggle === MapFilesTogglePosition.MAP ? 0 : 3,
              backgroundColor: "#E9E9E9",
              overflow: "auto",
              height:
                mapFilesToggle === MapFilesTogglePosition.IMAGES
                  ? "calc(100% - 1px)"
                  : mapFilesToggle === MapFilesTogglePosition.BOTH
                  ? "50%"
                  : 0,
            }}
          >
            {project.areFilesLoading && (
              <Box
                component="div"
                sx={{ display: "flex", justifyContent: "center" }}
              >
                <CircularProgress />
              </Box>
            )}
            {project.type === ProjectType.Panorama ? (
              <ProjectPointCloudGroupList />
            ) : (
              <ProjectImageList />
            )}
          </Box>

          <Box
            component="div"
            sx={{
              height:
                mapFilesToggle === MapFilesTogglePosition.IMAGES
                  ? "1px"
                  : mapFilesToggle === MapFilesTogglePosition.BOTH
                  ? "50%"
                  : "100%",
            }}
          >
            <ArcGISMap />
          </Box>
        </Box>
      </Grid>
    </Grid>
  );
};
