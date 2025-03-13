import { TextField, styled } from "@mui/material";

export const LoginTextField = styled(TextField)({
  ".MuiInputBase-root": {
    backgroundColor: "#fff",
    "&.Mui-error": {
      backgroundColor: "#FFE1E1",
    },
  },
  ".MuiInputBase-input": {
    fontSize: "18px",
  },
  ".MuiFormHelperText-root.Mui-error": {
    color: "#FFD4D4",
  },
});
