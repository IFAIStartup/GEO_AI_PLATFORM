import React, { useEffect, useState } from "react";
import FeatureLayer from "@arcgis/core/layers/FeatureLayer";
import { useTranslation } from "react-i18next";
import {
  Box,
  CircularProgress,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
} from "@mui/material";
import { useMapStore } from "@store/map.store";

interface Props {
  layer: FeatureLayer;
  search: string;
  isComparison?: boolean;
}

interface LayerObject {
  graphic: __esri.Graphic;
  name: string;
  oldName?: string;
  newName?: string;
  text?: string;
}

export const LayerObjectList: React.FC<Props> = ({
  layer,
  search,
  isComparison,
}) => {
  const { t } = useTranslation();
  const [objects, setObjects] = useState<LayerObject[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const mapView = useMapStore((state) => state.mapView);
  const setHighlightHandle = useMapStore((state) => state.setHighlightHandle);

  useEffect(() => {
    const queryObjects = async () => {
      setIsLoading(true);
      const where = search
        ? isComparison
          ? `name_old LIKE '%${search}%' OR name_new LIKE '%${search}%'`
          : `name LIKE '%${search}%'`
        : "";
      const firstFeatureSet = await layer.queryFeatures({
        where,
        outFields: ["*"],
        returnGeometry: true,
      });
      const features = firstFeatureSet.features;
      let exceededTransferLimit = firstFeatureSet.exceededTransferLimit;

      while (exceededTransferLimit) {
        const {
          features: additionalFeatures,
          exceededTransferLimit: stillExceeded,
        } = await layer.queryFeatures({
          start: features.length,
          num: 1000,
          where,
          outFields: ["*"],
          returnGeometry: true,
        });
        features.push(...additionalFeatures);
        exceededTransferLimit = stillExceeded;
      }

      setObjects(
        features.map((f) => {
          const name = f.getAttribute("name")?.trim() || "No name";
          let oldName = f.getAttribute("name_old")?.trim();
          let newName = f.getAttribute("name_new")?.trim();
          const text = f.getAttribute("text")?.trim();

          if (!oldName && !newName) {
            oldName = name;
            newName = "";
          } else {
            oldName = oldName || "No object";
            newName = newName || "No object";
          }
          return {
            graphic: f,
            name,
            oldName,
            newName,
            text,
          };
        })
      );
      setIsLoading(false);
    };

    queryObjects();
  }, [search]);

  const onLayerObjectClick = async (graphic: __esri.Graphic) => {
    if (!mapView) {
      return;
    }
    setHighlightHandle();
    mapView.openPopup({ features: [graphic] });
  };

  return (
    <List dense={true}>
      {isLoading && (
        <Box component="div" sx={{ display: "flex", justifyContent: "center" }}>
          <CircularProgress />
        </Box>
      )}
      {objects.map((obj, index) => (
        <ListItem disablePadding key={index}>
          <ListItemButton onClick={() => onLayerObjectClick(obj.graphic)}>
            <ListItemText
              primary={
                isComparison ? (
                  <Box
                    component="div"
                    sx={{ display: "flex", justifyContent: "space-between" }}
                  >
                    <Box component="div">{obj.oldName}</Box>
                    <Box component="div" sx={{ textAlign: "right" }}>
                      {obj.newName}
                    </Box>
                  </Box>
                ) : (
                  obj.name
                )
              }
              secondary={
                obj.text && !isComparison
                  ? `${t("map.text")}: ${obj.text}`
                  : undefined
              }
              primaryTypographyProps={{ fontWeight: "bold" }}
            />
          </ListItemButton>
        </ListItem>
      ))}
    </List>
  );
};
