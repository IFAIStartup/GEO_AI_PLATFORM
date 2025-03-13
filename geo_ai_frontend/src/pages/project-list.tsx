import React from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";
import { Box, Button, Container, Tab } from "@mui/material";

import { StyledTabs } from "@components/shared/tabs";
import { ProjectsTable } from "@components/project/projectsTable";
import { CreateProjectMenu } from "@components/project/createProjectMenu";
import { ComparisonsTable } from "@components/comparison/comparisonsTable";

enum TABS {
  Detection,
  Comparison,
}

export const ProjectListPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();

  const selectedTab = location.pathname.includes("/comparison")
    ? TABS.Comparison
    : TABS.Detection;

  const onNewComparison = () => {
    navigate(`/projects/comparison/0`);
  };

  const onTabSwitch = (newTab: TABS) => {
    if (newTab === selectedTab) {
      return;
    } else if (newTab === TABS.Detection) {
      navigate(`/projects`);
    } else if (newTab === TABS.Comparison) {
      navigate(`/projects/comparison`);
    }
  };

  return (
    <Container sx={{ pt: 4, pb: 2 }}>
      <Box
        component="div"
        sx={{ display: "flex", justifyContent: "space-between" }}
        dir="ltr"
      >
        <StyledTabs value={selectedTab} onChange={(_, tab) => onTabSwitch(tab)}>
          <Tab label={t("project.detectionTab")} id="detection-tab" />
          <Tab label={t("project.comparisonTab")} id="comparison-tab" />
        </StyledTabs>
        {selectedTab === TABS.Detection && <CreateProjectMenu />}
        {selectedTab === TABS.Comparison && (
          <Button
            variant="contained"
            id="start-comparison-button"
            onClick={onNewComparison}
          >
            {t("project.startComparison")}
          </Button>
        )}
      </Box>
      {selectedTab === TABS.Detection && <ProjectsTable />}
      {selectedTab === TABS.Comparison && <ComparisonsTable />}
    </Container>
  );
};
