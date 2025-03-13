import { createTheme } from "@mui/material";

export const theme = createTheme({
  palette: {
    primary: {
      main: "#007EFF",
    },
    secondary: {
      main: "#757575",
    },
    success: {
      main: "#00C3B8",
    },
    warning: {
      main: "#FF9800",
    },
    error: {
      main: "#EF5350",
    },
  },
  typography: {
    fontFamily: "JannaLT, Roboto, Arial",
    h3: {
      fontSize: "40px",
      fontWeight: "bold",
    },
    h4: {
      fontSize: "30px",
    },
    h5: {
      fontSize: "24px",
      fontWeight: "bold",
    },
    subtitle1: {
      fontSize: "18px",
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          fontWeight: "bold",
        },
        contained: {
          "&.Mui-disabled": {
            backgroundColor: "#297CFF4D",
            color: "#FFFFFF80",
          },
        },
      },
      defaultProps: {
        disableElevation: true,
      },
    },
    MuiToggleButton: {
      styleOverrides: {
        root: ({ theme }) => ({
          "&.Mui-selected, &.Mui-selected:hover": {
            color: "#fff",
            backgroundColor: theme.palette.primary.main,
          },
        }),
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          padding: "12px 16px",
        },
      },
    },
    MuiCssBaseline: {
      styleOverrides: `
        @font-face {
          font-family: 'JannaLT';
          src: url('/fonts/subset-JannaLT-Regular.eot');
          src: url('/fonts/subset-JannaLT-Regular.eot?#iefix') format('embedded-opentype'),
            url('/fonts/subset-JannaLT-Regular.woff2') format('woff2'),
            url('/fonts/subset-JannaLT-Regular.woff') format('woff'),
            url('/fonts/subset-JannaLT-Regular.ttf') format('truetype'),
            url('/fonts/subset-JannaLT-Regular.svg#JannaLT-Regular') format('svg');
          font-weight: normal;
          font-style: normal;
          unicode-range: U+0600-06FF;
        }
        
        @font-face {
          font-family: 'JannaLT';
          src: url('/fonts/subset-JannaLT-Bold.eot');
          src: url('/fonts/subset-JannaLT-Bold.eot?#iefix') format('embedded-opentype'),
            url('/fonts/subset-JannaLT-Bold.woff2') format('woff2'),
            url('/fonts/subset-JannaLT-Bold.woff') format('woff'),
            url('/fonts/subset-JannaLT-Bold.ttf') format('truetype'),
            url('/fonts/subset-JannaLT-Bold.svg#JannaLT-Bold') format('svg');
          font-weight: bold;
          font-style: normal;
          unicode-range: U+0600-06FF;
        }
      `,
    },
  },
});
