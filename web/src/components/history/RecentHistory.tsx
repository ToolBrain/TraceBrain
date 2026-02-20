import React, { useState, useEffect, useMemo } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  TablePagination,
  Tooltip,
  IconButton,
  TextField,
  InputAdornment,
} from "@mui/material";
import { Timeline, ViewList, Delete, Search } from "@mui/icons-material";
import type { Episode, Trace } from "../../types/trace";
import type { HistoryList } from "./types";
import { fetchHistory, clearHistory } from "../utils/api";
import TracesTable from "../shared/TracesTable";
import EpisodesTable from "../shared/EpisodesTable";

const DEBOUNCE_MS = 300;

const RecentHistory: React.FC = () => {
  const [viewMode, setViewMode] = useState<"traces" | "episodes">("traces");
  const [tracePage, setTracePage] = useState(0);
  const [episodePage, setEpisodePage] = useState(0);
  const currentPage = viewMode === "traces" ? tracePage : episodePage;
  const setCurrentPage = viewMode === "traces" ? setTracePage : setEpisodePage;
  const [rowsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");

  const [tracesData, setTracesData] = useState<HistoryList | null>(null);
  const [tracesLoading, setTracesLoading] = useState(false);
  const [episodesData, setEpisodesData] = useState<HistoryList | null>(null);
  const [episodesLoading, setEpisodesLoading] = useState(false);

  // Debounce search query and reset pagination on change
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery);
      setTracePage(0);
      setEpisodePage(0);
    }, DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Fetches paginated traces
  useEffect(() => {
    setTracesLoading(true);
    fetchHistory(
      rowsPerPage,
      tracePage * rowsPerPage,
      "trace",
      debouncedQuery || undefined,
    )
      .then(setTracesData)
      .finally(() => setTracesLoading(false));
  }, [tracePage, rowsPerPage, debouncedQuery]);

  // Fetches paginated episodes
  useEffect(() => {
    setEpisodesLoading(true);
    fetchHistory(
      rowsPerPage,
      episodePage * rowsPerPage,
      "episode",
      debouncedQuery || undefined,
    )
      .then(setEpisodesData)
      .finally(() => setEpisodesLoading(false));
  }, [episodePage, rowsPerPage, debouncedQuery]);

  // Initializes traces
  const traces = (tracesData?.data as Trace[]) ?? [];
  const totalTraces = tracesData?.total ?? 0;

  // Initializes episodes
  const episodes = useMemo<Episode[]>(
    () =>
      Object.entries((episodesData?.data as Record<string, Trace[]>) ?? {}).map(
        ([episode_id, traces]) => ({ episode_id, traces }),
      ),
    [episodesData],
  );
  const totalEpisodes = episodesData?.total ?? 0;

  const loading = viewMode === "traces" ? tracesLoading : episodesLoading;
  const currentTotal = viewMode === "traces" ? totalTraces : totalEpisodes;

  // Switches between traces and episodes view
  const handleViewModeChange = (
    _: React.SyntheticEvent,
    newValue: "traces" | "episodes",
  ) => {
    setViewMode(newValue);
  };

  // Handles page change
  const handleChangePage = (
    _: React.MouseEvent<HTMLButtonElement> | null,
    newPage: number,
  ) => {
    setCurrentPage(newPage);
  };

  // Clears browsing history
  const handleClearHistory = async () => {
    try {
      await clearHistory();
      setTracesData(null);
      setEpisodesData(null);
      setTracePage(0);
      setEpisodePage(0);
    } catch (error) {
      console.error("Failed to clear history:", error);
    }
  };

  return (
    <Box
      sx={{ p: 3, height: "100%", display: "flex", flexDirection: "column" }}
    >
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
            Recent History
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Browse your recently viewed
          </Typography>
        </Box>
        <Tooltip title="Clear History">
          <IconButton onClick={handleClearHistory}>
            <Delete />
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
          <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 3 }}>
            <Tabs value={viewMode} onChange={handleViewModeChange}>
              <Tab
                icon={<Timeline />}
                iconPosition="start"
                label="Traces"
                value="traces"
              />
              <Tab
                icon={<ViewList />}
                iconPosition="start"
                label="Episodes"
                value="episodes"
              />
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

          <Box sx={{ flexGrow: 1, overflow: "auto", minHeight: 0 }}>
            {viewMode === "traces" ? (
              <TracesTable traces={traces} loading={loading} />
            ) : (
              <EpisodesTable episodes={episodes} loading={loading} />
            )}
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

export default RecentHistory;
