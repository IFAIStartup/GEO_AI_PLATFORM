import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Box, Button, Tab } from "@mui/material";

import { UsersTable } from "@components/admin/usersTable";
import { UserModal } from "@components/admin/userModal";
import { StyledTabs } from "@components/shared/tabs";
import { CreateGroupModal } from "@components/admin/createGroupModal";
import { GroupsTable } from "@components/admin/groupsTable";

enum TABS {
  Users,
  Groups,
}

export const AdminPage: React.FC = () => {
  const { t } = useTranslation();

  const [selectedTab, setSelectedTab] = useState(TABS.Users);
  const [isUserModalOpen, setIsUserModalOpen] = useState(false);
  const [isGroupModalOpen, setIsGroupModalOpen] = useState(false);

  const onAddUser = () => {
    setIsUserModalOpen(true);
  };
  const onAddGroup = () => {
    setIsGroupModalOpen(true);
  };

  return (
    <>
      <Box
        component="div"
        sx={{ display: "flex", justifyContent: "space-between" }}
        dir="ltr"
      >
        <StyledTabs
          value={selectedTab}
          onChange={(_, tab) => setSelectedTab(tab)}
        >
          <Tab label={t("admin.userTab")} id="users-tab" />
          {/* <Tab label={t("admin.groupTab")} id="groups-tab" /> */}
        </StyledTabs>
        {selectedTab === TABS.Users && (
          <Button
            variant="contained"
            onClick={onAddUser}
            id="create-user-button"
          >
            {t("admin.createUser")}
          </Button>
        )}
        {selectedTab === TABS.Groups && (
          <Button
            variant="contained"
            onClick={onAddGroup}
            id="create-group-button"
          >
            {t("admin.createGroup")}
          </Button>
        )}
      </Box>
      {selectedTab === TABS.Users && <UsersTable />}
      {selectedTab === TABS.Groups && <GroupsTable />}
      <UserModal
        isOpen={isUserModalOpen}
        onClose={() => setIsUserModalOpen(false)}
      />
      <CreateGroupModal
        isOpen={isGroupModalOpen}
        onClose={() => setIsGroupModalOpen(false)}
      />
    </>
  );
};
