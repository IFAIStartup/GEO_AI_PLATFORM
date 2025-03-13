import React from "react";
import { Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Box, Card, Link } from "@mui/material";

import logoUrl from "@assets/logo.png";
import bgUrl from "@assets/login_bg.png";
import { LanguageSwitch } from "@components/shared/languageSwitch";

export const LoginLayout: React.FC = () => {
  const { t } = useTranslation();

  return (
    <Box
      component="div"
      sx={{
        position: "relative",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        gap: 2,
        minHeight: "100vh",
        backgroundImage: `url(${bgUrl}), linear-gradient(147.79deg, #007EFF 8.69%, #101597 97.52%)`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      <Box
        component="div"
        sx={{
          position: "absolute",
          top: 16,
          right: 16,
          display: "flex",
          alignItems: "center",
          gap: 1,
        }}
        dir="ltr"
      >
        <LanguageSwitch />
        <img src={logoUrl} />
      </Box>

      <Card
        sx={{
          position: "relative",
          display: "flex",
          flexDirection: "column",
          gap: 4,
          width: 520,
          px: 8,
          py: 6,
          backgroundImage: "linear-gradient(180deg, #1580FF 0%, #084CCE 100%)",
          color: "#fff",
          borderRadius: "20px",
          boxShadow: "0px 10px 30px rgba(13, 40, 169, 0.2)",
          overflow: "visible",
        }}
      >
        <Outlet />
      </Card>
      <Box component="div" sx={{ display: "flex", gap: 2 }} dir="ltr">
        <Link
          href="mailto:gis.tps@aam.gov.ae"
          underline="hover"
          variant="body2"
          sx={{ color: "#5AA9FF" }}
          id="contact-support-button"
        >
          {t("login.contact", { email: "gis.tps@aam.gov.ae" })}
        </Link>
        <Link
          href="#"
          underline="hover"
          variant="body2"
          sx={{ color: "#5AA9FF" }}
          id="privacy-button"
        >
          {t("login.privacy")}
        </Link>
      </Box>
    </Box>
  );
};
