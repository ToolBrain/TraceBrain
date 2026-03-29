import * as React from "react";
import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import Container from "@mui/material/Container";
import Button from "@mui/material/Button";
import IconButton from "@mui/material/IconButton";
import { useNavigate, useLocation } from "react-router-dom";
import { LightMode, DarkMode } from "@mui/icons-material";
import { useSettings } from "../../contexts/SettingsContext";
import lightOwl from "../../assets/light-owl.png";
import darkOwl from "../../assets/dark-owl.png";

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
  const isDark = settings.appearance.theme === "dark";
  const logoSrc = settings.appearance.theme === "dark" ? darkOwl : lightOwl;

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
                sx={{
                  width: 40,
                  height: 40,
                  mr: 1.5,
                  borderRadius: "50%",
                  display: "grid",
                  placeItems: "center",
                  background: "linear-gradient(145deg, rgba(255,255,255,0.95), rgba(255,255,255,0.75))",
                  border: "1px solid",
                  borderColor: isDark ? "rgba(255,255,255,0.35)" : "rgba(255,255,255,0.65)",
                  boxShadow: isDark
                    ? "0 6px 14px rgba(0,0,0,0.35)"
                    : "0 5px 12px rgba(0,0,0,0.2)",
                }}
              >
                <Box
                  component="img"
                  src={logoSrc}
                  alt="TraceBrain"
                  sx={{
                    width: 28,
                    height: 28,
                    display: "block",
                  }}
                />
              </Box>
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
                    my: 1.5,
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
