import React, { useState, useEffect } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  TablePagination,
  TextField,
  InputAdornment,
  IconButton,
  Tooltip,
} from "@mui/material";
import { Search, Timeline, ViewList, Refresh } from "@mui/icons-material";
import { useSearchParams } from "react-router-dom";
import { fetchTraces, fetchEpisodes } from "../utils/api";
import TracesTable from "../shared/TracesTable";
import EpisodesTable from "../shared/EpisodesTable";
import type { Trace, Episode } from "../../types/trace";
import FiltersPanel, { DEFAULT_EPISODE_FILTERS, DEFAULT_TRACE_FILTERS } from "./FiltersPanel";
import type { EpisodeFilters, TraceFilters } from "./types";

const DEBOUNCE_MS = 300;

type ViewMode = "traces" | "episodes";

const TRACE_PARAM_MAP: { key: string; value: keyof TraceFilters; type?: "number" }[] = [
  { key: "status", value: "status" },
  { key: "error_type", value: "errorType" },
  { key: "min_rating", value: "minRating", type: "number" },
  { key: "min_confidence", value: "minConfidence", type: "number" },
  { key: "max_confidence", value: "maxConfidence", type: "number" },
  { key: "start_time", value: "startTime" },
  { key: "end_time", value: "endTime" },
];

const EPISODE_PARAM_MAP: { key: string; value: keyof EpisodeFilters; type?: "number" }[] = [
  { key: "min_confidence_lt", value: "minConfidenceLt", type: "number" },
];

const traceFiltersFromParams = (params: URLSearchParams): TraceFilters => {
  const patch: Partial<TraceFilters> = {};
  TRACE_PARAM_MAP.forEach(({ key, value, type }) => {
    const val = params.get(key);
    if (val) (patch as any)[value] = type === "number" ? Number(val) : val;
  });
  return { ...DEFAULT_TRACE_FILTERS, ...patch };
};

const episodeFiltersFromParams = (params: URLSearchParams): EpisodeFilters => {
  const patch: Partial<EpisodeFilters> = {};
  EPISODE_PARAM_MAP.forEach(({ key, value, type }) => {
    const val = params.get(key);
    if (val) (patch as any)[value] = type === "number" ? Number(val) : val;
  });
  return { ...DEFAULT_EPISODE_FILTERS, ...patch };
};

const traceFiltersToParams = (filters: TraceFilters): Record<string, string | null> => {
  const patch: Record<string, string | null> = {};
  TRACE_PARAM_MAP.forEach(({ key, value }) => {
    const val = filters[value];
    patch[key] = val != null && String(val) !== "" ? String(val) : null;
  });
  return patch;
};

const episodeFiltersToParams = (filters: EpisodeFilters): Record<string, string | null> => {
  const patch: Record<string, string | null> = {};
  EPISODE_PARAM_MAP.forEach(({ key, value }) => {
    const val = filters[value];
    patch[key] = val != null && String(val) !== "" ? String(val) : null;
  });
  return patch;
};

