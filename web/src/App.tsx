import { ThemeProvider, CssBaseline, Box } from "@mui/material";
import { useMemo } from "react";
import { useSettings } from "./contexts/SettingsContext";
import HomePage from "./pages/HomePage";
import DashboardHeader from "./components/layout/DashboardHeader";
import TracePage from "./pages/TracePage";
import { Routes, Route } from "react-router-dom";
import SettingsPage from "./pages/SettingsPage";
import DashboardPage from "./pages/DashboardPage";
import ExplorerPage from "./pages/ExplorerPage";
import HistoryPage from "./pages/HistoryPage";
import { createAppTheme } from "./styles/theme";
import { Librarian } from "./components/chat/Librarian";
import RoadmapPage from "./pages/RoadmapPage";

const App: React.FC = () => {
  const { settings } = useSettings();

  const theme = useMemo(
    () => createAppTheme(settings.appearance.theme),
    [settings.appearance.theme],
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          height: "100vh",
          overflow: "hidden",
        }}
      >
        <DashboardHeader />
        <Box
          sx={{
            flex: 1,
            overflow: "auto",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            p: 0.5,
          }}
        >
          <Box
            sx={{
              width: "calc(100% - 1rem)",
              height: "calc(100% - 1rem)",
              bgcolor: "background.paper",
              borderRadius: 1,
              border: 2,
              borderColor: "divider",
            }}
          >
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/explorer" element={<ExplorerPage />} />
              <Route path="/history" element={<HistoryPage />} />
              <Route path="/roadmap" element={<RoadmapPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/trace/:id" element={<TracePage />} />
              <Route path="*" element={<div>Page not found!</div>} />
            </Routes>
            <Librarian />
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
};

export default App;
