import React, { useEffect, useState, ChangeEvent } from "react";
import { useTranslation } from "react-i18next";
import {
  Box,
  Button,
  IconButton,
  MenuItem,
  Modal,
  TextField,
  Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";

import { Role, User } from "@models/user";
import { useAdminStore } from "@store/admin.store";
import { ModalContent } from "@components/shared/modalContent";
import { ApiError, ModalProps } from "@models/common";
import { ERRORS } from "@models/error";

interface UserModalProps extends ModalProps {
  user?: User;
}

export const UserModal: React.FC<UserModalProps> = ({
  isOpen,
  onClose,
  user,
}) => {
  const { t } = useTranslation();
  const { createUser, updateUser } = useAdminStore();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState(Role.User);
  const [emailError, setEmailError] = useState("");

  useEffect(() => {
    if (isOpen && user) {
      setUsername(user.username);
      setEmail(user.email);
      setRole(user.role);
    }
  }, [isOpen, user]);

  const onEmailChange = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setEmail(e.target.value);
    setEmailError("");
  };

  const onSubmit = () => {
    if (user) {
      updateUser({
        id: user.id,
        username,
        role,
      }).then(() => {
        handleClose();
      });
    } else {
      createUser({
        username,
        email,
        role,
      })
        .then(() => {
          handleClose();
        })
        .catch((e: ApiError) => {
          const err = e.response?.data.detail;
          if (
            err?.code === "INVALID_EMAIL" ||
            err?.code === "EMAIL_ALREADY_REGISTERED"
          ) {
            setEmailError(t(ERRORS[err.code]));
          } else {
            setEmailError(t(ERRORS.OTHER));
          }
        });
    }
  };

  const handleClose = () => {
    setUsername("");
    setEmail("");
    setEmailError("");
    setRole(Role.User);
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
        <Typography variant="h5">
          {user ? t("admin.editUser") : t("admin.createUser")}
        </Typography>
        {user && (
          <Typography variant="body1" sx={{ textAlign: "center", px: 10 }}>
            {t("admin.editUserSub")}
          </Typography>
        )}
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
            id="name"
            label={t("admin.username")}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <TextField
            required
            fullWidth
            id="email"
            label={t("admin.email")}
            value={email}
            disabled={!!user}
            type="email"
            onChange={onEmailChange}
            error={!!emailError}
            helperText={emailError}
          />
          <TextField
            select
            required
            fullWidth
            id="role"
            label={t("general.role")}
            value={role}
            onChange={(e) => setRole(e.target.value as Role)}
          >
            {Object.values(Role).map((r) => (
              <MenuItem key={r} value={r}>
                {t(`roles.${r}`)}
              </MenuItem>
            ))}
          </TextField>
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
            disabled={!username || !email || !role || !!emailError}
            fullWidth
            id="create-user-button"
          >
            {user ? t("general.save") : t("admin.createUserButton")}
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
