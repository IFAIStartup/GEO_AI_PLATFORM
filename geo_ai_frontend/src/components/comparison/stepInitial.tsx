import React, { useState, ChangeEvent, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  Checkbox,
  InputAdornment,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  TextField,
  Typography,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import FeatureLayer from "@arcgis/core/layers/FeatureLayer";
import PictureMarkerSymbol from "@arcgis/core/symbols/PictureMarkerSymbol";
import Graphic from "@arcgis/core/Graphic";

import selectedImageIcon from "@assets/map_file_icon_selected.svg";

import { useComparisonStore } from "@store/comparison.store";
import { Project, ProjectType } from "@models/project";
import { addProjectFeatureLayer } from "@services/comparison";

const selectedSymbol = new PictureMarkerSymbol({
  url: selectedImageIcon,
  width: "24px",
  height: "24px",
});

export const ComparisonInitialStep: React.FC<{ mapView: __esri.MapView }> = ({
  mapView,
}) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const startComparison = useComparisonStore((state) => state.startComparison);
  const projects = useComparisonStore((state) => state.projects);

  const [search, setSearch] = useState("");
  const [filteredProjects, setFilteredProjects] = useState<Project[]>([]);
  const [selectedType, setSelectedType] = useState<ProjectType | null>(null);
  const [selectedProjectIds, setSelectedProjectIds] = useState<number[]>([]);

  const projectFeatureLayers = useRef<FeatureLayer[]>([]);

  useEffect(() => {
    return () => {
      const layersToRemove: __esri.Layer[] = [];
      projectFeatureLayers.current &&
        layersToRemove.push(
          ...projectFeatureLayers.current.filter((layer) => !!layer)
        );
      projectFeatureLayers.current = [];

      mapView.map.removeMany(layersToRemove);
      mapView.graphics.removeAll();
    };
  }, []);

  useEffect(() => {
    setSelectedProjectIds([]);
    mapView.when(() => {
      mapView.map.removeAll();
    });

    filteredProjects.forEach((project, index) => {
      addProjectFeatureLayer(
        mapView,
        project,
        projectFeatureLayers,
        index === 0
      );
    });
  }, [filteredProjects]);

  useEffect(() => {
    mapView.when(() => {
      mapView.graphics.removeAll();
    });

    selectedProjectIds.forEach((id) => {
      const layer = projectFeatureLayers.current[id];
      if (layer) {
        layer.when(async () => {
          const firstFeatureSet = await layer.queryFeatures();
          const features = firstFeatureSet.features;
          let exceededTransferLimit = firstFeatureSet.exceededTransferLimit;

          while (exceededTransferLimit) {
            const {
              features: additionalFeatures,
              exceededTransferLimit: stillExceeded,
            } = await layer.queryFeatures({
              start: features.length,
              num: 1000,
              outFields: ["*"],
              returnGeometry: true,
            });
            features.push(...additionalFeatures);
            exceededTransferLimit = stillExceeded;
          }

          features.forEach((feature) => {
            const selected = new Graphic({
              geometry: feature.geometry,
              symbol: selectedSymbol,
            });
            mapView.graphics.add(selected);
          });
        });
      }
    });
  }, [selectedProjectIds]);

  useEffect(() => {
    setFilteredProjects(
      projects.filter(
        (p) =>
          p.name.includes(search) &&
          (p.ml_model?.length || p.ml_model_deeplab?.length)
      )
    );
  }, [projects, search]);

  const onCancel = () => {
    navigate("/projects/comparison");
  };

  const onSearchChange = (e: ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
  };

  const onStartComparison = () => {
    startComparison(selectedProjectIds).then((comparisonId) => {
      navigate(`/projects/comparison/${comparisonId}`);
    });
  };

  const onListItemClick = (project: Project) => {
    const currentIndex = selectedProjectIds.indexOf(project.id);
    const newSelected = [...selectedProjectIds];

    if (currentIndex === -1) {
      setSelectedType(project.type);
      newSelected.push(project.id);
    } else {
      newSelected.splice(currentIndex, 1);
      if (!newSelected.length) {
        setSelectedType(null);
      }
    }

    setSelectedProjectIds(newSelected);
  };

  return (
    <>
      <Box
        component="div"
        sx={{
          display: "flex",
          flexDirection: "column",
          flexGrow: 1,
          mx: 2,
          my: 3,
          gap: 3,
          overflowX: "visible",
          overflowY: "auto",
        }}
      >
        <Box component="div">
          <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
            {t("comparison.projectSelectionTitle")}
          </Typography>
          <Typography variant="body1" sx={{ opacity: 0.6 }}>
            {t("comparison.projectSelectionSubTitle")}
          </Typography>
        </Box>
        <TextField
          label={t("general.search")}
          variant="outlined"
          size="small"
          value={search}
          onChange={onSearchChange}
          fullWidth
          disabled={!projects.length}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
        {!filteredProjects.length && (
          <Typography sx={{ textAlign: "center" }}>
            {t("project.noProjects")}
          </Typography>
        )}
        <List dense sx={{ overflowY: "auto" }}>
          {filteredProjects.map((project) => (
            <ListItem disablePadding key={project.id} sx={{ px: 0 }}>
              <ListItemButton
                onClick={() => onListItemClick(project)}
                disabled={
                  (!!selectedType && project.type !== selectedType) ||
                  (selectedProjectIds.length >= 2 &&
                    selectedProjectIds.indexOf(project.id) === -1)
                }
              >
                <ListItemIcon sx={{ minWidth: "auto", mr: 1 }}>
                  <Checkbox
                    edge="start"
                    tabIndex={-1}
                    disableRipple
                    checked={selectedProjectIds.indexOf(project.id) !== -1}
                  />
                </ListItemIcon>
                <ListItemText
                  primary={project.name}
                  primaryTypographyProps={{ fontWeight: "bold" }}
                  secondary={t("intlDateTime", {
                    val: new Date(project.date),
                    formatParams: {
                      val: {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                        hour: "numeric",
                        minute: "numeric",
                      },
                    },
                  })}
                  sx={{ wordWrap: "break-word" }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>
      <Box
        component="div"
        sx={{
          display: "flex",
          flexDirection: "column",
          gap: 1.5,
          px: 2,
          pb: 2,
        }}
      >
        <Button
          variant="contained"
          fullWidth
          onClick={onStartComparison}
          disabled={selectedProjectIds.length !== 2}
        >
          {t("comparison.startComparisonButton")}
        </Button>
        <Button variant="outlined" fullWidth onClick={onCancel}>
          {t("general.cancel")}
        </Button>
      </Box>
    </>
  );
};
