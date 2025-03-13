import React, { ChangeEvent, useEffect, useState, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useDebounce } from "use-debounce";
import FeatureLayer from "@arcgis/core/layers/FeatureLayer";
import GroupLayer from "@arcgis/core/layers/GroupLayer";
import PopupTemplate from "@arcgis/core/PopupTemplate";
import SimpleFillSymbol from "@arcgis/core/symbols/SimpleFillSymbol";
import SimpleMarkerSymbol from "@arcgis/core/symbols/SimpleMarkerSymbol";
import FillSymbol from "@arcgis/core/symbols/FillSymbol";
import MarkerSymbol from "@arcgis/core/symbols/MarkerSymbol";
import Color from "@arcgis/core/Color";
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Box,
  Button,
  Chip,
  CircularProgress,
  IconButton,
  InputAdornment,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import VisibilityIcon from "@mui/icons-material/Visibility";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import CircleIcon from "@mui/icons-material/Circle";
import SearchIcon from "@mui/icons-material/Search";

import { useComparisonStore } from "@store/comparison.store";
import { useMapStore } from "@store/map.store";
import { LayerObjectList } from "@components/shared/layerObjectList";
import {
  ComparisonObjectGroup,
  ComparisonStatusGroup,
} from "@models/comparison";
import { getPopupTemplateContent } from "@models/arcgis";

const template = new PopupTemplate({
  content: getPopupTemplateContent,
  outFields: ["*"],
});

const getStatusColor = (
  type: string
): "primary" | "secondary" | "success" | "warning" | "error" => {
  switch (type) {
    case "added":
      return "primary";
    case "changed":
      return "success";
    case "deleted":
      return "error";
    case "unchanged":
      return "secondary";
    default:
      return "primary";
  }
};

