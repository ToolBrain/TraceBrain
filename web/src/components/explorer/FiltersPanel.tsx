import React from "react";
import type { EpisodeFilters, TraceFilters } from "./types";
import { Box } from "@mui/material";
import TraceFiltersPanel from "./TraceFiltersPanel";
import EpisodesFiltersPanel from "./EpisodeFiltersPanel";

export const DEFAULT_TRACE_FILTERS: TraceFilters = {
  status: "",
  errorType: "",
  minRating: null,
  minConfidence: null,
  maxConfidence: null,
  startTime: "",
  endTime: "",
};

export const DEFAULT_EPISODE_FILTERS: EpisodeFilters = {
  minConfidenceLt: null
};

interface FilterPanelProps {
  mode: string;
  traceFilters: TraceFilters;
  episodeFilters: EpisodeFilters;
  onTraceFiltersChange: (filters: TraceFilters) => void;
  onEpisodeFiltersChange: (filters: EpisodeFilters) => void;
}

const FiltersPanel: React.FC<FilterPanelProps> = ({
  mode,
  traceFilters,
  episodeFilters,
  onTraceFiltersChange,
  onEpisodeFiltersChange,
}) => {
  return (
    <Box sx={{ mb: 2 }}>
      {mode === "traces" ? (
        <TraceFiltersPanel
          filters={traceFilters}
          onChange={onTraceFiltersChange}
        />
      ) : (
        <EpisodesFiltersPanel
          filters={episodeFilters}
          onChange={onEpisodeFiltersChange}
        />
      )}
    </Box>
  );
};

export default FiltersPanel;
