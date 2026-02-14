import React from "react";
import { Box, Typography } from "@mui/material";

interface SpanContentProps {
  title: string;
  subtitle?: string | null;
  content: string;
  hasError?: boolean;
}

const SpanContent: React.FC<SpanContentProps> = ({
  title,
  subtitle,
  content,
  hasError,
}) => {
  const errorColour = "rgba(220, 38, 38, 0.08)";
  const successColour = "rgba(34, 197, 94, 0.08)";
  return (
    <Box sx={{ mb: 3 }}>
      <Typography
        variant="overline"
        sx={{
          fontWeight: 700,
          letterSpacing: 1,
          color: "text.secondary",
          display: "block",
          mb: 1,
        }}
      >
        {title}
      </Typography>
      <Box
        sx={{
          px: 2.5,
          py: 2,
          borderRadius: 2,
          bgcolor: hasError ? errorColour : successColour,
          border: 1,
          borderColor: hasError ? "error.main" : "success.main",
        }}
      >
        {subtitle && (
          <>
            <Typography
              variant="subtitle2"
              sx={{
                fontWeight: 600,
                mb: 1,
                color: "text.primary",
                textTransform: "uppercase",
              }}
            >
              {subtitle}
            </Typography>
            <Box
              sx={{ width: "100%", height: "1px", bgcolor: "divider", mb: 1.5 }}
            />
          </>
        )}
        <Typography
          variant="body2"
          sx={{
            lineHeight: 1.75,
            color: "text.primary",
          }}
        >
          {content}
        </Typography>
      </Box>
    </Box>
  );
};

export default SpanContent;
