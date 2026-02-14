import { createTheme } from "@mui/material";

export const createAppTheme = (themeMode: "light" | "dark") => {
  const theme = createTheme({
    palette: {
      mode: themeMode,
      primary: {
        main: themeMode === "dark" ? "#ececec" : "#1976d2",
      },
      ...(themeMode === "dark" && {
        background: {
          default: "#2b2b2bff",
          paper: "#3a3a3aff",
        },
        text: {
          primary: "#ececec",
          secondary: "#b4b4b4",
        },
      }),
    },
  });

  const customScrollbar = {
    "::-webkit-scrollbar": {
      width: "8px",
    },
    "::-webkit-scrollbar-track": {
      backgroundColor: theme.palette.background.paper,
      borderRadius: "4px",
    },
    "::-webkit-scrollbar-thumb": {
      backgroundColor: theme.palette.action.disabled,
      borderRadius: "4px",
      "&:hover": {
        backgroundColor: theme.palette.action.active,
      },
    },
  };

  return createTheme({
    ...theme,
    components: {
      MuiButton: {
        styleOverrides: {
          root: { textTransform: "none" },
        },
      },
      MuiCssBaseline: {
        styleOverrides: {
          ...customScrollbar,
        },
      },
    },
  });
};
