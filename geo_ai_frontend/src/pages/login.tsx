import React, { ChangeEvent, Dispatch, SetStateAction, useState } from "react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  FormGroup,
  Link,
  Typography,
} from "@mui/material";

import { useUserStore } from "@store/user.store";
import { LoginTextField } from "@components/login/loginTextField";
import { ApiError } from "@models/common";
import { ERRORS } from "@models/error";

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const login = useUserStore((state) => state.login);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string>();

  const onInput = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
    setter: Dispatch<SetStateAction<string>>
  ) => {
    setError(undefined);
    setter(e.target.value);
  };

  const onLogin = () => {
    login({
      email: username,
      password,
    })
      .then(() => {
        navigate("/projects");
      })
      .catch((e: ApiError) => {
        const err = e.response?.data.detail;
        if (err?.code === "INVALID_LOGIN_PASSWORD") {
          setError(t(ERRORS[err.code]));
        } else {
          setError(t(ERRORS.OTHER));
        }
      });
  };

  return (
    <>
      <Typography variant="h3">{t("login.title")}</Typography>
      <LoginTextField
        required
        fullWidth
        id="username"
        placeholder={t("login.usernamePlaceholder")}
        autoComplete="email"
        value={username}
        onChange={(e) => onInput(e, setUsername)}
        error={!!error}
        autoFocus
      />
      <Box
        component="div"
        sx={{ display: "flex", flexDirection: "column", gap: 1 }}
      >
        <LoginTextField
          required
          fullWidth
          id="password"
          placeholder={t("login.pwdPlaceholder")}
          type={showPassword ? "text" : "password"}
          autoComplete="current-password"
          value={password}
          onChange={(e) => onInput(e, setPassword)}
          error={!!error}
        />
        <FormGroup>
          <FormControlLabel
            control={
              <Checkbox
                checked={showPassword}
                onChange={(e) => setShowPassword(e.target.checked)}
                sx={{
                  color: "#fff",
                  "&.Mui-checked": {
                    color: "#fff",
                  },
                }}
              />
            }
            label={t("login.showPwdLabel")}
            sx={{
              mx: "-11px",
            }}
            id="show-password-checkbox"
          />
        </FormGroup>
      </Box>
      <Box component="div">
        {!!error && (
          <Typography variant="body2" sx={{ mt: -3, mb: 1 }} color="#FFD4D4">
            {error}
          </Typography>
        )}
        <Button
          fullWidth
          variant="contained"
          size="large"
          disabled={!username || !password || !!error}
          onClick={onLogin}
          id="login-button"
        >
          {t("login.loginBtn")}
        </Button>
      </Box>
      <Link
        component={RouterLink}
        to="/restore-access"
        sx={{
          fontSize: "12px",
          fontWeight: "bold",
          color: "#fff",
          textTransform: "uppercase",
          mt: -1,
        }}
        id="restore-access-button"
      >
        {t("login.restore")}
      </Link>
    </>
  );
};
