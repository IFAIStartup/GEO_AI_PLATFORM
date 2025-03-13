import React from "react";
import { Box, CircularProgress } from "@mui/material";

export const LoadingPage: React.FC = () => {
  return (
    <Box
      component="div"
      sx={{ display: "flex", justifyContent: "center", pt: 8 }}
    >
      <CircularProgress size="80px" />
    </Box>
  );
};
