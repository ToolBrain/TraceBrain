import React from "react";
import { Box } from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import TimelineIcon from "@mui/icons-material/Timeline";
import HistoryIcon from "@mui/icons-material/History";
import SettingsIcon from "@mui/icons-material/Settings";
import HomeNavCard from "./HomeNavCard";
import HomeTitle from "./HomeTitle";
import { Map } from "@mui/icons-material";

const NAV_ITEMS = [
  {
    title: "Dashboard",
    description:
      "Monitor real-time training runs, view live metrics, and get a high-level overview of your agents' training progress.",
    route: "/dashboard",
    Icon: DashboardIcon,
  },
  {
    title: "Explorer",
    description: "Search and filter through your agent traces and episodes.",
    route: "/explorer",
    Icon: TimelineIcon,
  },
  {
    title: "History",
    description:
      "Browse and revisit traces and episodes you've previously opened and explored.",
    route: "/history",
    Icon: HistoryIcon,
  },
  {
    title: "Roadmap",
    description:
      "Generate sample training scenarios for your agents to learn from.",
    route: "/roadmap",
    Icon: Map,
  },
];

const Home: React.FC = () => {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        gap: 4,
        p: 4,
      }}
    >
      <HomeTitle />

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr" },
          gap: 3,
          width: "100%",
          height: "100%",
          maxHeight: 640,
          maxWidth: 960,
        }}
      >
        {NAV_ITEMS.map((item) => (
          <HomeNavCard key={item.route} {...item} />
        ))}
      </Box>
    </Box>
  );
};

export default Home;
