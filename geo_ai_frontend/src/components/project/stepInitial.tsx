import React, { MouseEvent, useEffect, ChangeEvent, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { setIntervalAsync, clearIntervalAsync } from "set-interval-async";
import {
  Box,
  Button,
  Typography,
  FormGroup,
  FormControl,
  FormControlLabel,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  ToggleButtonGroup,
  ToggleButton,
  SelectChangeEvent,
} from "@mui/material";
import FeatureLayer from "@arcgis/core/layers/FeatureLayer";
import PictureMarkerSymbol from "@arcgis/core/symbols/PictureMarkerSymbol";
import SimpleRenderer from "@arcgis/core/renderers/SimpleRenderer";

import { useProjectStore } from "@store/project.store";
import { ProjectType } from "@models/project";

import imageIcon from "@assets/map_image_icon.svg";
import pcdIcon from "@assets/map_pcd_icon.svg";
import { ApiError } from "@models/common";
import { handleError } from "@services/http";

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

export const ProjectInitialStep: React.FC<{ mapView: __esri.MapView }> = ({
  mapView,
}) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const project = useProjectStore((state) => state.project);
  const availableModelTypes = useProjectStore(
    (state) => state.availableModelTypes
  );
  const availableModelViews = useProjectStore(
    (state) => state.availableModelViews
  );
  const imageQualities = useProjectStore((state) => state.imageQualities);
  const toggleAllFiles = useProjectStore((state) => state.toggleAllFiles);
  const setImageQuality = useProjectStore((state) => state.setImageQuality);
  const selectMLModelType = useProjectStore((state) => state.selectMLModelType);
  const selectMLModelView = useProjectStore((state) => state.selectMLModelView);
  const startDetection = useProjectStore((state) => state.startDetection);
  const getImageQualities = useProjectStore((state) => state.getImageQualities);
  const getProject = useProjectStore((state) => state.getProject);
  const getAvailableMLModelTypes = useProjectStore(
    (state) => state.getAvailableMLModelTypes
  );
  const getAvailableMLModelViews = useProjectStore(
    (state) => state.getAvailableMLModelViews
  );

  const featureLayer = useRef<FeatureLayer>();
  const initialRender = useRef(false);

  useEffect(() => {
    let clickHandle: IHandle;

    if (!initialRender.current) {
      initialRender.current = true;

      getImageQualities();
      getAvailableMLModelTypes();
      getAvailableMLModelViews();

      mapView.when(() => {
        clickHandle = mapView.on("click", async (event) => {
          const projectState = useProjectStore.getState();
          const { results } = await mapView.hitTest(event);

          const featureLayerGraphicHit = results.find(
            (r) => r.layer === featureLayer.current
          ) as __esri.GraphicHit;

          if (featureLayerGraphicHit) {
            const image = projectState.project.images?.find(
              (img) =>
                img.name == featureLayerGraphicHit.graphic.attributes.name
            );
            const group = projectState.project.pointCloudGroups?.find(
              (group) =>
                group.title == featureLayerGraphicHit.graphic.attributes.title
            );

            if (image) {
              projectState.toggleImage(image.path);
            }

            if (group) {
              projectState.togglePointCloudGroup(group.title);
            }
          }
        });
      });
    }

    const interval = setIntervalAsync(async () => {
      if (useProjectStore.getState().project.areFilesLoading) {
        await getProject(project.id);
      } else {
        clearIntervalAsync(interval);
      }
    }, 5000);

    return () => {
      const layersToRemove: __esri.Layer[] = [];
      featureLayer.current && layersToRemove.push(featureLayer.current);
      featureLayer.current = undefined;

      mapView.map.removeMany(layersToRemove);
      mapView.graphics.removeAll();

      if (clickHandle && initialRender.current) {
        clickHandle.remove();
        initialRender.current = false;
      }
      clearIntervalAsync(interval);
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
    }
  }, [project.preview_layer_id]);

  useEffect(() => {
    if (!project.areFilesLoading && featureLayer.current) {
      featureLayer.current.when(async () => {
        if (!featureLayer.current) {
          return;
        }

        const firstFeatureSet = await featureLayer.current.queryFeatures();
        const features = firstFeatureSet.features;
        let exceededTransferLimit = firstFeatureSet.exceededTransferLimit;

        while (exceededTransferLimit) {
          const {
            features: additionalFeatures,
            exceededTransferLimit: stillExceeded,
          } = await featureLayer.current.queryFeatures({
            start: features.length,
            num: 1000,
            outFields: ["*"],
            returnGeometry: true,
          });
          features.push(...additionalFeatures);
          exceededTransferLimit = stillExceeded;
        }

        if (project.type === ProjectType.Panorama) {
          useProjectStore.getState().mapFeaturesToPointCloudGroups(features);
        } else {
          useProjectStore.getState().mapFeaturesToImages(features);
        }
      });
    }
  }, [project.areFilesLoading]);

  const onSelectAllChange = (event: ChangeEvent<HTMLInputElement>) => {
    toggleAllFiles(event.target.checked);
  };

  const onModelTypeChange = (e: SelectChangeEvent<string[]>) => {
    const {
      target: { value },
    } = e;
    selectMLModelType(typeof value === "string" ? value.split(",") : value);
  };

  const onModelViewChange = (e: SelectChangeEvent<string[]>) => {
    const {
      target: { value },
    } = e;
    selectMLModelView(typeof value === "string" ? value.split(",") : value);
  };

  const onQualityChange = (_: MouseEvent<HTMLElement>, value: string) => {
    setImageQuality(value);
  };

  const onCancel = () => {
    navigate("/projects");
  };

  const onStartDetection = () => {
    startDetection().catch((e: ApiError) => {
      handleError(e);
    });
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
        }}
      >
        <Box component="div">
          <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
            {t("project.areaSettingTitle")}
          </Typography>
          <Typography variant="body1" sx={{ opacity: 0.6 }}>
            {t("project.areaSettingSubtitle")}
          </Typography>
          <FormGroup>
            <FormControlLabel
              control={
                <Checkbox
                  checked={project.allFilesSelected || false}
                  onChange={onSelectAllChange}
                  disabled={project.areFilesLoading}
                />
              }
              label={t("general.selectAll")}
            />
          </FormGroup>
        </Box>
        <Box component="div">
          <Typography variant="subtitle1">
            {t("project.mlSettingTitle1")}
          </Typography>
          <FormControl fullWidth sx={{ mt: 1 }}>
            <InputLabel id="ml-model-select-label">
              {t("project.mlSettingTitle1")}
            </InputLabel>
            <Select
              labelId="ml-model-select-label"
              value={project.selectedModelTypes}
              label={t("project.mlSettingTitle1")}
              onChange={onModelTypeChange}
              disabled={!availableModelTypes.length}
              multiple
            >
              {availableModelTypes.map((model) => (
                <MenuItem key={model.id} value={model.name}>
                  {model.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
        <Box component="div">
          <Typography variant="subtitle1">
            {t("project.mlSettingTitle2")}
          </Typography>
          <FormControl fullWidth sx={{ mt: 1 }}>
            <InputLabel id="ml-model-select-view-label">
              {t("project.mlSettingTitle2")}
            </InputLabel>
            <Select
              labelId="ml-model-select-view-label"
              value={project.selectedModelViews}
              label={t("project.mlSettingTitle2")}
              onChange={onModelViewChange}
              disabled={!availableModelViews.length}
              multiple
            >
              {availableModelViews.map((model) => (
                <MenuItem key={model.id} value={model.name}>
                  {model.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
        {project.type !== ProjectType.Panorama && (
          <Box component="div">
            <Typography variant="subtitle1">
              {t("project.qualitySettingTitle")}
            </Typography>
            <Typography variant="body1" sx={{ opacity: 0.6 }}>
              {t("project.qualitySettingSubtitle")}
            </Typography>
            <ToggleButtonGroup
              value={project.imageQuality}
              onChange={onQualityChange}
              exclusive
              fullWidth
              sx={{ mt: 1 }}
            >
              {!!imageQualities &&
                Object.entries(imageQualities).map(([key, value]) => (
                  <ToggleButton
                    key={value}
                    value={value}
                    sx={{ textTransform: "lowercase" }}
                  >
                    {key}
                  </ToggleButton>
                ))}
            </ToggleButtonGroup>
          </Box>
        )}
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
          onClick={onStartDetection}
          disabled={
            !project.someFilesSelected ||
            (project.type === ProjectType.Panorama &&
              !project.selectedModelTypes.length &&
              !project.selectedModelViews.length)
          }
        >
          {t("project.detectionButton")}
        </Button>
        <Button variant="outlined" fullWidth onClick={onCancel}>
          {t("general.cancel")}
        </Button>
      </Box>
    </>
  );
};
