import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Alert, Snackbar } from "@mui/material";

import { useAlertStore } from "@store/alert.store";

let timeout: NodeJS.Timeout;

export const AlertSnackbar: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [open, setOpen] = useState(false);

  const { alert, dropAlert } = useAlertStore();

  useEffect(() => {
    return () => {
      if (timeout) {
        clearTimeout(timeout);
      }
    };
  }, []);

  useEffect(() => {
    if (alert) {
      setOpen(true);
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        setOpen(false);
        dropAlert();
      }, 6000);
    }
  }, [alert]);

  const handleClose = (_: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === "clickaway") {
      return;
    }

    setOpen(false);
  };

  return (
    <Snackbar
      open={open}
      onClose={handleClose}
      anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
    >
      {alert && (
        <Alert onClose={handleClose} severity={alert.severity} dir="ltr">
          {typeof alert.key === "string"
            ? i18n.exists(alert.key)
              ? t(alert.key)
              : alert.key
            : t("general.error")}
        </Alert>
      )}
    </Snackbar>
  );
};
