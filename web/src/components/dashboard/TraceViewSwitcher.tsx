import { Box, IconButton } from "@mui/material";
import { ChevronLeft, ChevronRight } from "@mui/icons-material";
import { useState } from "react";
import TraceGraph from "./TraceGraph";
import type { Trace } from "../../types/trace";
import TraceErrorChart from "./TraceErrorChart";

interface TraceViewSwitcherProps {
  traces: Trace[];
}

const VIEWS = [TraceGraph, TraceErrorChart];

const TraceViewSwitcher: React.FC<TraceViewSwitcherProps> = ({ traces }) => {
  const [activeIndex, setActiveIndex] = useState(0);

  const ActiveView = VIEWS[activeIndex];

  return (
    <Box
      sx={{
        position: "relative",
        width: "100%",
        height: 360,
      }}
    >
      <Box sx={{ height: "100%"}}>
        <ActiveView traces={traces} />
      </Box>

      {activeIndex > 0 && (
        <IconButton
          size="large"
          onClick={() => setActiveIndex((i) => i - 1)}
          sx={{
            position: "absolute",
            left: -18,
            top: "50%",
            transform: "translateY(-50%)",
            width: 36,
            height: 36,
            "& svg": { transition: "transform 0.2s ease" },
            "&:hover svg": { transform: "translateX(-2px)" },
          }}
        >
          <ChevronLeft sx={{ fontSize: 36, color: "primary.main" }} />
        </IconButton>
      )}

      {activeIndex < VIEWS.length - 1 && (
        <IconButton
          size="large"
          onClick={() => setActiveIndex((i) => i + 1)}
          sx={{
            position: "absolute",
            right: -18,
            top: "50%",
            transform: "translateY(-50%)",
            width: 36,
            height: 36,
            "& svg": { transition: "transform 0.2s ease" },
            "&:hover svg": { transform: "translateX(2px)" },
          }}
        >
          <ChevronRight sx={{ fontSize: 36, color: "primary.main" }} />
        </IconButton>
      )}
    </Box>
  );
};

export default TraceViewSwitcher;