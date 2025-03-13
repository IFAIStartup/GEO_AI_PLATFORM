import React, {
  ChangeEvent,
  Dispatch,
  SetStateAction,
  useEffect,
  useState,
} from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { Alert, Box, Button, Typography } from "@mui/material";
import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";

import { LoginTextField } from "@components/login/loginTextField";
import { useUserStore } from "@store/user.store";

export const ResetPasswordPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { resetKey } = useParams();
  const [searchParams] = useSearchParams();
  const { checkRestoreKey, resetPassword } = useUserStore();

  const [newPw, setNewPw] = useState("");
  const [newPw2, setNewPw2] = useState("");
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    if (resetKey) {
      checkRestoreKey(resetKey).then((isValid) => {
        if (!isValid) {
          navigate("/login");
        }
      });
    }
  }, [resetKey]);

  const onInput = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
    setter: Dispatch<SetStateAction<string>>
  ) => {
    setHasError(false);
    setter(e.target.value);
  };

  const onSave = () => {
    if (!resetKey) {
      return;
    }

    resetPassword({
      key: resetKey,
      password: newPw,
      confirm_password: newPw2,
    })
      .then(() => {
        navigate("/login");
      })
      .catch(() => {
        setHasError(true);
      });
  };

  const onBack = () => {
    navigate("/login");
  };

  return (
    <>
      <Button
        sx={{
          position: "absolute",
          left: -30,
          width: 60,
          height: 60,
          minWidth: 0,
          padding: 0,
          borderRadius: "50%",
        }}
        variant="contained"
        onClick={onBack}
      >
        <ArrowBackRoundedIcon />
      </Button>
      <Typography variant="h3" sx={{ textAlign: "center", pb: 2 }}>
        {searchParams.get("isNew") === "true"
          ? t("restore.title2")
          : t("restore.title")}
      </Typography>
      <LoginTextField
        required
        fullWidth
        id="new-pw"
        placeholder={t("home.newPw")}
        value={newPw}
        type="password"
        onChange={(e) => onInput(e, setNewPw)}
        error={hasError}
        autoFocus
      />
      <LoginTextField
        required
        fullWidth
        id="new-pw-2"
        placeholder={t("home.newPw2")}
        value={newPw2}
        type="password"
        onChange={(e) => onInput(e, setNewPw2)}
        error={hasError}
      />
      <Alert severity="info" variant="filled" sx={{ fontWeight: 400 }}>
        {t("login.passwordHint")}
      </Alert>
      <Box component="div">
        {hasError && (
          <Typography variant="body2" sx={{ mt: -3, mb: 1 }} color="#FFD4D4">
            {t("home.newPasswordError")}
          </Typography>
        )}
        <Button
          fullWidth
          variant="contained"
          size="large"
          disabled={!newPw || !newPw2 || hasError}
          onClick={onSave}
        >
          {t("restore.saveBtn")}
        </Button>
      </Box>
    </>
  );
};
