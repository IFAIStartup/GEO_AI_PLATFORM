import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Box, Button, IconButton, Modal, Typography } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import ShareIcon from "@mui/icons-material/Share";

import { ModalContent } from "@components/shared/modalContent";
import { useMLStore } from "@store/ml.store";

export const ShareMLModel: React.FC = () => {
  const { t } = useTranslation();
  const { model } = useMLStore();

  const [isModalOpen, setIsModalOpen] = useState(false);

  const onModalOpen = () => {
    setIsModalOpen(true);
  };

  const onModalClose = () => {
    setIsModalOpen(false);
  };

  const onSubmit = () => {
    setIsModalOpen(false);
  };

  if (!model) {
    return <></>;
  }

  return (
    <>
      <Button
        id="share-ml-model-button"
        variant="contained"
        startIcon={<ShareIcon />}
        onClick={onModalOpen}
      >
        {t("ml.share")}
      </Button>
      <Modal open={isModalOpen} onClose={onModalClose}>
        <ModalContent>
          <IconButton
            sx={{ alignSelf: "end" }}
            onClick={onModalClose}
            id="close-modal-button"
          >
            <CloseIcon />
          </IconButton>
          <Typography variant="h5">
            {t("ml.share")} {model.name}
          </Typography>
          <Typography variant="body1" sx={{ textAlign: "center", px: 10 }}>
            {t("ml.shareSub")}
          </Typography>
          <Box
            component="div"
            sx={{
              display: "flex",
              flexDirection: "column",
              width: 400,
              gap: 4,
              mt: 3,
            }}
          >
            {/* USER table */}
          </Box>
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
              onClick={onSubmit}
              fullWidth
              id="save-button"
            >
              {t("general.save")}
            </Button>
            <Button
              variant="text"
              onClick={onModalClose}
              fullWidth
              id="cancel-modal-button"
            >
              {t("general.cancel")}
            </Button>
          </Box>
        </ModalContent>
      </Modal>
    </>
  );
};