const Explorer: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const viewMode = (searchParams.get("type") === "episodes" ? "episodes" : "traces") as ViewMode;
  const tracePage = Number(searchParams.get("page") ?? 0);
  const episodePage = Number(searchParams.get("page") ?? 0);
  const currentPage = viewMode === "traces" ? tracePage : episodePage;
  const traceFilters = traceFiltersFromParams(searchParams);
  const episodeFilters = episodeFiltersFromParams(searchParams);

  const [rowsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");

  const [traces, setTraces] = useState<Trace[]>([]);
  const [totalTraces, setTotalTraces] = useState(0);
  const [tracesLoading, setTracesLoading] = useState(false);

  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [totalEpisodes, setTotalEpisodes] = useState(0);
  const [episodesLoading, setEpisodesLoading] = useState(false);

  const updateParams = (patch: Record<string, string | null>, resetPage = true) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      Object.entries(patch).forEach(([k, v]) => {
        if (v == null || v === "") next.delete(k);
        else next.set(k, v);
      });
      if (resetPage) next.set("page", "0");
      return next;
    }, { replace: true });
  };

  // Debounce search query and reset pagination on change
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Fetches paginated traces
  useEffect(() => {
    if (viewMode !== "traces") return;
    setTracesLoading(true);
    fetchTraces(tracePage * rowsPerPage, rowsPerPage, debouncedQuery || undefined, traceFilters)
      .then((data) => {
        setTraces(data.traces);
        setTotalTraces(data.total);
      })
      .finally(() => setTracesLoading(false));
  }, [searchParams, debouncedQuery]);

  // Fetches paginated episodes
  useEffect(() => {
    if (viewMode !== "episodes") return;
    setEpisodesLoading(true);
    fetchEpisodes(episodePage * rowsPerPage, rowsPerPage, debouncedQuery || undefined, episodeFilters)
      .then((data) => {
        setEpisodes(data.episodes);
        setTotalEpisodes(data.total);
      })
      .finally(() => setEpisodesLoading(false));
  }, [searchParams, debouncedQuery]);

  const loading = viewMode === "traces" ? tracesLoading : episodesLoading;
  const currentTotal = viewMode === "traces" ? totalTraces : totalEpisodes;

  // Switches between different views
  const handleViewModeChange = (_: React.SyntheticEvent, newValue: ViewMode) => {
    updateParams({ type: newValue });
  };

  // Handles page change
  const handleChangePage = (_: React.MouseEvent<HTMLButtonElement> | null, newPage: number) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set("page", String(newPage));
      return next;
    }, { replace: true });
  };

  // Resets pagination and refetches
  const handleRefresh = () => {
    setSearchQuery("");
    updateParams({ page: "0" }, false);
  };

  return (
    <Box sx={{ p: 3, height: "100%", display: "flex", flexDirection: "column" }}>
      <Box
        sx={{
          mb: 3,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
            Explorer
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Browse and search the <Box component="span" sx={{ fontWeight: "bold" }}>TraceStore</Box>
          </Typography>
        </Box>
        <Tooltip title="Refresh">
          <IconButton onClick={handleRefresh}>
            <Refresh />
          </IconButton>
        </Tooltip>
      </Box>

      <Card
        sx={{
          flexGrow: 1,
          display: "flex",
          flexDirection: "column",
          minHeight: 0,
        }}
      >
        <CardContent
          sx={{
            flexGrow: 1,
            display: "flex",
            flexDirection: "column",
            minHeight: 0,
          }}
        >
          <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 2 }}>
            <Tabs value={viewMode} onChange={handleViewModeChange}>
              <Tab icon={<Timeline />} iconPosition="start" label="Traces" value="traces" />
              <Tab icon={<ViewList />} iconPosition="start" label="Episodes" value="episodes" />
            </Tabs>
          </Box>
          <Box sx={{ mb: 3 }}>
            <TextField
              fullWidth
              placeholder="Search ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                },
              }}
            />
          </Box>

          <FiltersPanel
            mode={viewMode}
            traceFilters={traceFilters}
            episodeFilters={episodeFilters}
            onTraceFiltersChange={(filters) => updateParams({ ...traceFiltersToParams(filters), type: "traces" })}
            onEpisodeFiltersChange={(filters) => updateParams({ ...episodeFiltersToParams(filters), type: "episodes" })}
          />

          <Box sx={{ flexGrow: 1, overflow: "auto", minHeight: 0 }}>
            {viewMode === "traces" ? (
              <TracesTable traces={traces} loading={loading} />
            ) : viewMode === "episodes" ? (
              <EpisodesTable episodes={episodes} loading={loading} />
            ) : null}
          </Box>

          <TablePagination
            sx={{ flexShrink: 0 }}
            rowsPerPageOptions={[]}
            component="div"
            count={currentTotal}
            rowsPerPage={rowsPerPage}
            page={currentPage}
            onPageChange={handleChangePage}
          />
        </CardContent>
      </Card>
    </Box>
  );
};

export default Explorer;