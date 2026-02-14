import React, { useState } from "react";
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
} from "@mui/material";
import { Timeline, ViewList, Delete } from "@mui/icons-material";

const RecentHistory: React.FC = () => {
  const [viewMode, setViewMode] = useState<"traces" | "episodes">("traces");
  const [page, setPage] = useState(0);
  const [rowsPerPage] = useState(20);

  const [totalTraces] = useState(0);
  const [totalEpisodes] = useState(0);

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

  // Clears browsing history
  const clearHistory = () => {};

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
            Recent History
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Browse your recently viewed
          </Typography>
        </Box>
        <Tooltip title="Clear History">
          <IconButton onClick={clearHistory}>
            <Delete />
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

export default RecentHistory;
