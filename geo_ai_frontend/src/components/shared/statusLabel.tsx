import React from "react";
import { useTranslation } from "react-i18next";
import { Box, Tooltip } from "@mui/material";
import CircleIcon from "@mui/icons-material/Circle";
import AccessTimeIcon from "@mui/icons-material/AccessTime";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";

import { ProjectStatus } from "@models/project";

interface Props {
  status: ProjectStatus;
  translatedInfo?: string;
}

export const StatusLabel: React.FC<Props> = ({ status, translatedInfo }) => {
  const { t } = useTranslation();

  const getLabel = (): React.ReactNode => {
    switch (status) {
      case ProjectStatus.Initial:
        return (
          <>
            <CircleIcon color="primary" sx={{ fontSize: 12, mr: 1 }} />
            {t("project.ready")}
          </>
        );
      case ProjectStatus.InProgress:
        return (
          <Box component="div" sx={{ display: "flex", alignItems: "center" }}>
            <CircleIcon color="warning" sx={{ fontSize: 12, mr: 1 }} />
            {t("project.inProgress")}
            <AccessTimeIcon sx={{ fontSize: 18, ml: 1 }} />
          </Box>
        );
      case ProjectStatus.Finished:
        return (
          <>
            <CircleIcon color="success" sx={{ fontSize: 12, mr: 1 }} />
            {t("project.completed")}
          </>
        );
      case ProjectStatus.Error:
        return (
          <Box component="div" sx={{ display: "flex", alignItems: "center" }}>
            <CircleIcon color="error" sx={{ fontSize: 12, mr: 1 }} />
            {t("project.error")}
            {translatedInfo && (
              <Tooltip title={translatedInfo}>
                <InfoOutlinedIcon sx={{ fontSize: 18, ml: 1 }} />
              </Tooltip>
            )}
          </Box>
        );
      default:
        return <>{status}</>;
    }
  };

  return <>{getLabel()}</>;
};
