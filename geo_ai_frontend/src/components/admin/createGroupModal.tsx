import React, { useState, ChangeEvent } from "react";
import { useTranslation } from "react-i18next";
import {
  Box,
  Button,
  IconButton,
  Modal,
  TextField,
  Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";

import { useAdminStore } from "@store/admin.store";
import { ModalContent } from "@components/shared/modalContent";
import { ApiError, ModalProps } from "@models/common";

export const CreateGroupModal: React.FC<ModalProps> = ({ isOpen, onClose }) => {
  const { t } = useTranslation();
  const createGroup = useAdminStore((state) => state.createGroup);

  const [name, setName] = useState("");
  const [nameError, setNameError] = useState("");

  const onNameChange = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setName(e.target.value);
    setNameError("");
  };

  const onSubmit = () => {
    createGroup({
      name,
    })
      .then(() => {
        handleClose();
      })
      .catch((e: ApiError) => {
        const err = e.response?.data.detail;
        console.log(err?.message);
      });
  };

  const handleClose = () => {
    setName("");
    setNameError("");
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
        <Typography variant="h5">{t("admin.createGroup")}</Typography>
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
          <TextField
            required
            fullWidth
            id="group-name"
            label={t("admin.groupName")}
            value={name}
            onChange={onNameChange}
            error={!!nameError}
            helperText={nameError}
          />
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
            disabled={!name || !!nameError}
            fullWidth
            id="create-group-button"
          >
            {t("general.save")}
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
