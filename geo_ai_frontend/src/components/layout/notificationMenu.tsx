import React, { MouseEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Box,
  Button,
  IconButton,
  Divider,
  Menu,
  Typography,
} from "@mui/material";
import NotificationsIcon from "@mui/icons-material/Notifications";
import DoneAllIcon from "@mui/icons-material/DoneAll";
import VisibilityIcon from "@mui/icons-material/Visibility";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";

export const NotificationMenu: React.FC = () => {
  const { t } = useTranslation();

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);
  const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };
  const handleClose = () => {
    setAnchorEl(null);
  };

  return (
    <>
      <IconButton
        onClick={handleClick}
        color="inherit"
        id="notifications-button"
      >
        <NotificationsIcon />
      </IconButton>
      <Menu anchorEl={anchorEl} open={open} onClose={handleClose}>
        <Box
          component="div"
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: 400,
            px: 2,
          }}
        >
          <Typography variant="body1" sx={{ fontWeight: "bold" }}>
            {t("notifications.title")}
          </Typography>
          <Button
            variant="text"
            startIcon={<DoneAllIcon />}
            sx={{ textTransform: "none", fontWeight: "normal" }}
            id="mark-as-read-button"
          >
            {t("notifications.markAsRead")}
          </Button>
        </Box>
        <Divider sx={{ mt: 1, mb: 2 }} />
        {notifications.map((notification, index) => (
          <Box component="div" key={notification.id}>
            {!!index && <Divider sx={{ mt: 1, mb: 2 }} />}
            <Box component="div" sx={{ px: 2 }}>
              <Box
                component="div"
                sx={{ display: "flex", gap: 1.5, alignItems: "center" }}
              >
                <Box
                  component="div"
                  sx={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    width: 42,
                    height: 42,
                    borderRadius: 0.5,
                    backgroundColor:
                      notification.status === "Success" ? "#EFFFF0" : "#FFF6F6",
                  }}
                >
                  {notification.status === "Success" ? (
                    <CheckCircleOutlineIcon sx={{ color: "success.dark" }} />
                  ) : (
                    <ErrorOutlineIcon sx={{ color: "error.dark" }} />
                  )}
                </Box>
                <Box component="div">
                  <Typography variant="body2" sx={{ fontWeight: "bold" }}>
                    {notification.text}
                  </Typography>
                  <Typography variant="body2">
                    {t("intlRelativeTime", {
                      val: notification.date,
                      numeric: "auto",
                    })}
                  </Typography>
                </Box>
              </Box>
              <Button
                variant="text"
                startIcon={<VisibilityIcon />}
                sx={{ textTransform: "none", fontWeight: "normal", mt: 0.5 }}
              >
                {t("notifications.viewResult")}
              </Button>
            </Box>
          </Box>
        ))}
      </Menu>
    </>
  );
};

const notifications = [
  {
    id: 1,
    status: "Success",
    text: "Project 1 detection completed",
    date: -1,
  },
  {
    id: 2,
    status: "Success",
    text: "Compare Project 1 and Project 2 completed",
    date: -2,
  },
  {
    id: 3,
    status: "Error",
    text: "An error occurred while detecting Project 5",
    date: -9,
  },
];
