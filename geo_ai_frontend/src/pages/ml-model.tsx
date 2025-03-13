import React, { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Box, CircularProgress } from "@mui/material";

import { useMLStore } from "@store/ml.store";
import { MLStatus } from "@models/ml";
import { LoadingModelStep } from "@components/ml/loadingModelStep";
import { TrainModelStep } from "@components/ml/trainModelStep";

export const MLModelPage: React.FC = () => {
  const { modelId } = useParams();
  const navigate = useNavigate();

  const model = useMLStore((state) => state.model);
  const getModel = useMLStore((state) => state.getModel);
  const getModelTypes = useMLStore((state) => state.getModelTypes);

  useEffect(() => {
    getModelTypes();
  }, []);

  useEffect(() => {
    const id = +(modelId || NaN);
    if (!isNaN(id)) {
      getModel(id);
    } else {
      navigate("/ml");
    }
  }, [modelId]);

  const getStep = () => {
    switch (model?.status) {
      case MLStatus.Loading:
      case MLStatus.InTraining:
        return <LoadingModelStep />;
      case MLStatus.NotTrained:
        return <TrainModelStep model={model} />;
      default:
        navigate("/ml");
        return <></>;
    }
  };

  if (!model) {
    return (
      <Box
        component="div"
        sx={{ display: "flex", justifyContent: "center", pt: 12 }}
      >
        <CircularProgress size="60px" />
      </Box>
    );
  }

  return (
    <Box
      component="div"
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "calc(100vh - 112px)",
        alignItems: "center",
      }}
    >
      {getStep()}
    </Box>
  );
};
