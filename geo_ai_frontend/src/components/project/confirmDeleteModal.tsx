import React from "react";
import { useTranslation } from "react-i18next";
import { Box, Button, IconButton, Modal, Typography } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";

import { ModalContent } from "@components/shared/modalContent";
import { ApiError, ModalProps } from "@models/common";
import { Project } from "@models/project";
import { useProjectListStore } from "@store/projectList.store";

interface DeleteModalProps extends ModalProps {
  project: Project;
}

export const ConfirmProjectDeleteModal: React.FC<DeleteModalProps> = ({
  project,
  isOpen,
  onClose,
}) => {
  const { t } = useTranslation();
  const deleteProject = useProjectListStore((state) => state.deleteProject);

  const onDelete = () => {
    deleteProject(project.id)
      .then(() => {
        handleClose();
      })
      .catch((e: ApiError) => {
        const err = e.response?.data.detail;
        console.log(err?.message);
      });
  };

  const handleClose = () => {
    onClose();
  };

  return (
    <Modal open={isOpen} onClose={handleClose}>
      <ModalContent>
        <IconButton
          sx={{ alignSelf: "end" }}
          onClick={handleClose}
          id="close-modal-button"
        >
          <CloseIcon />
        </IconButton>
        <Typography
          variant="h5"
          textAlign="center"
          sx={{ overflowWrap: "anywhere" }}
        >
          {t("project.confirmDelete", {
            project: project.name,
          })}
        </Typography>
        <Box
          component="div"
          sx={{
            display: "flex",
            flexDirection: "column",
            width: 400,
            gap: 2,
            mt: 4,
          }}
        >
          <Button
            variant="contained"
            onClick={onDelete}
            fullWidth
            id="delete-project-button"
            color="error"
          >
            {t("project.deleteProject")}
          </Button>
          <Button
            variant="text"
            onClick={handleClose}
            fullWidth
            id="cancel-modal-button"
          >
            {t("general.cancel")}
          </Button>
        </Box>
      </ModalContent>
    </Modal>
  );
};