export const ComparisonResultStep: React.FC<{ mapView: __esri.MapView }> = ({
  mapView,
}) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const comparison = useComparisonStore((state) => state.comparison);
  const theme = useTheme();

  const resultLayers = useRef<{ [key: string]: GroupLayer }>({});
  const mapViewInitiated = useRef(false);
  const [isLoading, setIsLoading] = useState(false);
  const [totalObjects, setTotalObjects] = useState(0);
  const [statusGroups, setStatusGroups] = useState<ComparisonStatusGroup[]>([]);
  const [objectGroups, setObjectGroups] = useState<ComparisonObjectGroup[]>([]);
  const [search, setSearch] = useState("");
  const [debouncedSearch] = useDebounce(search, 500);

  useEffect(() => {
    let clickHandle: IHandle;

    if (!mapViewInitiated.current) {
      mapViewInitiated.current = true;

      mapView.when(() => {
        clickHandle = mapView.on("click", async (event) => {
          const { results } = await mapView.hitTest(event);

          if (results.length > 1) {
            const resultLayerGraphicHit = results[0] as __esri.GraphicHit;
            const layerView = (await mapView.whenLayerView(
              resultLayerGraphicHit.layer
            )) as __esri.FeatureLayerView;

            if (layerView.highlight) {
              useMapStore
                .getState()
                .setHighlightHandle(
                  layerView.highlight(resultLayerGraphicHit.graphic)
                );
            }
          } else {
            useMapStore.getState().setHighlightHandle();
          }
        });
      });
    }

    return () => {
      const layersToRemove: __esri.Layer[] = [];
      resultLayers.current &&
        layersToRemove.push(...Object.values(resultLayers.current));
      resultLayers.current = {};

      mapView.map.removeMany(layersToRemove);
      mapView.graphics.removeAll();

      if (clickHandle && mapViewInitiated.current) {
        clickHandle.remove();
        mapViewInitiated.current = false;
      }
    };
  }, []);

  useEffect(() => {
    const queryObjects = async () => {
      setIsLoading(true);
      let total = 0;
      const query = debouncedSearch
        ? { where: `name LIKE '%${debouncedSearch}%'` }
        : undefined;
      const newGroups = [...objectGroups];
      for (const group of newGroups) {
        const count = await group.layer.queryFeatureCount(query);
        group.total = count;
        total += count;
      }

      setObjectGroups(newGroups);
      setTotalObjects(total);
      setIsLoading(false);
    };
    if (objectGroups.length) {
      queryObjects();
    }
  }, [debouncedSearch]);

  useEffect(() => {
    setStatusGroups([]);
    setObjectGroups([]);
    setTotalObjects(0);

    mapView.when(() => {
      mapView.map.removeAll();
    });

    if (comparison?.task_result?.layer_objects) {
      const stGroups: ComparisonStatusGroup[] = [];

      for (const [type, layerId] of Object.entries(
        comparison.task_result.layer_objects
      )) {
        const newGroupLayer = new GroupLayer({
          portalItem: {
            id: layerId,
          },
        });
        resultLayers.current[layerId] = newGroupLayer;

        stGroups.push({
          title: type,
          layer: newGroupLayer,
          isVisible: true,
        });

        mapView.when(() => {
          mapView.map.add(newGroupLayer);
        });

        newGroupLayer.when(async () => {
          let biggestExtent: __esri.Extent | undefined;
          let total = 0;

          for (const layer of newGroupLayer.allLayers) {
            if (layer instanceof FeatureLayer) {
              await layer.when(async () => {
                let symbol = layer.renderer.get("symbol") as
                  | FillSymbol
                  | MarkerSymbol;

                const count = await layer.queryFeatureCount();
                total += count;

                switch (symbol.type) {
                  case "simple-fill":
                    symbol = new SimpleFillSymbol({
                      color: new Color(
                        theme.palette[getStatusColor(type)].main
                      ),
                    });
                    break;
                  case "picture-marker":
                    symbol = new SimpleMarkerSymbol({
                      color: new Color(
                        theme.palette[getStatusColor(type)].main
                      ),
                      size: 5,
                    });
                    break;
                }
                layer.renderer.set("symbol", symbol);

                if (
                  !biggestExtent ||
                  (layer.fullExtent.height > biggestExtent.height &&
                    layer.fullExtent.width > biggestExtent.width)
                ) {
                  biggestExtent = layer.fullExtent;
                }

                setObjectGroups((groups) => [
                  ...groups,
                  {
                    title: `${t("comparison.group." + type)} ${layer.title}`,
                    layer,
                    isVisible: true,
                    total: count,
                  },
                ]);
              });

              layer.popupTemplate = template;
            }
          }

          setTotalObjects((t) => t + total);
          mapView.goTo(biggestExtent, { duration: 2000 });
        });
      }
      setStatusGroups(
        stGroups.sort((a, b) => {
          const titleA = a.title.toLowerCase();
          const titleB = b.title.toLowerCase();
          if (titleA < titleB) {
            return -1;
          }
          if (titleA > titleB) {
            return 1;
          }
          return 0;
        })
      );
    }
  }, [comparison?.task_result?.layer_objects]);

  const onCancel = () => {
    navigate("/projects/comparison");
  };

  const toggleGroupLayerVisibility = (
    e: React.MouseEvent<HTMLButtonElement, MouseEvent>,
    selectedGroup: ComparisonStatusGroup
  ) => {
    e.stopPropagation();

    selectedGroup.layer.set("visible", !selectedGroup.isVisible);
    setStatusGroups(
      statusGroups.map((group) => {
        if (group.title === selectedGroup.title) {
          return { ...group, isVisible: !selectedGroup.isVisible };
        } else {
          return group;
        }
      })
    );
  };

  const toggleObjectLayersVisibility = (
    e: React.MouseEvent<HTMLButtonElement, MouseEvent>,
    selectedGroup: ComparisonObjectGroup
  ) => {
    e.stopPropagation();

    selectedGroup.layer.set("visible", !selectedGroup.isVisible);

    setObjectGroups(
      objectGroups.map((group) => {
        if (group.title === selectedGroup.title) {
          return { ...group, isVisible: !selectedGroup.isVisible };
        } else {
          return group;
        }
      })
    );
  };

  const onSearchChange = (e: ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
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
          overflowX: "visible",
          overflowY: "auto",
        }}
      >
        {!!statusGroups.length && (
          <>
            <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
              {t("comparison.statuses")}
            </Typography>
            {statusGroups.map((group, index) => (
              <Box
                component="div"
                key={index}
                sx={{ display: "flex", alignItems: "center", gap: 1 }}
              >
                <IconButton
                  size="small"
                  onClick={(e) => toggleGroupLayerVisibility(e, group)}
                >
                  {group.isVisible ? (
                    <VisibilityIcon color="primary" fontSize="inherit" />
                  ) : (
                    <VisibilityOffIcon fontSize="inherit" />
                  )}
                </IconButton>
                <CircleIcon
                  color={getStatusColor(group.title)}
                  sx={{ fontSize: 12 }}
                />
                {t(`comparison.group.${group.title}`)}
              </Box>
            ))}
          </>
        )}
        {!!objectGroups.length && (
          <>
            <Box component="div" sx={{ py: 1, mt: 1 }}>
              <TextField
                label={t("general.search")}
                variant="outlined"
                size="small"
                value={search}
                onChange={onSearchChange}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
                sx={{ width: "100%" }}
                id="object-search"
              />
            </Box>
            <Box
              component="div"
              sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}
            >
              <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
                {t("project.objectsResultTitle")}
              </Typography>
              <Chip
                label={
                  isLoading ? <CircularProgress size="1rem" /> : totalObjects
                }
                variant="outlined"
                sx={{ ".MuiChip-label": { display: "flex" } }}
              />
            </Box>
            <Box
              component="div"
              sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}
            >
              <Box component="div">
                {comparison?.project_1.name}
                <br />
                {comparison?.project_1.date && (
                  <Typography fontSize={12}>
                    {t("intlDateTime", {
                      val: new Date(comparison?.project_1.date),
                      formatParams: {
                        val: {
                          year: "numeric",
                          month: "long",
                          day: "numeric",
                        },
                      },
                    })}
                  </Typography>
                )}
              </Box>
              <Box component="div" sx={{ textAlign: "right" }}>
                {comparison?.project_2.name}
                <br />
                {comparison?.project_2.date && (
                  <Typography fontSize={12}>
                    {t("intlDateTime", {
                      val: new Date(comparison?.project_2.date),
                      formatParams: {
                        val: {
                          year: "numeric",
                          month: "long",
                          day: "numeric",
                        },
                      },
                    })}
                  </Typography>
                )}
              </Box>
            </Box>
            <Box component="div" sx={{ p: 0.5, overflowY: "auto" }}>
              {objectGroups?.map((group, index) => (
                <Accordion
                  key={index}
                  TransitionProps={{ unmountOnExit: true }}
                >
                  <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    sx={{
                      ".MuiAccordionSummary-content": {
                        alignItems: "center",
                        justifyContent: "space-between",
                      },
                    }}
                    disabled={!group.total}
                  >
                    <Box component="div">
                      <IconButton
                        size="small"
                        onClick={(e) => toggleObjectLayersVisibility(e, group)}
                        sx={{
                          mr: 1,
                        }}
                      >
                        {group.isVisible ? (
                          <VisibilityIcon color="primary" fontSize="inherit" />
                        ) : (
                          <VisibilityOffIcon fontSize="inherit" />
                        )}
                      </IconButton>
                      {group.title}
                    </Box>
                    <Chip
                      label={group.total}
                      variant="outlined"
                      size="small"
                      sx={{ mr: 1 }}
                    />
                  </AccordionSummary>
                  <AccordionDetails>
                    <LayerObjectList
                      layer={group.layer}
                      search={debouncedSearch}
                      isComparison
                    />
                  </AccordionDetails>
                </Accordion>
              ))}
            </Box>
          </>
        )}
      </Box>
      <Box component="div" sx={{ px: 2, pb: 2 }}>
        <Button variant="outlined" fullWidth onClick={onCancel}>
          {t("general.cancel")}
        </Button>
      </Box>
    </>
  );
};
