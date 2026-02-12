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
} from "@mui/material";
import FileDownloadOutlinedIcon from "@mui/icons-material/FileDownloadOutlined";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import { ArrowDownward, ArrowUpward, Refresh } from "@mui/icons-material";
import CurriculumList from "./CurriculumList";
import { generateCurriculum, fetchCurriculumTasks } from "../utils/api";
import { handleExportJSON, handleExportJSONL } from "../utils/utils";

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
    setIsLoading(true);
    try {
      await generateCurriculum();
      await handleRefresh();
    } catch (error) {
      console.error("Error generating curriculum:", error);
    } finally {
      setIsLoading(false);
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
    <Box
      sx={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        bgcolor: "background.default",
      }}
    >
      <Box
        sx={{
          p: 3,
          borderBottom: 1,
          borderColor: "divider",
          bgcolor: "background.paper",
        }}
      >
        <Box sx={{ pb: 2 }}>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
            Roadmap
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Generate sample tasks for your agents
          </Typography>
        </Box>

        <Box
          sx={{
            display: "flex",
            gap: 2,
            alignItems: "center",
            justifyContent: "space-between",
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
                bgcolor: "action.hover",
                borderRadius: 1,
                border: 1,
                borderColor: "text.secondary",
                userSelect: "none",
              }}
            >
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {tasks.length}
              </Typography>
            </Box>
          </Box>

          <Box sx={{ display: "flex", gap: 2 }}>
            {/* JSON export button */}
            <Button
              variant="outlined"
              startIcon={<FileDownloadOutlinedIcon />}
              onClick={handleExportJSON}
              disabled={isLoading || tasks.length === 0}
            >
              Export JSON
            </Button>

            {/* JSONL export button */}
            <Button
              variant="outlined"
              startIcon={<FileDownloadOutlinedIcon />}
              onClick={handleExportJSONL}
              disabled={isLoading || tasks.length === 0}
            >
              Export JSONL
            </Button>

            {/* Generate tasks button */}
            <Button
              variant="contained"
              startIcon={<AutoAwesomeIcon />}
              onClick={handleGenerate}
              disabled={isLoading}
            >
              Generate
            </Button>
          </Box>
        </Box>
      </Box>

      <Box
        sx={{
          flex: 1,
          overflow: "auto",
        }}
      >
        <CurriculumList tasks={sortedTasks} isLoading={isLoading} />
      </Box>
    </Box>
  );
};

export default Roadmap;
