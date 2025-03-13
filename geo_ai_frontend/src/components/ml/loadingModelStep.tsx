import React, { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Box, Button, CircularProgress, Typography } from "@mui/material";
import { clearIntervalAsync, setIntervalAsync } from "set-interval-async";
import { MLStatus } from "@models/ml";
import { useMLStore } from "@store/ml.store";

export const LoadingModelStep: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const model = useMLStore((state) => state.model);
  const getModel = useMLStore((state) => state.getModel);

  useEffect(() => {
    const interval = setIntervalAsync(async () => {
      if (model?.id) {
        await getModel(model.id);
      }
    }, 10000);

    return () => {
      clearIntervalAsync(interval);
    };
  }, []);

  const onCancel = () => {
    navigate("/ml");
  };

  return (
    <Box
      component="div"
      sx={{
        minWidth: 400,
        display: "flex",
        flexDirection: "column",
        flexGrow: 1,
        alignItems: "center",
        justifyContent: "center",
        gap: 4,
      }}
    >
      <CircularProgress size={80} />
      <Box component="div" sx={{ textAlign: "center" }}>
        <Typography variant="h6" sx={{ fontWeight: "bold" }}>
          {model?.status === MLStatus.InTraining
            ? t("ml.training")
            : t("ml.loading")}
        </Typography>
        <Typography variant="h6" sx={{ fontWeight: "bold" }}>
          {t("general.pleaseWait")}
        </Typography>
      </Box>
      <Button
        variant="outlined"
        disabled={!model?.mlflow_url}
        onClick={() => window.open(model?.mlflow_url)}
        sx={{ px: 4 }}
      >
        {t("ml.openMlFlow")}
      </Button>
      <Button variant="outlined" onClick={onCancel} sx={{ px: 4 }}>
        {t("general.cancel")}
      </Button>
    </Box>
  );
};
