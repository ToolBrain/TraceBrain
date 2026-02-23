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
import { Search, Timeline, ViewList, Refresh, ManageSearch } from "@mui/icons-material";
import { fetchTraces, fetchEpisodes } from "../utils/api";
import TracesTable from "../shared/TracesTable";
import EpisodesTable from "../shared/EpisodesTable";
import type { Trace, Episode } from "../../types/trace";

const DEBOUNCE_MS = 300;

type ViewMode = "traces" | "episodes" | "advanced";

const TraceExplorer: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>("traces");
  const [tracePage, setTracePage] = useState(0);
  const [episodePage, setEpisodePage] = useState(0);
  const currentPage = viewMode === "traces" ? tracePage : episodePage;
  const setCurrentPage = viewMode === "traces" ? setTracePage : setEpisodePage;
  const [rowsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");

  const [traces, setTraces] = useState<Trace[]>([]);
  const [totalTraces, setTotalTraces] = useState(0);
  const [tracesLoading, setTracesLoading] = useState(false);

  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [totalEpisodes, setTotalEpisodes] = useState(0);
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
    if (viewMode === "advanced") return;
    setTracesLoading(true);
    fetchTraces(tracePage * rowsPerPage, rowsPerPage, debouncedQuery || undefined)
      .then((data) => {
        setTraces(data.traces);
        setTotalTraces(data.total);
      })
      .finally(() => setTracesLoading(false));
  }, [tracePage, rowsPerPage, debouncedQuery]);

  // Fetches paginated episodes
  useEffect(() => {
    if (viewMode === "advanced") return;
    setEpisodesLoading(true);
    fetchEpisodes(episodePage * rowsPerPage, rowsPerPage, debouncedQuery || undefined)
      .then((data) => {
        setEpisodes(data.episodes);
        setTotalEpisodes(data.total);
      })
      .finally(() => setEpisodesLoading(false));
  }, [episodePage, rowsPerPage, debouncedQuery]);

  const loading = viewMode === "traces" ? tracesLoading : episodesLoading;
  const currentTotal = viewMode === "traces" ? totalTraces : totalEpisodes;

  // Switches between different views
  const handleViewModeChange = (
    _: React.SyntheticEvent,
    newValue: ViewMode,
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

  // Resets pagination and refetches
  const handleRefresh = () => {
    setTracePage(0);
    setEpisodePage(0);
    setSearchQuery("");
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
            Trace Explorer
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
              <Tab
                icon={<ManageSearch />}
                iconPosition="start"
                label="Advanced Search"
                value="advanced"
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

export default TraceExplorer;