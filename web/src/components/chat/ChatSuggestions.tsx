import React from "react";
import { Stack, Box, Typography, IconButton } from "@mui/material";
import { AutoAwesome, Close } from "@mui/icons-material";
import type { Suggestion } from "./engine/chatEngine";

const MAX_SUGGESTIONS = 2;

interface ChatSuggestionsProps {
  suggestions: Suggestion[];
  onSuggestionClick: (value: string) => void;
  onDismiss: () => void;
}

export const ChatSuggestions: React.FC<ChatSuggestionsProps> = ({
  suggestions,
  onSuggestionClick,
  onDismiss,
}) => {
  return (
    <Stack
      spacing={0.5}
      sx={{
        p: 1.5,
        pt: 1,
        pb: 1,
        bgcolor: "background.default",
        borderTop: 1,
        borderColor: "divider",
        minWidth: 0,
        overflow: "hidden",
        "@keyframes suggestionsIn": {
          from: { opacity: 0, transform: "translateY(6px)" },
          to: { opacity: 1, transform: "translateY(0)" },
        },
        animation: "suggestionsIn 180ms ease-out",
      }}
    >
      <Stack direction="row" spacing={0.5} alignItems="center" sx={{ px: 0.5 }}>
        <AutoAwesome sx={{ fontSize: 12, color: "primary.main" }} />
        <Typography
          variant="caption"
          sx={{ color: "text.secondary", fontWeight: 500, fontSize: "0.75rem", flex: 1 }}
        >
          Suggestions
        </Typography>
        <IconButton size="small" onClick={onDismiss} sx={{ p: 0 }}>
          <Close sx={{ fontSize: 16, color: "text.secondary" }} />
        </IconButton>
      </Stack>
      <Stack spacing={0.5}>
        {suggestions.slice(0, MAX_SUGGESTIONS).map((suggestion, index) => (
          <Box
            key={index}
            onClick={() => onSuggestionClick(suggestion.value)}
            sx={{
              px: 1.5,
              py: 0.75,
              bgcolor: "background.paper",
              border: 1,
              borderColor: "divider",
              borderRadius: 2,
              cursor: "pointer",
              transition: "all 140ms ease",
              "&:hover": {
                bgcolor: "action.hover",
                borderColor: "primary.main",
                boxShadow: 1,
                transform: "translateY(-1px)",
              },
            }}
          >
            <Typography
              variant="body2"
              sx={{
                color: "text.primary",
                fontSize: "0.75rem",
                lineHeight: 1.5,
              }}
            >
              {suggestion.label}
            </Typography>
          </Box>
        ))}
      </Stack>
    </Stack>
  );
};