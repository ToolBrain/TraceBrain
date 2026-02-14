import * as React from "react";
import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import Container from "@mui/material/Container";
import Button from "@mui/material/Button";
import IconButton from "@mui/material/IconButton";
import tracebrainimg from "../../assets/tracebrain.png";
import { useNavigate, useLocation } from "react-router-dom";
import { LightMode, DarkMode } from "@mui/icons-material";
import { useSettings } from "../../contexts/SettingsContext";

const pages = [
  { label: "Dashboard", path: "/dashboard" },
  { label: "Explorer", path: "/explorer" },
  { label: "History", path: "/history" },
  { label: "Roadmap", path: "/roadmap" },
  { label: "Settings", path: "/settings" },
];

const DashboardHeader: React.FC = () => {
  const { settings, updateSettings } = useSettings();
  const location = useLocation();
  const nav = useNavigate();

  const toggleTheme = () => {
    updateSettings((draft) => {
      draft.appearance.theme =
        draft.appearance.theme === "light" ? "dark" : "light";
    });
  };

  const navigate = (path: string) => {
    if (location.pathname !== path) {
      nav(path);
    }
  };

  return (
    <>
      <AppBar position="sticky">
        <Container maxWidth={false}>
          <Toolbar disableGutters>
            <Box
              onClick={() => navigate("/")}
              sx={{
                cursor: "pointer",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                userSelect: "none",
              }}
            >
              <Box
                component={"img"}
                src={tracebrainimg}
                sx={{ width: "5rem" }}
              />
              <Typography
                variant="h6"
                noWrap
                sx={{
                  mr: 2,
                  fontFamily: "monospace",
                  fontWeight: 700,
                  letterSpacing: ".3rem",
                  color: "inherit",
                  textDecoration: "none",
                  userSelect: "none",
                }}
              >
                TRACEBRAIN
              </Typography>
            </Box>

            <Box sx={{ flexGrow: 1, display: "flex" }}>
              {pages.map((page) => (
                <Button
                  key={page.path}
                  onClick={() => navigate(page.path)}
                  sx={{
                    my: 2,
                    color: "white",
                    display: "block",
                    fontSize: "1rem",
                    borderBottom:
                      location.pathname === page.path
                        ? "3px solid white"
                        : "3px solid transparent",
                    fontWeight: 600,
                    "&:hover": {
                      backgroundColor: "action.hover",
                    },
                  }}
                >
                  {page.label}
                </Button>
              ))}
            </Box>

            <IconButton onClick={toggleTheme} color="inherit">
              {settings.appearance.theme === "light" ? (
                <DarkMode />
              ) : (
                <LightMode />
              )}
            </IconButton>
          </Toolbar>
        </Container>
      </AppBar>
    </>
  );
};
export default DashboardHeader;
