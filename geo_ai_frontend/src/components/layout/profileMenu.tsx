import React, { MouseEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Box, Button, Divider, Menu, Typography } from "@mui/material";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import ArrowDropUpIcon from "@mui/icons-material/ArrowDropUp";
import LogoutIcon from "@mui/icons-material/Logout";

import { useUserStore } from "@store/user.store";
import { ChangePasswordModal } from "./changePasswordModal";

export const ProfileMenu: React.FC = () => {
  const { t } = useTranslation();
  const { user, logout } = useUserStore();

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);
  const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };
  const handleClose = () => {
    setAnchorEl(null);
  };

  const [isModalOpen, setIsModalOpen] = useState(false);

  const onChangePassword = () => {
    setIsModalOpen(true);
  };

  const handleLogout = () => {
    logout();
  };

  if (!user) {
    return <></>;
  }

  return (
    <>
      <Button
        variant="text"
        onClick={handleClick}
        sx={{ color: "#fff", textTransform: "capitalize" }}
        endIcon={open ? <ArrowDropUpIcon /> : <ArrowDropDownIcon />}
        id="open-profile-button"
      >
        {user.username}
      </Button>
      <Menu anchorEl={anchorEl} open={open} onClose={handleClose}>
        <Box
          component="div"
          sx={{
            display: "flex",
            flexDirection: "column",
            minWidth: 340,
            gap: 1.5,
            pt: 1,
            px: 2,
          }}
        >
          <MenuItem
            title={t("admin.username")}
            value={user.username}
            capitalize={true}
          />
          {user.email && (
            <MenuItem title={t("admin.email")} value={user.email} />
          )}
          <MenuItem title={t("general.role")} value={user.role} />
          {user.external_user && (
            <Button
              variant="outlined"
              onClick={onChangePassword}
              id="change-password-button"
            >
              {t("home.changePassword")}
            </Button>
          )}
        </Box>
        <Divider sx={{ my: 2 }} />
        <Button
          fullWidth
          color="secondary"
          startIcon={<LogoutIcon />}
          onClick={handleLogout}
          id="logout-button"
          dir="ltr"
        >
          {t("home.logout")}
        </Button>
      </Menu>
      <ChangePasswordModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  );
};

interface MenuItemProps {
  title: string;
  value: string;
  capitalize?: boolean;
}

const MenuItem: React.FC<MenuItemProps> = ({ title, value, capitalize }) => {
  return (
    <Box component="div">
      <Typography sx={{ opacity: 0.6 }}>{title}</Typography>
      <Typography
        sx={{
          fontWeight: "bold",
          textTransform: capitalize ? "capitalize" : "none",
        }}
      >
        {value}
      </Typography>
    </Box>
  );
};
