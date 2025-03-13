import React from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Box, Button, Tab } from "@mui/material";

import { MLModelTypes } from "@models/ml";
import { useMLStore } from "@store/ml.store";
import { useUserStore } from "@store/user.store";
import { StyledTabs } from "@components/shared/tabs";
import { DefaultMLModels } from "@components/ml/defaultMLModelsTable";
import { CreatedMLModels } from "@components/ml/createdMLModelsTable";

export const MLModelListPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const resetModel = useMLStore((state) => state.resetModel);

  const mlTab = useUserStore((state) => state.preferences.mlTab);
  const setMLTab = useUserStore((state) => state.setMLTab);

  const onCreateNewMLModel = () => {
    resetModel();
    navigate(`/ml/create`);
  };

  return (
    <>
      <Box
        component="div"
        sx={{ display: "flex", justifyContent: "space-between" }}
        dir="ltr"
      >
        <StyledTabs value={mlTab} onChange={(_, tab) => setMLTab(tab)}>
          <Tab
            label={t("ml.defaultTab")}
            id="ml-default-tab"
            value={MLModelTypes.Default}
          />
          <Tab
            label={t("ml.createdTab")}
            id="ml-created-tab"
            value={MLModelTypes.Created}
          />
        </StyledTabs>
        <Box component="div" sx={{ display: "flex", gap: 2 }}>
          <Button
            variant="contained"
            id="create-model-button"
            onClick={onCreateNewMLModel}
          >
            {t("ml.createModelButton")}
          </Button>
        </Box>
      </Box>
      {mlTab === MLModelTypes.Default && <DefaultMLModels />}
      {mlTab === MLModelTypes.Created && <CreatedMLModels />}
    </>
  );
};
