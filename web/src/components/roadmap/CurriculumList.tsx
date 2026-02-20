import React from "react";
import { Box, Typography, Skeleton } from "@mui/material";
import StatusChip from "../shared/StatusChip";
import type { CurriculumTask } from "./types";

interface CurriculumListProps {
  tasks: CurriculumTask[];
  isLoading?: boolean;
}

const CurriculumList: React.FC<CurriculumListProps> = ({
  tasks,
  isLoading = false,
}) => {
  // Loading state
  if (isLoading) {
    return (
      <Box>
        {Array.from({ length: 5 }).map((_, i) => (
          <Box
            key={i}
            sx={{
              p: 3,
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
        <Typography variant="h6" color="text.secondary">
          No tasks yet
        </Typography>
        <Typography variant="body2" color="text.secondary">
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
            p: 3,
            borderBottom: 2,
            borderColor: "divider",
            bgcolor: "background.paper",
            transition: "background-color 0.2s ease",
            "&:hover": {
              bgcolor: "action.hover",
            },
          }}
        >
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              mb: 2,
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
              <StatusChip status={task.status} secondary />
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

          {/* Description */}
          <Box
            sx={{
              bgcolor: "action.hover",
              p: 2,
              borderRadius: 1,
              borderLeft: 3,
              borderColor: "primary.main",
              mb: 2,
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
            <Typography variant="body2" color="text.secondary">
              {task.task_description}
            </Typography>
          </Box>

          {/* Reasoning */}
          <Box
            sx={{
              bgcolor: "action.hover",
              p: 2,
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
            <Typography variant="body2" color="text.secondary">
              {task.reasoning}
            </Typography>
          </Box>
        </Box>
      ))}
    </Box>
  );
};

export default CurriculumList;
