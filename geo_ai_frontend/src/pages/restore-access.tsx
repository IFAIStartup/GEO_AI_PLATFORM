import React, { useState, ChangeEvent } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Box, Button, Typography } from "@mui/material";
import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";

import { LoginTextField } from "@components/login/loginTextField";
import { useUserStore } from "@store/user.store";
import { ApiError } from "@models/common";
import { ERRORS } from "@models/error";

export const RestoreAccessPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const restoreAccess = useUserStore((state) => state.restoreAccess);

  const [email, setEmail] = useState("");
  const [emailSent, setEmailSent] = useState(false);
  const [error, setError] = useState<string>();

  const onInput = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setEmail(e.target.value);
    setError(undefined);
  };

  const onRestore = () => {
    restoreAccess({
      email,
    })
      .then(() => {
        setEmailSent(true);
      })
      .catch((e: ApiError) => {
        const err = e.response?.data.detail;
        if (err?.code === "INVALID_EMAIL" || err?.code === "USER_NOT_FOUND") {
          setError(t(ERRORS[err.code]));
        } else {
          setError(t(ERRORS.OTHER));
        }
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
        id="back-button"
      >
        <ArrowBackRoundedIcon />
      </Button>
      <Typography variant="h3" sx={{ textAlign: "center" }}>
        {t("restore.title")}
      </Typography>
      {emailSent ? (
        <>
          <Typography variant="subtitle1" sx={{ textAlign: "center" }}>
            {t("restore.description3")}
          </Typography>
          <Typography
            variant="subtitle1"
            sx={{ textAlign: "center", color: "success.main" }}
          >
            {t("restore.description4")}
          </Typography>
          <Button
            fullWidth
            href="mailto:gis.tps@aam.gov.ae"
            variant="contained"
            size="large"
            color="success"
            sx={{ color: "#fff" }}
            id="contact-support-button"
          >
            {t("restore.contactBtn")}
          </Button>
        </>
      ) : (
        <>
          <Box component="div">
            <Typography variant="subtitle1" sx={{ textAlign: "center" }}>
              {t("restore.description1")}
            </Typography>
            <Typography variant="subtitle1" sx={{ textAlign: "center" }}>
              {t("restore.description2")}
            </Typography>
          </Box>
          <LoginTextField
            required
            fullWidth
            id="email"
            placeholder={t("restore.emailPlaceholder")}
            type="email"
            autoComplete="email"
            value={email}
            onChange={onInput}
            error={!!error}
            helperText={error}
            autoFocus
          />
          <Button
            fullWidth
            variant="contained"
            size="large"
            disabled={!email || !!error}
            onClick={onRestore}
            id="restore-button"
          >
            {t("restore.restoreBtn")}
          </Button>
        </>
      )}
    </>
  );
};
