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
          from: { opacity: 0, transform: "translateY(10px)" },
          to: { opacity: 1, transform: "translateY(0)" },
        },
        animation: "chatMessageIn 220ms ease-out",
        animationDelay: `${Math.min(index * 45, 300)}ms`,
        animationFillMode: "both",
      }}
    >
      {!isUser && <AssistantAvatar size={30} />}

      <Paper
        elevation={0}
        sx={{
          position: "relative",
          maxWidth: "80%",
          px: 1.75,
          py: 1.2,
          backgroundColor: isUser ? "primary.main" : "background.paper",
          color: isUser ? "primary.contrastText" : "text.primary",
          borderRadius: 3,
          border: "1px solid",
          borderColor: "divider",
          fontSize: "0.875rem",
          boxShadow: "none",
          "&::after": isUser
            ? (theme) => ({
                content: '""',
                position: "absolute",
                right: -6,
                bottom: 12,
                borderTop: "6px solid transparent",
                borderBottom: "6px solid transparent",
                borderLeft: `8px solid ${theme.palette.primary.main}`,
              })
            : (theme) => ({
                content: '""',
                position: "absolute",
                bottom: 12,
                width: 7,
                height: 7,
                backgroundColor: theme.palette.background.paper,
                borderLeft: `1px solid ${theme.palette.divider}`,
                borderBottom: `1px solid ${theme.palette.divider}`,
                transform: "rotate(45deg)",
                left: -4,
                zIndex: 1,
              }),
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
