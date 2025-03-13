import React from "react";
import { useTranslation } from "react-i18next";
import { Box, Tab } from "@mui/material";

import { StyledTabs } from "@components/shared/tabs";
import { HistoryTable } from "@components/history/historyTable";
import { useHistoryStore } from "@store/history.store";
import { HistoryType } from "@models/history";

export const HistoryPage: React.FC = () => {
  const { t } = useTranslation();
  const type = useHistoryStore((state) => state.historyType);
  const setHistoryType = useHistoryStore((state) => state.setHistoryType);

  return (
    <>
      <Box
        component="div"
        sx={{ display: "flex", justifyContent: "space-between" }}
        dir="ltr"
      >
        <StyledTabs value={type} onChange={(_, tab) => setHistoryType(tab)}>
          <Tab
            label={t("history.actionsTab")}
            id="action-tab"
            value={HistoryType.Action}
          />
          {/* <Tab
            label={t("history.objectsTab")}
            id="object-tab"
            value={HistoryType.Object}
          /> */}
          <Tab
            label={t("history.errorsTab")}
            id="error-tab"
            value={HistoryType.Error}
          />
          {/* <Tab label={t("history.notificationsTab")} id="notifications-tab" /> */}
        </StyledTabs>
      </Box>
      <HistoryTable />
      {/* {selectedTab === TABS.Notifications && <>Notifications</>} */}
    </>
  );
};
