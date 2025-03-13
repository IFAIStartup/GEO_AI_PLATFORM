import React, { MouseEvent } from "react";
import { ToggleButton, ToggleButtonGroup } from "@mui/material";
import { useTranslation } from "react-i18next";

import { useUserStore } from "@store/user.store";
import { MapFilesTogglePosition } from "@models/project";

export const MapFilesToggle: React.FC = () => {
  const { t } = useTranslation();

  const position = useUserStore((state) => state.preferences.mapFilesToggle);
  const setPosition = useUserStore((state) => state.setMapFilesTogglePosition);

  const handlePositionChange = (
    _: MouseEvent<HTMLElement>,
    newPos: MapFilesTogglePosition
  ) => {
    if (newPos) {
      setPosition(newPos);
    }
  };

  return (
    <ToggleButtonGroup
      value={position}
      exclusive
      size="small"
      onChange={handlePositionChange}
    >
      <ToggleButton value={MapFilesTogglePosition.IMAGES}>
        {t("project.images")}
      </ToggleButton>
      <ToggleButton value={MapFilesTogglePosition.BOTH}>
        {t("project.imagesAndMap")}
      </ToggleButton>
      <ToggleButton value={MapFilesTogglePosition.MAP}>
        {t("project.map")}
      </ToggleButton>
    </ToggleButtonGroup>
  );
};
