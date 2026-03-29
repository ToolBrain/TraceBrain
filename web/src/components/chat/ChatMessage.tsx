import React from "react";
import { Box, Paper, Typography } from "@mui/material";
import type { Message } from "./engine/chatEngine";
import TraceSources from "./TraceSources";
import TraceFilters from "./TraceFilters";
import { AssistantAvatar, UserAvatar } from "./Icons";

interface ChatMessageProps {
  message: Message;
  index: number;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, index }) => {
  const isUser = message.role === "user";
  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        alignItems: "flex-end",
        gap: 1,
        mb: 1.2,
        "@keyframes chatMessageIn": {
          from: {
            opacity: 0,
            transform: "translateY(10px)",
          },
          to: {
            opacity: 1,
            transform: "translateY(0)",
          },
        },
        animation: "chatMessageIn 220ms ease-out",
        animationDelay: `${Math.min(index * 45, 300)}ms`,
        animationFillMode: "both",
      }}
    >
      {!isUser && <AssistantAvatar size={30} />}

      <Paper
        elevation={1}
        sx={{
          position: "relative",
          maxWidth: "80%",
          px: 1.75,
          py: 1.2,
          background: isUser
            ? "linear-gradient(140deg, #2e86de 0%, #1f6fbe 100%)"
            : undefined,
          backgroundColor: isUser ? undefined : "background.paper",
          color: isUser ? "primary.contrastText" : "text.primary",
          borderRadius: 3,
          border: "1px solid",
          borderColor: isUser ? "rgba(255,255,255,0.18)" : "divider",
          fontSize: "0.875rem",
          boxShadow: isUser
            ? "0 8px 18px rgba(31, 111, 190, 0.28)"
            : "0 4px 12px rgba(16, 24, 40, 0.08)",
          "&::after": isUser
            ? {
                content: '""',
                position: "absolute",
                right: -6,
                bottom: 12,
                borderTop: "6px solid transparent",
                borderBottom: "6px solid transparent",
                borderLeft: "8px solid #1f6fbe",
              }
            : {
                content: '""',
                position: "absolute",
                left: -6,
                bottom: 12,
                borderTop: "6px solid transparent",
                borderBottom: "6px solid transparent",
                borderRight: "8px solid",
                borderRightColor: "background.paper",
              },
        }}
      >
        <Typography
          variant="body2"
          sx={{
            fontSize: "0.95rem",
            lineHeight: 1.55,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {message.content.answer}
        </Typography>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 1 }}>
          {!isUser && message.content.sources && message.content.sources.length > 0 && (
            <TraceSources sources={message.content.sources} />
          )}
          {!isUser &&
            message.content.filters &&
            Object.keys(message.content.filters).length > 0 && (
              <Box sx={{ ml: "auto" }}>
                <TraceFilters filters={message.content.filters} />
              </Box>
            )}
        </Box>
      </Paper>

      {isUser && <UserAvatar size={30} />}
    </Box>
  );
};
