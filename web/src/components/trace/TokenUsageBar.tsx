import React, { useState } from "react";
import { Box, Typography } from "@mui/material";

interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

interface TokenUsageBarProps {
  usage: TokenUsage;
  hasError?: boolean;
}

const TokenUsageBar: React.FC<TokenUsageBarProps> = ({ usage, hasError }) => {
  const [active, setActive] = useState<string>("prompt");

  const borderColour = hasError ? "error.main" : "success.main";
  const barBg = hasError ? "rgba(220, 38, 38, 0.5)" : "rgba(34, 197, 94, 0.5)";
  const chipBg = hasError
    ? "rgba(220, 38, 38, 0.15)"
    : "rgba(34, 197, 94, 0.15)";

  const stats = [
    {
      key: "prompt",
      label: "Prompt",
      value: usage.prompt_tokens,
      pct: (usage.prompt_tokens / usage.total_tokens) * 100,
    },
    {
      key: "completion",
      label: "Completion",
      value: usage.completion_tokens,
      pct: (usage.completion_tokens / usage.total_tokens) * 100,
    },
  ];

  return (
    <Box sx={{ mb: 3 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
        <Typography
          variant="overline"
          sx={{ fontWeight: 700, letterSpacing: 1, color: "text.secondary" }}
        >
          Token Usage
        </Typography>
        <Typography
          variant="caption"
          sx={{
            fontFamily: "monospace",
            color: "text.secondary",
            fontWeight: 600,
          }}
        >
          {usage.total_tokens.toLocaleString()} total
        </Typography>
      </Box>

      <Box
        sx={{
          width: "100%",
          height: 6,
          borderRadius: 3,
          bgcolor: "divider",
          display: "flex",
          overflow: "hidden",
          mb: 1.5,
        }}
      >
        {stats.map(({ key, pct }) => (
          <Box
            key={key}
            sx={{
              width: `${pct}%`,
              bgcolor: barBg,
              opacity: active !== key ? 0.25 : 1,
              transition: "opacity 0.2s ease",
            }}
          />
        ))}
      </Box>

      <Box sx={{ display: "flex", gap: 1 }}>
        {stats.map(({ key, label, value }) => (
          <Box
            key={key}
            onClick={() => setActive(key)}
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 0.75,
              px: 1.5,
              py: 0.5,
              borderRadius: 1.5,
              bgcolor: chipBg,
              border: 1,
              borderColor: active === key ? borderColour : "transparent",
              opacity: active !== key ? 0.5 : 1,
              cursor: "pointer",
              userSelect: "none",
              transition: "opacity 0.2s ease, border-color 0.2s ease",
              "&:hover": { borderColor: borderColour },
            }}
          >
            <Box
              sx={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                bgcolor: chipBg,
                border: "1 px solid",
                borderColor: borderColour,
              }}
            />
            <Typography
              variant="caption"
              sx={{ color: "text.secondary", fontWeight: 500 }}
            >
              {label}
            </Typography>
            <Typography
              variant="caption"
              sx={{
                color: "text.primary",
                fontFamily: "monospace",
                fontWeight: 700,
              }}
            >
              {value.toLocaleString()}
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
};

export default TokenUsageBar;
