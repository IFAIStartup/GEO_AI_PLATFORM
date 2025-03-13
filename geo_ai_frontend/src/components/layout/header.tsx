/// <reference types="vite-plugin-svgr/client" />
import React, { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";
import { AppBar, Box, IconButton, Link, SvgIcon, Toolbar } from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";

import logoUrl from "@assets/logo.png";

import MLFlowLogo from "@assets/mlflow_logo_icon.svg?react";
import CVATLogo from "@assets/cvat_logo.svg?react";

import { useUserStore } from "@store/user.store";
import { ProfileMenu } from "@components/layout/profileMenu";
import { LanguageSwitch } from "@components/shared/languageSwitch";
import { Role } from "@models/user";
import { useMLStore } from "@store/ml.store";

const navLinks = [
  {
    path: "/projects",
    name: "home.projects",
    id: "projects",
    roles: [Role.User, Role.ML, Role.Admin],
  },
  {
    path: "/history",
    name: "home.history",
    id: "history",
    roles: [Role.User, Role.ML, Role.Admin],
  },
  {
    path: "/ml",
    name: "home.ml",
    id: "ml",
    roles: [Role.ML, Role.Admin],
  },
  {
    path: "/admin",
    name: "home.admin",
    id: "admin",
    roles: [Role.Admin],
  },
];

const nextcloudURL = import.meta.env.VITE_NEXTCLOUD_URL;
const cvatURL = import.meta.env.VITE_CVAT_URL;
const dozzleURL = import.meta.env.VITE_DOZZLE_URL;

export const Header: React.FC = () => {
  const { t } = useTranslation();
  const user = useUserStore((state) => state.user);
  const mlFlowURL = useMLStore((state) => state.mlFlowURL);
  const getMLFlowURL = useMLStore((state) => state.getMLFlowURL);

  useEffect(() => {
    getMLFlowURL();
  }, []);

  return (
    <AppBar position="sticky" elevation={0}>
      <Toolbar
        sx={{ display: "flex", justifyContent: "space-between" }}
        dir="ltr"
      >
        <Box component="div" sx={{ display: "flex" }}>
          <img src={logoUrl} width={112} />
        </Box>
        <Box
          component="div"
          sx={{ display: "flex", gap: 1, alignItems: "center" }}
        >
          {navLinks
            .filter((l) => l.roles.includes(user?.role || Role.User))
            .map((link) => (
              <Link
                key={link.path}
                component={NavLink}
                to={link.path}
                sx={{
                  minWidth: 120,
                  p: 1,
                  fontSize: "16px",
                  fontWeight: "bold",
                  color: "#fff",
                  textAlign: "center",
                  borderRadius: "4px",
                  textDecoration: "none",
                  "&:hover, &.active": {
                    backgroundColor: "#fff",
                    color: "primary.main",
                  },
                }}
                id={`${link.id}-header-button`}
              >
                {t(link.name)}
              </Link>
            ))}
        </Box>
        <Box
          component="div"
          sx={{ display: "flex", gap: 1, alignItems: "center" }}
        >
          {cvatURL && [Role.Admin].includes(user?.role || Role.User) && (
            <IconButton
              href={cvatURL}
              target="_blank"
              title="CVAT"
              sx={{
                color: "#fff",
                fontSize: "40px",
              }}
            >
              <SvgIcon component={CVATLogo} inheritViewBox fontSize="inherit" />
            </IconButton>
          )}
          {dozzleURL && [Role.Admin].includes(user?.role || Role.User) && (
            <IconButton
              href={dozzleURL}
              target="_blank"
              title="Dozzle"
              sx={{
                color: "#fff",
                fontSize: "20px",
                padding: "6px 11px",
              }}
            >
              dz
            </IconButton>
          )}
          {nextcloudURL && (
            <IconButton
              href={nextcloudURL}
              target="_blank"
              title="Nextcloud"
              sx={{
                color: "#fff",
              }}
            >
              <CloudUploadIcon />
            </IconButton>
          )}
          {mlFlowURL &&
            [Role.ML, Role.Admin].includes(user?.role || Role.User) && (
              <IconButton
                href={mlFlowURL}
                target="_blank"
                title="ML Flow"
                sx={{
                  color: "#fff",
                }}
              >
                <SvgIcon
                  component={MLFlowLogo}
                  inheritViewBox
                  sx={{ fontSize: "20px" }}
                />
              </IconButton>
            )}
          {/* <NotificationMenu /> */}
          <ProfileMenu />
          <LanguageSwitch />
        </Box>
      </Toolbar>
    </AppBar>
  );
};
