import React from "react";
import { Box, Typography, LinearProgress } from "@mui/material";
import { StarBorder, Star } from "@mui/icons-material";
import StatusChip, { type ChipStatus } from "../dashboard/StatusChip";

interface AIEvaluationProps {
  evaluation: {
    rating: number;
    confidence: number;
    status: string;
    feedback: string;
  };
}

const AIEvaluation: React.FC<AIEvaluationProps> = ({ evaluation }) => {
  return (
    <Box sx={{ mb: 3 }}>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          mb: 1.5,
        }}
      >
        <Typography
          variant="subtitle2"
          sx={{
            fontWeight: 600,
            color: "text.primary",
          }}
        >
          AI Evaluation
        </Typography>
        <StatusChip status={evaluation.status as ChipStatus} />
      </Box>

      <Box
        sx={{
          p: 2.5,
          borderRadius: 1.5,
          border: 1,
          borderColor: "divider",
          bgcolor: "background.paper",
        }}
      >
        <Box sx={{ display: "flex", gap: 3, mb: 2.5 }}>
          {/* Rating */}
          <Box sx={{ flex: 1 }}>
            <Typography
              variant="caption"
              sx={{
                color: "text.secondary",
                fontWeight: 500,
                textTransform: "uppercase",
                letterSpacing: 0.5,
                display: "block",
                mb: 0.75,
              }}
            >
              Rating
            </Typography>
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              {[1, 2, 3, 4, 5].map((star) => (
                <Box key={star} sx={{ color: "warning.main" }}>
                  {star <= evaluation.rating ? (
                    <Star sx={{ fontSize: "1.25rem" }} />
                  ) : (
                    <StarBorder sx={{ fontSize: "1.25rem" }} />
                  )}
                </Box>
              ))}
              <Typography
                variant="body2"
                sx={{ ml: 0.5, fontWeight: 600, color: "text.primary" }}
              >
                {evaluation.rating}/5
              </Typography>
            </Box>
          </Box>

          {/* Confidence */}
          <Box sx={{ flex: 1 }}>
            <Typography
              variant="caption"
              sx={{
                color: "text.secondary",
                fontWeight: 500,
                textTransform: "uppercase",
                letterSpacing: 0.5,
                display: "block",
                mb: 0.75,
              }}
            >
              Confidence
            </Typography>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <LinearProgress
                variant="determinate"
                value={evaluation.confidence * 100}
                sx={{
                  flex: 1,
                  height: 6,
                  borderRadius: 3,
                  bgcolor: "action.hover",
                  "& .MuiLinearProgress-bar": {
                    borderRadius: 3,
                    bgcolor:
                      evaluation.confidence >= 0.8
                        ? "success.main"
                        : evaluation.confidence >= 0.5
                          ? "warning.main"
                          : "error.main",
                  },
                }}
              />
              <Typography
                variant="body2"
                sx={{ fontWeight: 600, minWidth: "3rem", textAlign: "right" }}
              >
                {(evaluation.confidence * 100).toFixed(0)}%
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Feedback */}
        <Box>
          <Typography
            variant="caption"
            sx={{
              color: "text.secondary",
              fontWeight: 500,
              textTransform: "uppercase",
              letterSpacing: 0.5,
              display: "block",
              mb: 1,
            }}
          >
            Feedback
          </Typography>
          <Typography
            variant="body2"
            sx={{
              color: "text.primary",
              lineHeight: 1.6,
              p: 1.5,
              bgcolor: "action.hover",
              borderRadius: 1,
            }}
          >
            {evaluation.feedback}
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default AIEvaluation;
