import React, { useEffect } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { Container, Box } from "@mui/material";

import { useUserStore } from "@store/user.store";
import { AlertSnackbar } from "@components/shared/alertSnackbar";
import { Header } from "./header";

export const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useUserStore((state) => state);

  useEffect(() => {
    if (!user) {
      navigate("/login", { replace: true });
    }
  }, [user]);

  return (
    <Box
      component="div"
      sx={{ display: "flex", flexDirection: "column", height: "100%" }}
    >
      <Header />
      {location.pathname.startsWith("/projects") ? (
        <Outlet />
      ) : (
        <Container sx={{ pt: 4, pb: 2 }}>
          <Outlet />
        </Container>
      )}
      <AlertSnackbar />
    </Box>
  );
};
