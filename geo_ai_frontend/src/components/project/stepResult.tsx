import React, { useEffect, useState, useRef, ChangeEvent } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useDebounce } from "use-debounce";
import GroupLayer from "@arcgis/core/layers/GroupLayer";
import FeatureLayer from "@arcgis/core/layers/FeatureLayer";
import PopupTemplate from "@arcgis/core/PopupTemplate";
import Collection from "@arcgis/core/core/Collection";
import Editor from "@arcgis/core/widgets/Editor";
import FieldElement from "@arcgis/core/form/elements/FieldElement";
import FormTemplate from "@arcgis/core/form/FormTemplate";
import * as reactiveUtils from "@arcgis/core/core/reactiveUtils";
import {
  Box,
  Button,
  IconButton,
  Typography,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  TextField,
  InputAdornment,
  CircularProgress,
} from "@mui/material";
import VisibilityIcon from "@mui/icons-material/Visibility";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import SearchIcon from "@mui/icons-material/Search";

import { useProjectStore } from "@store/project.store";
import { useMapStore } from "@store/map.store";
import { DetectionResultGroup } from "@models/project";
import { getPopupTemplateContent } from "@models/arcgis";
import { LayerObjectList } from "@components/shared/layerObjectList";

const getPopupTemplateActions = () => {
  const collection = new Collection();
  const editThisAction = {
    title: "Edit feature",
    id: "edit-this",
    className: "esri-icon-edit",
  };

  collection.add(editThisAction);

  return collection;
};

const template = new PopupTemplate({
  actions: getPopupTemplateActions(),
  content: getPopupTemplateContent,
  outFields: ["*"],
});

