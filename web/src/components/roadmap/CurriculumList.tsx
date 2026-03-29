import React from "react";
import { Box, Typography, Skeleton, IconButton, Tooltip } from "@mui/material";
import { Assignment, DeleteOutline, TaskAlt } from "@mui/icons-material";
import StatusChip from "../shared/StatusChip";
import type { CurriculumTask } from "./types";

interface CurriculumListProps {
  tasks: CurriculumTask[];
  isLoading?: boolean;
  onMarkComplete: (id: number) => void;
  onDelete: (id: number) => void;
}

const CurriculumList: React.FC<CurriculumListProps> = ({
  tasks,
  isLoading = false,
  onMarkComplete,
  onDelete,
}) => {
  // Loading state
  if (isLoading) {
    return (
      <Box>
        {Array.from({ length: 5 }).map((_, i) => (
          <Box
            key={i}
            sx={{
              p: 2,
              borderBottom: 2,
              borderColor: "divider",
              bgcolor: "background.paper",
            }}
          >
            <Box
              sx={{ display: "flex", justifyContent: "space-between", mb: 2 }}
            >
              <Box sx={{ display: "flex", gap: 1 }}>
                <Skeleton
                  variant="rectangular"
                  width={40}
                  height={24}
                  sx={{ borderRadius: 1 }}
                />
                <Skeleton
                  variant="rectangular"
                  width={80}
                  height={24}
                  sx={{ borderRadius: 1 }}
                />
                <Skeleton
                  variant="rectangular"
                  width={80}
                  height={24}
                  sx={{ borderRadius: 1 }}
                />
              </Box>
              <Skeleton variant="text" width={120} />
            </Box>
            <Skeleton
              variant="rectangular"
              height={80}
              sx={{ mb: 2, borderRadius: 1 }}
            />
            <Skeleton
              variant="rectangular"
              height={80}
              sx={{ borderRadius: 1 }}
            />
          </Box>
        ))}
      </Box>
    );
  }

  // Empty state
  if (tasks.length === 0) {
    return (
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
          width: "100%",
          p: 4,
        }}
      >
        <Assignment sx={{ fontSize: 40, color: "text.disabled" }} />
        <Typography variant="body2" color="text.disabled">
          Generate sample tasks to get started
        </Typography>
      </Box>
    );
  }

  // Loaded tasks
  return (
    <Box>
      {tasks.map((task) => (
        <Box
          key={task.id}
          sx={{
            p: 2,
            borderBottom: 2,
            borderColor: "divider",
            bgcolor: "background.paper",
            transition: "background-color 0.2s ease",
            "&:hover": {
              bgcolor: "action.hover",
            },
            "&:hover .row-actions": {
              opacity: 1,
            },
          }}
        >
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              mb: 1.5,
            }}
          >
            <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ fontWeight: 600 }}
              >
                #{task.id}
              </Typography>
              <StatusChip status={task.priority} />
              <StatusChip status={task.status} secondary={task.status === "completed"} />
            </Box>

            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <Box
                className="row-actions"
                sx={{ display: "flex", gap: 0.5, opacity: 0, transition: "opacity 0.15s ease" }}
              >
                <Tooltip title="Mark as complete">
                  <span>
                    <IconButton
                      size="small"
                      onClick={() => onMarkComplete(task.id)}
                      disabled={task.status === "completed"}
                      color="success"
                    >
                      <TaskAlt fontSize="small" />
                    </IconButton>
                  </span>
                </Tooltip>
                <Tooltip title="Delete">
                  <IconButton
                    size="small"
                    onClick={() => onDelete(task.id)}
                    color="error"
                  >
                    <DeleteOutline fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>

              <Typography variant="caption" color="text.secondary">
                {new Date(task.created_at).toLocaleString("en-GB", {
                  day: "2-digit",
                  month: "short",
                  year: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                  hour12: true,
                })}
              </Typography>
            </Box>
          </Box>

          {/* Description */}
          <Box
            sx={{
              bgcolor: "action.hover",
              p: 1.5,
              borderRadius: 1,
              borderLeft: 3,
              borderColor: "primary.main",
              mb: 1.5,
            }}
          >
            <Typography
              variant="caption"
              color="primary"
              sx={{
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: 0.5,
                display: "block",
                mb: 1,
              }}
            >
              Description
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: "pre-wrap"}}>
              {task.task_description}
            </Typography>
          </Box>

          {/* Reasoning */}
          <Box
            sx={{
              bgcolor: "action.hover",
              p: 1.5,
              borderRadius: 1,
              borderLeft: 3,
              borderColor: "primary.main",
            }}
          >
            <Typography
              variant="caption"
              color="primary"
              sx={{
                fontWeight: 600,
                textTransform: "uppercase",
                letterSpacing: 0.5,
                display: "block",
                mb: 1,
              }}
            >
              Reasoning
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: "pre-wrap"}}>
              {task.reasoning}
            </Typography>
          </Box>
        </Box>
      ))}
    </Box>
  );
};

export default CurriculumList;