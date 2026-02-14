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
  CircularProgress,
  Tooltip,
} from "@mui/material";
import { Search, Timeline, ViewList, Refresh } from "@mui/icons-material";
import type { Episode, Trace } from "../../types/trace";
import { fetchTraces, fetchEpisodeTraces } from "../utils/api";

const TraceExplorer: React.FC = () => {
  const [viewMode, setViewMode] = useState<"traces" | "episodes">("traces");
  const [page, setPage] = useState(0);
  const [rowsPerPage] = useState(20);
  const [searchQuery, setSearchQuery] = useState("");

  const [traces, setTraces] = useState<Trace[]>([]);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [totalTraces, setTotalTraces] = useState(0);
  const [totalEpisodes, setTotalEpisodes] = useState(0);

  const [loading, setLoading] = useState(false);

  const handleViewModeChange = (
    _: React.SyntheticEvent,
    newValue: "traces" | "episodes",
  ) => {
    setViewMode(newValue);
    setPage(0);
  };

  const handleChangePage = (
    _: React.MouseEvent<HTMLButtonElement> | null,
    newPage: number,
  ) => {
    setPage(newPage);
  };

  const currentTotal = viewMode === "traces" ? totalTraces : totalEpisodes;

  return (
    <Box sx={{ p: 3 }}>
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
            Browse and search the{" "}
            <Box component="span" sx={{ fontWeight: "bold" }}>
              TraceStore
            </Box>
          </Typography>
        </Box>
        <Tooltip title="Refresh">
          <IconButton onClick={() => setPage(0)}>
            <Refresh />
          </IconButton>
        </Tooltip>
      </Box>

      <Card>
        <CardContent>
          <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 3 }}>
            <Tabs value={viewMode} onChange={handleViewModeChange}>
              <Tab
                icon={<Timeline />}
                iconPosition="start"
                label={"Traces"}
                value="traces"
              />
              <Tab
                icon={<ViewList />}
                iconPosition="start"
                label={"Episodes"}
                value="episodes"
              />
            </Tabs>
          </Box>

          <Box sx={{ mb: 3 }}>
            <TextField
              fullWidth
              placeholder={"Search ID..."}
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

          <TablePagination
            rowsPerPageOptions={[]} // Can change this later for users to select how many items per page
            component="div"
            count={currentTotal}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
          />
        </CardContent>
      </Card>
    </Box>
  );
};

export default TraceExplorer;
