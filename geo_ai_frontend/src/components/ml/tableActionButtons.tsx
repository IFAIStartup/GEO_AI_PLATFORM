import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Box, Button, IconButton, Menu, MenuItem } from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import HourglassTopIcon from "@mui/icons-material/HourglassTop";
import DoneIcon from "@mui/icons-material/Done";

import { MLModel, MLStatus } from "@models/ml";
import { ConfirmMLModelDeleteModal } from "./confirmDeleteModal";
import { useMLStore } from "@store/ml.store";

export const CreatedMLModelActionButtons: React.FC<{ model: MLModel }> = ({
  model,
}) => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const setModel = useMLStore((state) => state.setModel);
  const finishModelTraining = useMLStore((state) => state.finishTraining);

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

  const openModel = (model: MLModel) => {
    setModel(model);
    navigate(`/ml/${model.id}`);
  };

  const finishTraining = (model: MLModel) => {
    finishModelTraining(model.id);
  };

  const onOpenMLFlow = (model: MLModel) => {
    setModel(model);
    window.open(model.mlflow_url);
  };

  const handleDeleteActionClick = () => {
    setIsConfirmDeleteModalOpen(true);
    handleAdditionalActionsMenuClose();
  };

  const getActionButton = (model: MLModel) => {
    switch (model.status) {
      case MLStatus.Loading:
      case MLStatus.InTraining:
        return (
          <Button
            startIcon={<HourglassTopIcon />}
            sx={{ textTransform: "none" }}
            onClick={() => openModel(model)}
            id={`ml-${model.id}-view-progress-button`}
          >
            {t("general.viewProgress")}
          </Button>
        );
      case MLStatus.NotTrained:
        return (
          <Button
            startIcon={<PlayArrowIcon />}
            sx={{ textTransform: "none" }}
            onClick={() => openModel(model)}
            id={`ml-${model.id}-start-training-button`}
          >
            {t("ml.startTraining")}
          </Button>
        );
      case MLStatus.Trained:
        return (
          <Button
            startIcon={<DoneIcon />}
            sx={{ textTransform: "none" }}
            onClick={() => finishTraining(model)}
            id={`ml-${model.id}-finish-training-button`}
          >
            {t("ml.finishTraining")}
          </Button>
        );
      case MLStatus.Ready:
      case MLStatus.Error:
      default:
        return <></>;
    }
  };

  return (
    <Box
      component="div"
      sx={{ display: "flex", justifyContent: "space-between" }}
    >
      <Box component="div">{getActionButton(model)}</Box>
      <IconButton
        id={`ml-model-${model.id}-more-actions-button`}
        onClick={openAdditionalActionsMenu}
      >
        <MoreVertIcon />
      </IconButton>
      <Menu
        anchorEl={additionalActionsMenuEl}
        open={!!additionalActionsMenuEl}
        onClose={handleAdditionalActionsMenuClose}
      >
        {(model.status === MLStatus.InTraining ||
          model.status === MLStatus.Trained ||
          model.status === MLStatus.Ready) && (
          <MenuItem
            id={`ml-model-${model.id}-open-ml-flow-button`}
            onClick={() => onOpenMLFlow(model)}
            disabled={!model.mlflow_url}
          >
            {t("ml.openMlFlow")}
          </MenuItem>
        )}
        <MenuItem
          id={`ml-model-${model.id}-delete-button`}
          onClick={handleDeleteActionClick}
        >
          {t("ml.delete")}
        </MenuItem>
      </Menu>
      <ConfirmMLModelDeleteModal
        isOpen={isConfirmDeleteModalOpen}
        onClose={() => setIsConfirmDeleteModalOpen(false)}
        model={model}
      />
    </Box>
  );
};
