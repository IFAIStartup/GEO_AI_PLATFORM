import { Box, styled } from "@mui/material";

export const ModalContent = styled(Box)({
  position: "absolute",
  direction: "ltr",
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
  width: 560,
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  backgroundColor: "#fff",
  padding: 24,
  paddingBottom: 40,
  borderRadius: 4,
  boxShadow:
    "0px 2px 1px -1px rgba(0, 0, 0, 0.20), 0px 1px 1px 0px rgba(0, 0, 0, 0.14), 0px 1px 3px 0px rgba(0, 0, 0, 0.12)",
});
