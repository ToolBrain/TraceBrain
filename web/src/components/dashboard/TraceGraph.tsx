import { BarChart } from "@mui/x-charts/BarChart";
import { Box, Typography, IconButton, Select, MenuItem } from "@mui/material";
import { ChevronLeft, ChevronRight } from "@mui/icons-material";
import { useState, useMemo } from "react";
import type { Trace } from "../../types/trace";

interface TraceGraphProps {
  traces: Trace[];
}

type TimeRange = "1h" | "1d" | "1w" | "1m";

const TIME_CONFIGS = {
  "1h": { slots: 12, interval: 5 * 60 * 1000, label: "1 Hour" },
  "1d": { slots: 24, interval: 60 * 60 * 1000, label: "1 Day" },
  "1w": { slots: 7, interval: 24 * 60 * 60 * 1000, label: "1 Week" },
  "1m": { slots: 30, interval: 24 * 60 * 60 * 1000, label: "1 Month" },
} as const;

// Get the time step for navigation based on the selected time range
const getNavigationStep = (range: TimeRange): number => {
  const steps = {
    "1h": 60 * 60 * 1000,
    "1d": 24 * 60 * 60 * 1000,
    "1w": 7 * 24 * 60 * 60 * 1000,
    "1m": 30 * 24 * 60 * 60 * 1000,
  };
  return steps[range];
};

// Format time labels for the x-axis based on the selected time range
const formatTimeLabel = (time: Date, range: TimeRange): string => {
  if (range === "1h" || range === "1d") {
    return time.toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  } else if (range === "1w") {
    const day = time.toLocaleDateString("en-GB", { weekday: "short" });
    const timeStr = time.toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
    return `${day} ${timeStr}`;
  } else {
    return time.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "short",
    });
  }
};

// Function to get trace start and end times from its spans
const getTraceTimeBounds = (
  trace: Trace,
): { start: Date; end: Date } | null => {
  if (trace.spans.length === 0) return null;

  const spanTimes = trace.spans.map((span) => ({
    start: new Date(span.start_time).getTime(),
    end: new Date(span.end_time).getTime(),
  }));

  const start = Math.min(...spanTimes.map((t) => t.start));
  const end = Math.max(...spanTimes.map((t) => t.end));

  return { start: new Date(start), end: new Date(end) };
};

const TraceGraph: React.FC<TraceGraphProps> = ({ traces }) => {
  const [timeRange, setTimeRange] = useState<TimeRange>("1h");
  const [endDate, setEndDate] = useState(new Date());

  const config = TIME_CONFIGS[timeRange];

  const { timeSlots, timeLabels, traceCounts } = useMemo(() => {
    const slots: Date[] = [];
    for (let i = config.slots - 1; i >= 0; i--) {
      slots.push(new Date(endDate.getTime() - i * config.interval));
    }

    const labels = slots.map((time) => formatTimeLabel(time, timeRange));

    const counts = new Array(slots.length).fill(0);

    // Process each trace and count it in the appropriate time slot
    traces.forEach((trace) => {
      const bounds = getTraceTimeBounds(trace);
      if (!bounds) return;

      const { start } = bounds;

      // Find which time slot this trace belongs to based on its start time
      const slotIndex = slots.findIndex((slot, index) => {
        if (index === slots.length - 1) return start >= slot;
        return start >= slot && start < slots[index + 1];
      });

      if (slotIndex !== -1) {
        counts[slotIndex] += 1;
      }
    });

    return { timeSlots: slots, timeLabels: labels, traceCounts: counts };
  }, [endDate, config.slots, config.interval, timeRange, traces]);

  const startTime = timeSlots[0].toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });

  const endTime = timeSlots[timeSlots.length - 1].toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });

  // Navigate backward or forward in time
  const navigate = (direction: "prev" | "next") => {
    const step = getNavigationStep(timeRange);
    const multiplier = direction === "prev" ? -1 : 1;
    const newDate = new Date(endDate.getTime() + step * multiplier);

    // Prevent navigating beyond the current time
    if (direction === "next" && newDate > new Date()) {
      return;
    }

    setEndDate(newDate);
  };

  // Check if clicking next would exceed the current time
  const wouldExceedCurrentTime = () => {
    const step = getNavigationStep(timeRange);
    const nextDate = new Date(endDate.getTime() + step);
    return nextDate > new Date();
  };

  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          px: 1,
          py: 1,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <IconButton size="small" onClick={() => navigate("prev")}>
            <ChevronLeft fontSize="small" />
          </IconButton>
          <Typography variant="body2" color="text.secondary">
            {startTime}
          </Typography>
        </Box>

        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <Select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as TimeRange)}
            size="small"
            sx={{ minWidth: 100 }}
          >
            {Object.entries(TIME_CONFIGS).map(([key, { label }]) => (
              <MenuItem key={key} value={key}>
                {label}
              </MenuItem>
            ))}
          </Select>
        </Box>

        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Typography variant="body2" color="text.secondary">
            {endTime}
          </Typography>
          <IconButton
            size="small"
            onClick={() => navigate("next")}
            disabled={wouldExceedCurrentTime()}
          >
            <ChevronRight fontSize="small" />
          </IconButton>
        </Box>
      </Box>

      <BarChart
        series={[{ data: traceCounts, color: "#1976d2", id: "traceCount" }]}
        xAxis={[
          {
            data: timeLabels,
            scaleType: "band",
            tickLabelStyle: { fontSize: 10 },
          },
        ]}
        height={200}
      />
    </Box>
  );
};

export default TraceGraph;
