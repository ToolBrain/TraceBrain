import { Box, IconButton } from "@mui/material";
import { useState, useEffect, useMemo } from "react";
import { ChevronLeft, ChevronRight } from "@mui/icons-material";
import Sidebar from "./SideBar";
import MainContent from "./MainContent";
import type { Trace } from "../../types/trace";
import type { FilterOption } from "./types";
import { fetchTraces } from "../utils/api";
import { useSettings } from "../../contexts/SettingsContext";
import { traceGetErrorType, traceGetStatus } from "../utils/traceUtils";
import TraceViewSwitcher from "./TraceViewSwitcher";

const DRAWER_WIDTH = 240;
const COLLAPSED_WIDTH = 60;

const FILTER_CONFIG = {
  Status: {
    options: [
      { key: "running", label: "Running" },
      { key: "completed", label: "Completed" },
      { key: "failed", label: "Failed" },
      { key: "needs_review", label: "Review" },
    ],
    getValue: (trace: Trace) => traceGetStatus(trace) || "running",
  },
  Error_Type: {
    options: [
      { key: "logic_loop", label: "Logic Loop" },
      { key: "hallucination", label: "Hallucination" },
      { key: "invalid_tool_usage", label: "Invalid Tool" },
      { key: "tool_execution_error", label: "Execution Error" },
      { key: "format_error", label: "Format Error" },
      { key: "misinterpretation", label: "Misinterpretation" },
      { key: "context_overflow", label: "Context Overflow" },
      { key: "general_failure", label: "General Failure" },
      { key: "none", label: "None" },
    ],
    getValue: (trace: Trace) => traceGetErrorType(trace) || "none",
  },
} as const;

const Dashboard: React.FC = () => {
  const { settings } = useSettings();
  const [traces, setTraces] = useState<Trace[]>([]);
  const [open, setOpen] = useState(true);
  const [showContent, setShowContent] = useState(true);

  const [filters, setFilters] = useState<Record<string, FilterOption[]>>(() => {
    const initialFilters: Record<string, FilterOption[]> = {};
    Object.entries(FILTER_CONFIG).forEach(([category, config]) => {
      initialFilters[category] = config.options.map((option) => ({
        ...option,
        checked: false,
        count: 0,
      }));
    });
    return initialFilters;
  });

  // Calculate filter counts based on traces
  useEffect(() => {
    setFilters((prevFilters) => {
      const newFilters = { ...prevFilters };

      Object.entries(FILTER_CONFIG).forEach(([category, config]) => {
        const counts: Record<string, number> = {};

        config.options.forEach((option) => {
          counts[option.key] = 0;
        });

        traces.forEach((trace) => {
          const value = config.getValue(trace);
          if (counts[value] !== undefined) {
            counts[value]++;
          }
        });

        newFilters[category] = newFilters[category].map((filter) => ({
          ...filter,
          count: counts[filter.key] || 0,
        }));
      });

      return newFilters;
    });
  }, [traces]);

  // Function to fetch the latest traces
  const handleFetchTraces = async () => {
    try {
      const data = await fetchTraces();
      if (data) setTraces(data.traces);
    } catch (error) {
      console.error("Failed to fetch traces:", error);
    }
  };

  // Initial traces fetch
  useEffect(() => {
    handleFetchTraces();
  }, []);

  // Auto refresh traces
  useEffect(() => {
    if (!settings.refresh.autoRefresh) return;

    const interval = setInterval(
      handleFetchTraces,
      settings.refresh.refreshInterval * 1000,
    );

    return () => clearInterval(interval);
  }, [settings.refresh.autoRefresh, settings.refresh.refreshInterval]);

  // Check if any filter is checked
  const hasActiveFilters = Object.values(filters).some((category) =>
    category.some((filter) => filter.checked),
  );

  // Clear all filters
  const clearFilters = () => {
    setFilters((prevFilters) => {
      const newFilters = { ...prevFilters };
      Object.keys(newFilters).forEach((category) => {
        newFilters[category] = newFilters[category].map((filter) => ({
          ...filter,
          checked: false,
        }));
      });
      return newFilters;
    });
  };

  // Filter traces based on active filters
  const filteredTraces = useMemo(() => {
    if (!hasActiveFilters) {
      return traces;
    }

    // Checked filters
    const checkedFilters: Record<string, string[]> = {};
    Object.keys(filters).forEach((category) => {
      const checked = filters[category]
        .filter((f) => f.checked)
        .map((f) => f.key);

      if (checked.length > 0) {
        checkedFilters[category] = checked;
      }
    });

    // Filter traces
    return traces.filter((trace) => {
      return Object.keys(checkedFilters).every((category) => {
        const config = FILTER_CONFIG[category as keyof typeof FILTER_CONFIG];
        const traceValue = config.getValue(trace);
        return checkedFilters[category].includes(traceValue);
      });
    });
  }, [traces, filters, hasActiveFilters]);

  // Slight delay before displaying contents
  useEffect(() => {
    if (open) {
      const timer = setTimeout(() => setShowContent(true), 200);
      return () => clearTimeout(timer);
    } else {
      setShowContent(false);
    }
  }, [open]);

  return (
    <Box sx={{ display: "flex", height: "100%" }}>
      <Box
        sx={{
          width: open ? DRAWER_WIDTH : COLLAPSED_WIDTH,
          flexShrink: 0,
          bgcolor: "background.paper",
          borderRight: 1,
          borderColor: "divider",
          transition: "width 0.3s",
          overflow: "hidden",
        }}
      >
        <Box
          sx={{
            display: "flex",
            justifyContent: open ? "flex-end" : "center",
            p: 1,
            float: "right",
          }}
        >
          <IconButton onClick={() => setOpen(!open)}>
            {open ? <ChevronLeft /> : <ChevronRight />}
          </IconButton>
        </Box>
        {showContent && (
          <Sidebar
            filters={filters}
            setFilters={setFilters}
            onClearFilters={clearFilters}
            hasActiveFilters={hasActiveFilters}
          />
        )}
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: "background.default",
          overflow: "auto",
        }}
      >
        <MainContent
          traces={filteredTraces}
          onFetchTraces={handleFetchTraces}
          view={<TraceViewSwitcher traces={filteredTraces} />}
        />
      </Box>
    </Box>
  );
};

export default Dashboard;
