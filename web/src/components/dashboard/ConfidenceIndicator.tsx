import React from "react";
import { Box, LinearProgress, Typography } from "@mui/material";
import { CheckCircle, Schedule } from "@mui/icons-material";

interface ConfidenceIndicatorProps {
  confidence: number;
  status: "pending_review" | "completed";
}

const ConfidenceIndicator: React.FC<ConfidenceIndicatorProps> = ({
  confidence,
  status,
}) => {
  const percentage = confidence * 100;
  const progressColor =
    confidence < 0.2 ? "error" : confidence < 0.8 ? "warning" : "success";

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
      <Box sx={{ flexGrow: 1 }}>
        <LinearProgress
          variant="determinate"
          value={percentage}
          color={progressColor}
          sx={{
            height: 6,
            borderRadius: 2,
          }}
        />
      </Box>
      <Typography
        variant="body2"
        sx={{
          fontFamily: "monospace",
          fontSize: "0.75rem",
          color: "text.secondary",
        }}
      >
        {percentage.toFixed(0)}%
      </Typography>

      {status === "completed" ? (
        <CheckCircle sx={{ fontSize: 16, color: "success.main" }} />
      ) : (
        <Schedule sx={{ fontSize: 16, color: "warning.main" }} />
      )}
    </Box>
  );
};

export default ConfidenceIndicator;
