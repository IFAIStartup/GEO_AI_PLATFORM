import React, { useEffect } from "react";
import { IconButton, SvgIcon } from "@mui/material";
import { useTranslation } from "react-i18next";

import AeFlag from "@assets/ae.svg?react";
import GbFlag from "@assets/gb.svg?react";
import RuFlag from "@assets/ru.svg?react";

const LANGUAGES = ["en", "ar", "ru"];

export const LanguageSwitch: React.FC = () => {
  const { i18n } = useTranslation();

  useEffect(() => {
    document.dir = i18n.resolvedLanguage === "ar" ? "rtl" : "";
  }, []);

  const handleChange = () => {
    const index = LANGUAGES.indexOf(i18n.resolvedLanguage || "");
    const newIndex = index >= LANGUAGES.length - 1 ? 0 : index + 1;
    i18n.changeLanguage(LANGUAGES[newIndex]);
    document.dir = i18n.resolvedLanguage === "ar" ? "rtl" : "";
  };

  const getFlag = () => {
    switch (i18n.resolvedLanguage) {
      case "en":
        return GbFlag;
      case "ar":
        return AeFlag;
      case "ru":
        return RuFlag;
      default:
        return GbFlag;
    }
  };

  return (
    <>
      <IconButton
        aria-label="change-language"
        sx={{ width: 28, height: 28, overflow: "hidden", padding: 0 }}
        onClick={handleChange}
      >
        <SvgIcon
          component={getFlag()}
          inheritViewBox
          sx={{ fontSize: "60px" }}
        />
      </IconButton>
    </>
  );
};
