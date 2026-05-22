import React from "react";
import { Box } from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import TimelineIcon from "@mui/icons-material/Timeline";
import HistoryIcon from "@mui/icons-material/History";
import HomeNavCard from "./HomeNavCard";
import HomeTitle from "./HomeTitle";
import { Map } from "@mui/icons-material";

const NAV_ITEMS = [
  {
    title: "Dashboard",
    description:
      "Monitor real-time agent telemetry, track errors, and assess system health at a glance.",
    route: "/dashboard",
    Icon: DashboardIcon,
  },
  {
    title: "Explorer",
    description: "Explore multi-turn traces, visualize span hierarchies, and compare executions side by side.",
    route: "/explorer",
    Icon: TimelineIcon,
  },
  {
    title: "History",
    description:
      "Access recent traces, episodes, and validated feedback for quick review.",
    route: "/history",
    Icon: HistoryIcon,
  },
  {
    title: "Roadmap",
    description:
      "Turn failures into targeted training tasks with automated curriculum generation.",
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
        justifyContent: "flex-start",
        height: "100%",
        minHeight: 0,
        overflowY: "auto",
        gap: { xs: 3, md: 4 },
        p: { xs: 2, sm: 3, md: 4 },
        pb: { xs: 4, md: 5 },
      }}
    >
      <HomeTitle />

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr" },
          gap: { xs: 2, sm: 3 },
          width: "100%",
          maxWidth: 960,
          alignContent: "start",
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
