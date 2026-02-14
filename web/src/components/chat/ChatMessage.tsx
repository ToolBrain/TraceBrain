import React from "react";
import { Box, Chip, Paper, Stack, Typography } from "@mui/material";
import type { Message } from "./engine/chatEngine";
import { AssistantAvatar, UserAvatar } from "./Icons";
import { Source } from "@mui/icons-material";

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === "user";

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        gap: 1,
        mb: 2,
      }}
    >
      {!isUser && <AssistantAvatar />}

      <Paper
        elevation={1}
        sx={{
          maxWidth: "80%",
          px: 1.5,
          py: 1,
          bgcolor: isUser ? "primary.main" : "background.default",
          color: isUser ? "primary.contrastText" : "text.primary",
          borderRadius: 2,
          fontSize: "0.875rem",
        }}
      >
        <Typography
          variant="body2"
          sx={{
            fontSize: "0.875rem",
            lineHeight: 1.5,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {message.content}
        </Typography>
        {!isUser && message.sources && message.sources.length > 0 && (
          <Box sx={{ mt: 1 }}>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1,
                pb: 0.75,
                borderBottom: 1,
                borderColor: "divider",
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  fontSize: "0.75rem",
                  color: "text.secondary",
                  fontWeight: 600,
                  textTransform: "uppercase",
                  letterSpacing: 0.5,
                }}
              >
                Sources
              </Typography>
            </Box>
            <Stack
              direction="row"
              spacing={0.5}
              sx={{ mt: 0.75, flexWrap: "wrap", gap: 0.5 }}
            >
              {message.sources.map((source, index) => (
                <Chip
                  key={index}
                  icon={<Source sx={{ fontSize: 12 }} />}
                  label={source}
                  size="small"
                  variant="outlined"
                  sx={{
                    height: 24,
                    fontSize: "0.625rem",
                    borderColor: "divider",
                    bgcolor: "background.paper",
                    "& .MuiChip-icon": {
                      fontSize: 12,
                    },
                    p: 0.5,
                  }}
                />
              ))}
            </Stack>
          </Box>
        )}
      </Paper>

      {isUser && <UserAvatar />}
    </Box>
  );
};
