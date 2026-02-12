import React from "react";
import { Stack, Box, Typography } from "@mui/material";
import { AutoAwesome } from "@mui/icons-material";
import type { Suggestion } from "./engine/chatEngine";

interface ChatSuggestionsProps {
  suggestions: Suggestion[];
  onSuggestionClick: (value: string) => void;
}
const MAX_SUGGESTIONS = 2;

export const ChatSuggestions: React.FC<ChatSuggestionsProps> = ({
  suggestions,
  onSuggestionClick,
}) => {
  return (
    <Stack
      spacing={1}
      sx={{
        p: 1.5,
        pb: 1,
        bgcolor: "background.default",
        borderTop: 1,
        borderColor: "divider",
      }}
    >
      <Stack direction="row" spacing={0.5} alignItems="center" sx={{ px: 0.5 }}>
        <AutoAwesome sx={{ fontSize: 12, color: "primary.main" }} />
        <Typography
          variant="caption"
          sx={{ color: "text.secondary", fontWeight: 500, fontSize: "0.7rem" }}
        >
          Suggestions
        </Typography>
      </Stack>
      <Stack
        direction="row"
        spacing={0.75}
        sx={{
          flexWrap: "wrap",
          gap: 0.75,
        }}
      >
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
              "&:hover": {
                bgcolor: "action.hover",
                borderColor: "primary.main",
                boxShadow: 1,
              },
            }}
          >
            <Typography
              variant="body2"
              sx={{
                color: "text.primary",
                fontWeight: 500,
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
