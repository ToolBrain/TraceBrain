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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
} from "@mui/material";
import {
  ArrowDownward,
  ArrowUpward,
  AutoAwesome,
  DeleteOutline,
  FileDownloadOutlined,
  Refresh,
  TaskAlt,
  Tune,
} from "@mui/icons-material";
import CurriculumList from "./CurriculumList";
import CurriculumConfiguration from "./CurriculumConfiguration";
import {
  generateCurriculum,
  fetchCurriculumTasks,
  fetchExportCurriculum,
  deleteAllCurriculumTasks,
  markAllCurriculumTasksComplete,
  deleteCurriculumTask,
  markCurriculumTaskComplete,
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
    severity: "success" as "success" | "error" | "warning",
    key: 0,
  });

  const [generateAnchorEl, setGenerateAnchorEl] = useState<HTMLButtonElement | null>(null);

  const [selectedErrorTypes, setSelectedErrorTypes] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem("curriculum");
      return saved ? (JSON.parse(saved).errorTypes ?? []) : [];
    } catch {
      return [];
    }
  });
  const [taskLimit, setTaskLimit] = useState<number>(() => {
    try {
      const saved = localStorage.getItem("curriculum");
      return saved ? (JSON.parse(saved).taskLimit ?? 5) : 5;
    } catch {
      return 5;
    }
  });

  const [deleteAllConfirmOpen, setDeleteAllConfirmOpen] = useState(false);

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
      key: Date.now(),
    });

    try {
      const result = await generateCurriculum({
        error_types: selectedErrorTypes.length > 0 ? selectedErrorTypes : null,
        limit: taskLimit,
      });
      await handleRefresh();
      if (result.tasks_generated === 0) {
        setSnackbar({
          open: true,
          message: "No tasks generated",
          severity: "warning",
          key: Date.now(),
        });
      } else {
        setSnackbar({
          open: true,
          message: `${result.tasks_generated} task${result.tasks_generated === 1 ? "" : "s"} generated`,
          severity: "success",
          key: Date.now(),
        });
      }
    } catch (error) {
      console.error("Error generating curriculum:", error);
      setSnackbar({
        open: true,
        message: "Failed to generate curriculum",
        severity: "error",
        key: Date.now(),
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

  // Handle mark all tasks as complete
  const handleMarkAllComplete = async () => {
    const pendingTasks = tasks.filter((t) => t.status === "pending");

    const prev = tasks;
    setTasks(tasks.map((t) => ({ ...t, status: "completed" })));
    setSnackbar({
      open: true,
      message: `${pendingTasks.length} task${pendingTasks.length !== 1 ? "s" : ""} marked as complete`,
      severity: "success",
      key: Date.now(),
    });
    try {
      await markAllCurriculumTasksComplete();
    } catch (error) {
      console.error("Error marking all tasks as complete:", error);
      setTasks(prev);
      setSnackbar({
        open: true,
        message: "Failed to mark all tasks as complete",
        severity: "error",
        key: Date.now(),
      });
    }
  };

  // Handle delete all tasks
  const handleDeleteAll = async () => {
    setDeleteAllConfirmOpen(false);
    const prev = tasks;
    const count = tasks.length;
    setTasks([]);
    setSnackbar({
      open: true,
      message: `${count} task${count !== 1 ? "s" : ""} deleted`,
      severity: "success",
      key: Date.now(),
    });
    try {
      await deleteAllCurriculumTasks();
    } catch (error) {
      console.error("Error deleting all tasks:", error);
      setTasks(prev);
      setSnackbar({
        open: true,
        message: "Failed to delete all tasks",
        severity: "error",
        key: Date.now(),
      });
    }
  };

  // Handle mark single task as complete
  const handleMarkComplete = async (id: number) => {
    const prev = tasks;
    setTasks(tasks.map((t) => (t.id === id ? { ...t, status: "completed" } : t)));
    setSnackbar({
      open: true,
      message: "Task marked as complete",
      severity: "success",
      key: Date.now(),
    });
    try {
      await markCurriculumTaskComplete(id);
    } catch (error) {
      console.error("Error marking task as complete:", error);
      setTasks(prev);
      setSnackbar({
        open: true,
        message: "Failed to mark task as complete",
        severity: "error",
        key: Date.now(),
      });
    }
  };

  // Handle delete single task
  const handleDelete = async (id: number) => {
    const prev = tasks;
    setTasks(tasks.filter((t) => t.id !== id));
    setSnackbar({ open: true, message: "Task deleted", severity: "success", key: Date.now() });
    try {
      await deleteCurriculumTask(id);
    } catch (error) {
      console.error("Error deleting task:", error);
      setTasks(prev);
      setSnackbar({
        open: true,
        message: "Failed to delete task",
        severity: "error",
        key: Date.now(),
      });
    }
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
    <Box sx={{ p: 3, height: "100%", display: "flex", flexDirection: "column" }}>
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
              variant="outlined"
              onClick={handleRefresh}
              disabled={isLoading}
              size="small"
              sx={{
                border: 1,
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

            {/* Mark all tasks as complete button */}
            <Button
              variant="outlined"
              startIcon={<TaskAlt />}
              onClick={handleMarkAllComplete}
              disabled={isLoading || tasks.length === 0}
              color="success"
            >
              Mark All Complete
            </Button>

            {/* Delete all tasks button */}
            <Button
              variant="outlined"
              startIcon={<DeleteOutline />}
              onClick={() => setDeleteAllConfirmOpen(true)}
              disabled={isLoading || tasks.length === 0}
              color="error"
            >
              Delete All
            </Button>

            {/* Generate tasks button */}
            <Button
              variant="contained"
              startIcon={
                isGenerating ? <CircularProgress size={16} color="inherit" /> : <AutoAwesome />
              }
              onClick={handleGenerate}
              disabled={isLoading || isGenerating}
            >
              {isGenerating ? "Generating..." : "Generate"}
            </Button>

            {/* Configuration menu button*/}
            <IconButton
              onClick={(e) => setGenerateAnchorEl(e.currentTarget)}
              disabled={isLoading || isGenerating}
              size="small"
            >
              <Tune fontSize="small" />
            </IconButton>

            <CurriculumConfiguration
              anchorEl={generateAnchorEl}
              onClose={() => setGenerateAnchorEl(null)}
              onConfirm={(errorTypes, limit) => {
                setSelectedErrorTypes(errorTypes);
                setTaskLimit(limit);
                setGenerateAnchorEl(null);
              }}
            />
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
          <CurriculumList
            tasks={sortedTasks}
            isLoading={isLoading}
            onMarkComplete={handleMarkComplete}
            onDelete={handleDelete}
          />
        </CardContent>
      </Card>

      <Dialog open={deleteAllConfirmOpen} onClose={() => setDeleteAllConfirmOpen(false)}>
        <DialogTitle>Delete All Tasks?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            You are about to permanently delete all{" "}
            <Box component="span" sx={{ fontWeight: "bold" }}>
              {tasks.length} task{tasks.length !== 1 ? "s" : ""}
            </Box>
            . This cannot be recovered.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteAllConfirmOpen(false)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleDeleteAll}>
            Delete All
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        key={snackbar.key}
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
