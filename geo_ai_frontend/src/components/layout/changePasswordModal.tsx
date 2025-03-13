import React, { useState, ChangeEvent, Dispatch, SetStateAction } from "react";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Box,
  Button,
  IconButton,
  Modal,
  TextField,
  Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";

import { ModalContent } from "@components/shared/modalContent";
import { useUserStore } from "@store/user.store";
import { ApiError, ModalProps } from "@models/common";
import { ERRORS } from "@models/error";

export const ChangePasswordModal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
}) => {
  const { t } = useTranslation();
  const { user, changePassword } = useUserStore();

  const [oldPw, setOldPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [newPw2, setNewPw2] = useState("");
  const [oldPwError, setOldPwError] = useState("");
  const [newPwError, setNewPwError] = useState("");

  const onInput = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
    setter: Dispatch<SetStateAction<string>>
  ) => {
    setter(e.target.value);
    setOldPwError("");
    setNewPwError("");
  };

  const onSubmit = () => {
    if (newPw !== newPw2) {
      setNewPwError(t("home.passwordsDoNotMatch"));
      return;
    }

    if (user) {
      changePassword({
        id: user.id,
        old_password: oldPw,
        password: newPw,
        confirm_password: newPw2,
      })
        .then(() => {
          handleClose();
        })
        .catch((e: ApiError) => {
          const err = e.response?.data.detail;
          if (err?.code === "INVALID_CHANGE_PASSWORD") {
            setOldPwError(t(ERRORS[err.code]));
          } else if (
            err?.code === "INVALID_PASSWORD" ||
            err?.code === "PASSWORD_MATCH_OLD_PASSWORD"
          ) {
            setNewPwError(t(ERRORS[err.code]));
          } else {
            setNewPwError(t(ERRORS.OTHER));
          }
        });
    }
  };

  const handleClose = () => {
    setOldPw("");
    setNewPw("");
    setNewPw2("");
    setOldPwError("");
    setNewPwError("");
    onClose();
  };

  return (
    <Modal open={isOpen} onClose={handleClose}>
      <ModalContent>
        <IconButton sx={{ alignSelf: "end" }} onClick={handleClose}>
          <CloseIcon />
        </IconButton>
        <Typography variant="h5" sx={{ textTransform: "capitalize" }}>
          {t("home.changePassword")}
        </Typography>
        <Box
          component="div"
          sx={{
            display: "flex",
            flexDirection: "column",
            width: 400,
            gap: 2,
            mt: 3,
          }}
        >
          <TextField
            required
            fullWidth
            id="old-pw"
            label={t("home.oldPw")}
            value={oldPw}
            type="password"
            onChange={(e) => onInput(e, setOldPw)}
            error={!!oldPwError}
            helperText={oldPwError}
          />
          <TextField
            required
            fullWidth
            id="new-pw"
            label={t("home.newPw")}
            value={newPw}
            type="password"
            onChange={(e) => onInput(e, setNewPw)}
            error={!!newPwError}
          />
          <TextField
            required
            fullWidth
            id="new-pw-2"
            label={t("home.newPw2")}
            value={newPw2}
            type="password"
            onChange={(e) => onInput(e, setNewPw2)}
            error={!!newPwError}
            helperText={newPwError}
          />
          <Alert severity="info">{t("login.passwordHint")}</Alert>
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
            disabled={
              !oldPw || !newPw || !newPw2 || !!oldPwError || !!newPwError
            }
          >
            {t("home.changePassword")}
          </Button>
          <Button variant="text" onClick={handleClose} fullWidth>
            {t("general.cancel")}
          </Button>
        </Box>
      </ModalContent>
    </Modal>
  );
};
