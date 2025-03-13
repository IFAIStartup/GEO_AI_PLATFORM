import React from "react";
import { useTranslation } from "react-i18next";
import { Box, Button, IconButton, Modal, Typography } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";

import { ModalContent } from "@components/shared/modalContent";
import { ApiError, ModalProps } from "@models/common";
import { Comparison } from "@models/comparison";
import { useComparisonStore } from "@store/comparison.store";

interface DeleteModalProps extends ModalProps {
  comparison: Comparison;
}

export const ConfirmComparisonDeleteModal: React.FC<DeleteModalProps> = ({
  comparison,
  isOpen,
  onClose,
}) => {
  const { t } = useTranslation();
  const deleteComparison = useComparisonStore(
    (state) => state.deleteComparison
  );

  const onDelete = () => {
    deleteComparison(comparison.id)
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
          {t("comparison.confirmDelete", {
            project1: comparison.project_1.name,
            project2: comparison.project_2.name,
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
            id="delete-comparison-button"
            color="error"
          >
            {t("comparison.deleteComparison")}
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
