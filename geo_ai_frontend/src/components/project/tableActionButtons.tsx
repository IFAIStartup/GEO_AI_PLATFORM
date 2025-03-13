import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Tooltip,
} from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import VisibilityIcon from "@mui/icons-material/Visibility";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import HourglassTopIcon from "@mui/icons-material/HourglassTop";
import DeleteIcon from "@mui/icons-material/Delete";

import { Project, ProjectStatus } from "@models/project";
import { ConfirmProjectDeleteModal } from "./confirmDeleteModal";
import { ProjectDetailsModal } from "./detailsModal";

export const ProjectActionButtons: React.FC<{ project: Project }> = ({
  project,
}) => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const [isConfirmDeleteModalOpen, setIsConfirmDeleteModalOpen] =
    useState(false);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
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
    navigate(`/projects/${project.id}`);
  };

  const handleDeleteActionClick = () => {
    setIsConfirmDeleteModalOpen(true);
    handleAdditionalActionsMenuClose();
  };

  const handleDetailsActionClick = () => {
    setIsDetailsModalOpen(true);
    handleAdditionalActionsMenuClose();
  };

  return (
    <Box
      component="div"
      sx={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}
    >
      {project.status === ProjectStatus.Initial && (
        <Button
          startIcon={<PlayArrowIcon />}
          sx={{ textTransform: "none" }}
          onClick={onMainActionClick}
          id={`project-${project.id}-start-detection-button`}
        >
          {t("project.startDetection")}
        </Button>
      )}
      {project.status === ProjectStatus.InProgress && (
        <Button
          startIcon={<HourglassTopIcon />}
          sx={{ textTransform: "none" }}
          onClick={onMainActionClick}
          id={`project-${project.id}-view-progress-button`}
        >
          {t("general.viewProgress")}
        </Button>
      )}
      {project.status === ProjectStatus.Finished &&
        (!project.ml_model?.length && !project.ml_model_deeplab?.length ? (
          <Tooltip title={t("project.viewResultDisabledTooltip")}>
            <span>
              <Button
                startIcon={<VisibilityIcon />}
                sx={{ textTransform: "none" }}
                onClick={onMainActionClick}
                id={`project-${project.id}-view-results-button`}
                disabled
              >
                {t("project.viewResult")}
              </Button>
            </span>
          </Tooltip>
        ) : (
          <Button
            startIcon={<VisibilityIcon />}
            sx={{ textTransform: "none" }}
            onClick={onMainActionClick}
            id={`project-${project.id}-view-results-button`}
          >
            {t("project.viewResult")}
          </Button>
        ))}
      {project.status === ProjectStatus.Error && (
        <Button
          startIcon={<DeleteIcon />}
          sx={{ textTransform: "none", color: "error.primary" }}
          onClick={handleDeleteActionClick}
          id={`project-${project.id}-delete-button`}
        >
          {t("project.deleteProject")}
        </Button>
      )}

      <IconButton
        id={`project-${project.id}-more-actions-button`}
        onClick={openAdditionalActionsMenu}
      >
        <MoreVertIcon />
      </IconButton>
      <Menu
        anchorEl={additionalActionsMenuEl}
        open={!!additionalActionsMenuEl}
        onClose={handleAdditionalActionsMenuClose}
      >
        <MenuItem
          id={`project-${project.id}-details-button`}
          onClick={handleDetailsActionClick}
        >
          {t("project.details")}
        </MenuItem>
        {project.status !== ProjectStatus.Error && (
          <MenuItem
            id={`project-${project.id}-delete-button`}
            onClick={handleDeleteActionClick}
          >
            {t("project.deleteProject")}
          </MenuItem>
        )}
      </Menu>
      <ConfirmProjectDeleteModal
        isOpen={isConfirmDeleteModalOpen}
        onClose={() => setIsConfirmDeleteModalOpen(false)}
        project={project}
      />
      <ProjectDetailsModal
        isOpen={isDetailsModalOpen}
        onClose={() => setIsDetailsModalOpen(false)}
        project={project}
      />
    </Box>
  );
};
