import React, { useState, useMemo, useEffect } from "react";
import {
  Box,
  Typography,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Snackbar,
  Alert,
  CircularProgress,
  Card,
  CardContent,
} from "@mui/material";
import {
  ArrowDownward,
  ArrowUpward,
  AutoAwesome,
  FileDownloadOutlined,
  Refresh,
} from "@mui/icons-material";
import CurriculumList from "./CurriculumList";
import {
  generateCurriculum,
  fetchCurriculumTasks,
  fetchExportCurriculum,
} from "../utils/api";
import { exportJSON, exportJSONL } from "../utils/utils";

interface CurriculumTask {
  id: number;
  task_description: string;
  reasoning: string;
  status: "pending" | "completed";
  priority: "high" | "medium" | "low";
  created_at: string;
}

const sortOptions = [
  { value: "datetime", label: "DateTime" },
  { value: "priority", label: "Priority" },
  { value: "status", label: "Status" },
];

const priorityValues = {
  high: 3,
  medium: 2,
  low: 1,
};

const statusValues = {
  pending: 2,
  completed: 1,
};

const Roadmap: React.FC = () => {
  const [sortBy, setSortBy] = useState("priority");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const [tasks, setTasks] = useState<CurriculumTask[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success" as "success" | "error",
  });

  // initial fetch of tasks
  useEffect(() => {
    handleRefresh();
  }, []);

  // Handle refresh
  const handleRefresh = async () => {
    setIsLoading(true);
    try {
      const data = await fetchCurriculumTasks();
      setTasks(data);
    } catch (error) {
      console.error("Error fetching curriculum tasks:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle generate
  const handleGenerate = async () => {
    setIsGenerating(true);

    setSnackbar({
      open: true,
      message: "Curriculum generation started in background",
      severity: "success",
    });

    try {
      await generateCurriculum();
      await handleRefresh();
    } catch (error) {
      console.error("Error generating curriculum:", error);
      setSnackbar({
        open: true,
        message: "Failed to generate curriculum",
        severity: "error",
      });
    } finally {
      setTimeout(() => setIsGenerating(false), 3000);
    }
  };

  // Handle export to JSON
  const handleExportJSON = async () => {
    const data = await fetchExportCurriculum("json");
    exportJSON(data);
  };

  // Handle export to JSONL
  const handleExportJSONL = async () => {
    const jsonlContent = await fetchExportCurriculum("jsonl");
    exportJSONL(jsonlContent);
  };

  // Sort tasks based on sortBy and sortOrder
  const sortedTasks = useMemo(() => {
    const tasksWithMetrics = tasks.map((task) => {
      const dateTime = new Date(task.created_at).getTime();
      const priority = priorityValues[task.priority];
      const status = statusValues[task.status];

      return { task, dateTime, priority, status };
    });

    return tasksWithMetrics
      .sort((a, b) => {
        let compareValue = 0;

        if (sortBy === "datetime") {
          compareValue = a.dateTime - b.dateTime;
        } else if (sortBy === "priority") {
          compareValue = a.priority - b.priority;
        } else if (sortBy === "status") {
          compareValue = a.status - b.status;
        }

        return sortOrder === "asc" ? compareValue : -compareValue;
      })
      .map((item) => item.task);
  }, [tasks, sortBy, sortOrder]);

  return (
    <Box
      sx={{ p: 3, height: "100%", display: "flex", flexDirection: "column" }}
    >
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
          Training Roadmap
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Browse existing tasks or generate new ones
        </Typography>

        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
            {/* Sort by */}
            <FormControl size="small">
              <InputLabel>Sort By</InputLabel>
              <Select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                label="Sort By"
                IconComponent={() => (
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
                    }}
                    sx={{ mr: 1 }}
                  >
                    {sortOrder === "asc" ? (
                      <ArrowUpward fontSize="small" />
                    ) : (
                      <ArrowDownward fontSize="small" />
                    )}
                  </IconButton>
                )}
              >
                {sortOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Refresh button */}
            <Button
              onClick={handleRefresh}
              disabled={isLoading}
              size="small"
              sx={{
                border: "2px solid",
                borderColor: "gray",
                borderRadius: "4px",
                height: "40px",
                "&:hover": {
                  borderColor: "text.primary",
                  bgcolor: "action.hover",
                },
              }}
            >
              <Refresh fontSize="small" />
            </Button>

            {/* Tasks count */}
            <Box
              sx={{
                px: 1.5,
                height: "40px",
                display: "flex",
                alignItems: "center",
                userSelect: "none",
                borderLeft: 2,
                borderColor: "divider",
              }}
            >
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ fontWeight: 600, fontFamily: "monospace" }}
              >
                {tasks.length} Tasks
              </Typography>
            </Box>
          </Box>

          <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
            {/* JSON export button */}
            <Button
              variant="outlined"
              startIcon={<FileDownloadOutlined />}
              onClick={handleExportJSON}
              disabled={isLoading || tasks.length === 0}
            >
              Export JSON
            </Button>

            {/* JSONL export button */}
            <Button
              variant="outlined"
              startIcon={<FileDownloadOutlined />}
              onClick={handleExportJSONL}
              disabled={isLoading || tasks.length === 0}
            >
              Export JSONL
            </Button>

            {/* Generate tasks button */}
            <Button
              variant="contained"
              startIcon={
                isGenerating ? (
                  <CircularProgress size={16} color="inherit" />
                ) : (
                  <AutoAwesome />
                )
              }
              onClick={handleGenerate}
              disabled={isLoading || isGenerating}
            >
              {isGenerating ? "Generating..." : "Generate"}
            </Button>
          </Box>
        </Box>
      </Box>

      <Card sx={{ flexGrow: 1, display: "flex", flexDirection: "column" }}>
        <CardContent
          sx={{
            flexGrow: 1,
            display: "flex",
            flexDirection: "column",
            overflow: "auto",
            p: 0,
          }}
        >
          <CurriculumList tasks={sortedTasks} isLoading={isLoading} />
        </CardContent>
      </Card>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert
          severity={snackbar.severity}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Roadmap;