export const ProjectResultStep: React.FC<{ mapView: __esri.MapView }> = ({
  mapView,
}) => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const project = useProjectStore((state) => state.project);

  const resultLayer = useRef<GroupLayer>();
  const editor = useRef<Editor>();
  const mapViewInitiated = useRef(false);
  const [totalObjects, setTotalObjects] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [groups, setGroups] = useState<DetectionResultGroup[]>([]);
  const [search, setSearch] = useState("");
  const [debouncedSearch] = useDebounce(search, 500);

  useEffect(() => {
    let clickHandle: IHandle;
    let popupHandle: IHandle;
    let popupWatchHandle: IHandle;

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

          if (editor.current?.activeWorkflow) {
            editor.current.viewModel.cancelWorkflow();
          }
        });

        popupHandle = reactiveUtils.on(
          () => mapView.popup,
          "trigger-action",
          (event) => {
            if (event.action.id !== "edit-this" || !editor.current) {
              return;
            }

            if (!editor.current.activeWorkflow) {
              editor.current
                .startUpdateWorkflowAtFeatureEdit(mapView.popup.selectedFeature)
                .then(() => {
                  mapView.closePopup();
                  mapView.popup.clear();
                });
            } else {
              editor.current.cancelWorkflow().then(() => {
                editor.current
                  ?.startUpdateWorkflowAtFeatureEdit(
                    mapView.popup.selectedFeature
                  )
                  .then(() => {
                    mapView.closePopup();
                    mapView.popup.clear();
                  });
              });
            }
          }
        );
      });

      popupWatchHandle = reactiveUtils.watch(
        () => mapView.popup?.visible,
        (n) => {
          if (!n && editor.current?.viewModel.state !== "editing-attributes") {
            useMapStore.getState().setHighlightHandle();
          }
        }
      );
    }

    return () => {
      const layersToRemove: __esri.Layer[] = [];
      resultLayer.current && layersToRemove.push(resultLayer.current);
      resultLayer.current = undefined;

      mapView.when(() => {
        mapView.map.removeMany(layersToRemove);
        mapView.graphics.removeAll();
      });

      if (mapViewInitiated.current) {
        clickHandle?.remove();
        popupHandle?.remove();
        popupWatchHandle?.remove();
        mapViewInitiated.current = false;
      }
    };
  }, []);

  useEffect(() => {
    const queryGroups = async () => {
      setIsLoading(true);
      let total = 0;
      const query = debouncedSearch
        ? { where: `name LIKE '%${debouncedSearch}%'` }
        : undefined;
      const newGroups = [...groups];
      for (const group of newGroups) {
        const count = await group.layer.queryFeatureCount(query);
        group.total = count;
        total += count;
      }

      setGroups(newGroups);
      setTotalObjects(total);
      setIsLoading(false);
    };

    if (groups.length) {
      queryGroups();
    }
  }, [debouncedSearch]);

  useEffect(() => {
    const eventHandles: IHandle[] = [];

    if (project.task_result?.layer_id && !resultLayer.current) {
      resultLayer.current = new GroupLayer({
        portalItem: {
          id: project.task_result.layer_id,
        },
      });

      mapView.when(() => {
        if (!resultLayer.current) {
          return;
        }

        mapView.map.add(resultLayer.current);
      });

      resultLayer.current.when(async () => {
        if (!resultLayer.current) {
          return;
        }

        let total = 0;
        const groups: DetectionResultGroup[] = [];
        let biggestExtent: __esri.Extent | undefined;
        const layerInfos: __esri.LayerInfo[] = [];

        for (const layer of resultLayer.current.allLayers) {
          if (layer instanceof FeatureLayer) {
            const count = await layer.queryFeatureCount();
            total += count;
            if (
              !biggestExtent ||
              (layer.fullExtent.height > biggestExtent.height &&
                layer.fullExtent.width > biggestExtent.width)
            ) {
              biggestExtent = layer.fullExtent;
            }

            groups.push({
              title: layer.title,
              isVisible: true,
              total: count,
              layer,
            });

            layer.popupTemplate = template;

            const nameElement = new FieldElement({
              label: "Name",
              fieldName: "name",
            });
            const formTemplate = new FormTemplate({
              elements: [nameElement],
            });
            layerInfos.push({
              layer,
              formTemplate,
            });

            const eventHandle = layer.on("edits", (e) => {
              if (editor.current?.activeWorkflow) {
                editor.current.cancelWorkflow().then(async () => {
                  if (e.updatedFeatures.length) {
                    const featureSet = await layer.queryFeatures({
                      where: `FID = '${e.updatedFeatures[0].objectId}'`,
                      outFields: ["*"],
                      returnGeometry: true,
                    });
                    mapView.openPopup({
                      features: featureSet.features,
                    });
                  }
                });
              }
            });

            eventHandles.push(eventHandle);
          }
        }

        editor.current = new Editor({
          view: mapView,
          visibleElements: {
            snappingControls: false,
            tooltipsToggle: false,
            createFeaturesSection: false,
          },
          visible: false,
          container: document.createElement("div"),
          layerInfos,
        });
        mapView.ui.add(editor.current, "bottom-right");

        const editorWatchHandle = reactiveUtils.watch(
          () => editor.current?.viewModel.state,
          (state, oldState) => {
            if (!editor.current) {
              return;
            }
            editor.current.visible = state === "editing-attributes";
            if (oldState === "editing-attributes" && state === "ready") {
              useMapStore.getState().setHighlightHandle();
            }
          }
        );
        eventHandles.push(editorWatchHandle);

        mapView.goTo(biggestExtent, { duration: 2000 });

        groups.sort((a, b) => {
          if (a.title > b.title) {
            return 1;
          }
          if (a.title < b.title) {
            return -1;
          }
          return 0;
        });

        setTotalObjects(total);
        setGroups(groups);
        setIsLoading(false);
      });

      return () => {
        eventHandles.forEach((e) => {
          e.remove();
        });
      };
    }
  }, [project.task_result?.layer_id]);

  const onCancel = () => {
    navigate("/projects");
  };

  const toggleLayerVisibility = (
    e: React.MouseEvent<HTMLButtonElement, MouseEvent>,
    selectedGroup: DetectionResultGroup
  ) => {
    e.stopPropagation();

    selectedGroup.layer.set("visible", !selectedGroup.isVisible);
    setGroups(
      groups.map((group) => {
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
        <Box component="div" sx={{ py: 1, mb: 1 }}>
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
          sx={{ display: "flex", justifyContent: "space-between" }}
        >
          <Typography variant="subtitle1" sx={{ fontWeight: "bold" }}>
            {t("project.objectsResultTitle")}
          </Typography>
          <Chip
            label={isLoading ? <CircularProgress size="1rem" /> : totalObjects}
            variant="outlined"
            sx={{ ".MuiChip-label": { display: "flex" } }}
          />
        </Box>
        <Box component="div" sx={{ mt: 2, p: 0.5, overflowY: "auto" }}>
          {groups.map((group) => (
            <Accordion
              key={group.title}
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
                    onClick={(e) => toggleLayerVisibility(e, group)}
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
                <LayerObjectList layer={group.layer} search={debouncedSearch} />
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      </Box>
      <Box component="div" sx={{ px: 2, pb: 2 }}>
        <Button variant="outlined" fullWidth onClick={onCancel}>
          {t("general.cancel")}
        </Button>
      </Box>
    </>
  );
};
