import React, { useEffect, useRef } from "react";
import { Stack, Box, Typography } from "@mui/material";
import { ChatMessage } from "./ChatMessage";
import type { Message } from "./engine/chatEngine";
import { AssistantAvatar } from "./Icons";

interface ChatMessagesProps {
  messages: Message[];
  isLoading: boolean;
}

export const ChatMessages: React.FC<ChatMessagesProps> = ({
  messages,
  isLoading,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <Stack
      spacing={2}
      sx={{
        flex: 1,
        p: 2,
        overflowY: "auto",
        bgcolor: "background.default",
        backgroundImage: (theme) =>
          theme.palette.mode === "dark"
            ? "radial-gradient(circle at top right, rgba(46,134,222,0.08), transparent 45%)"
            : "radial-gradient(circle at top right, rgba(46,134,222,0.06), transparent 45%)",
      }}
    >
      {messages.length === 0 && !isLoading && (
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100%",
            textAlign: "center",
            color: "text.secondary",
          }}
        >
          <Typography variant="h6" gutterBottom>
            Welcome to TraceBrain Librarian
          </Typography>
          <Typography variant="body2">Type to get started</Typography>
        </Box>
      )}

      {messages.map((message, index) => (
        <ChatMessage key={`${message.role}-${index}`} message={message} index={index} />
      ))}

      {isLoading && (
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            py: 0.5,
            "@keyframes typingPulse": {
              "0%, 80%, 100%": { transform: "scale(0.72)", opacity: 0.35 },
              "40%": { transform: "scale(1)", opacity: 1 },
            },
          }}
        >
          <AssistantAvatar size={30} />
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 0.6,
              px: 1.4,
              py: 1,
              borderRadius: 3,
              border: "1px solid",
              borderColor: "divider",
              bgcolor: "background.paper",
              boxShadow: "0 4px 12px rgba(16,24,40,0.08)",
              "& span": {
                width: 7,
                height: 7,
                borderRadius: "50%",
                bgcolor: "primary.main",
                animation: "typingPulse 1.15s infinite ease-in-out",
              },
              "& span:nth-of-type(2)": { animationDelay: "0.16s" },
              "& span:nth-of-type(3)": { animationDelay: "0.32s" },
            }}
          >
            <span />
            <span />
            <span />
          </Box>
          <Typography
            variant="body2"
            sx={{ color: "text.secondary", fontStyle: "italic" }}
          >
            Librarian is thinking…
          </Typography>
        </Box>
      )}

      <div ref={messagesEndRef} />
    </Stack>
  );
};
