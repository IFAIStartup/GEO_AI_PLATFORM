import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Box, Button, IconButton, Menu, MenuItem } from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import VisibilityIcon from "@mui/icons-material/Visibility";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import HourglassTopIcon from "@mui/icons-material/HourglassTop";
import DeleteIcon from "@mui/icons-material/Delete";

import { ProjectStatus } from "@models/project";
import { Comparison } from "@models/comparison";
import { ConfirmComparisonDeleteModal } from "@components/comparison/confirmDeleteModal";

export const ComparisonActionButtons: React.FC<{ comparison: Comparison }> = ({
  comparison,
}) => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [isConfirmDeleteModalOpen, setIsConfirmDeleteModalOpen] =
    useState(false);
  const [additionalActionsMenuEl, setAdditionalActionsMenuEl] =
    useState<null | HTMLElement>(null);

  const openAdditionalActionsMenu = (
    event: React.MouseEvent<HTMLButtonElement>
  ) => {
    setAdditionalActionsMenuEl(event.currentTarget);
  };

  const handleAdditionalActionsMenuClose = () => {
    setAdditionalActionsMenuEl(null);
  };

  const onMainActionClick = () => {
    navigate(`/projects/comparison/${comparison.id}`);
  };

  const handleDeleteActionClick = () => {
    setIsConfirmDeleteModalOpen(true);
    handleAdditionalActionsMenuClose();
  };

  return (
    <Box
      component="div"
      sx={{ display: "flex", justifyContent: "space-between" }}
    >
      <Box component="div">
        {comparison.status === ProjectStatus.Initial && (
          <Button
            startIcon={<PlayArrowIcon />}
            sx={{ textTransform: "none" }}
            onClick={onMainActionClick}
            id={`comparison-${comparison.id}-start-detection-button`}
          >
            {t("comparison.startComparisonButton")}
          </Button>
        )}
        {comparison.status === ProjectStatus.InProgress && (
          <Button
            startIcon={<HourglassTopIcon />}
            sx={{ textTransform: "none" }}
            onClick={onMainActionClick}
            id={`comparison-${comparison.id}-view-progress-button`}
          >
            {t("general.viewProgress")}
          </Button>
        )}
        {comparison.status === ProjectStatus.Finished && (
          <Button
            startIcon={<VisibilityIcon />}
            sx={{ textTransform: "none" }}
            onClick={onMainActionClick}
            id={`comparison-${comparison.id}-view-results-button`}
          >
            {t("project.viewResult")}
          </Button>
        )}
        {comparison.status === ProjectStatus.Error && (
          <Button
            startIcon={<DeleteIcon />}
            sx={{ textTransform: "none", color: "error.primary" }}
            onClick={handleDeleteActionClick}
            id={`comparison-${comparison.id}-delete-button`}
          >
            {t("comparison.deleteComparison")}
          </Button>
        )}
      </Box>
      {comparison.status !== ProjectStatus.Error && (
        <IconButton
          id={`comparison-${comparison.id}-more-actions-button`}
          onClick={openAdditionalActionsMenu}
        >
          <MoreVertIcon />
        </IconButton>
      )}
      <Menu
        anchorEl={additionalActionsMenuEl}
        open={!!additionalActionsMenuEl}
        onClose={handleAdditionalActionsMenuClose}
      >
        <MenuItem
          id={`comparison-${comparison.id}-delete-button`}
          onClick={handleDeleteActionClick}
        >
          {t("comparison.deleteComparison")}
        </MenuItem>
      </Menu>
      <ConfirmComparisonDeleteModal
        isOpen={isConfirmDeleteModalOpen}
        onClose={() => setIsConfirmDeleteModalOpen(false)}
        comparison={comparison}
      />
    </Box>
  );
};
