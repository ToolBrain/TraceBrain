import React, { useEffect, useRef } from "react";
import { Stack, Box, CircularProgress, Typography } from "@mui/material";
import { ChatMessage } from "./ChatMessage";
import type { Message } from "./engine/chatEngine";

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
        <ChatMessage key={index} message={message} />
      ))}

      {isLoading && (
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1.5,
            ml: 5,
            py: 0.5,
          }}
        >
          <CircularProgress size={24} thickness={4} />
          <Typography
            variant="body2"
            sx={{ color: "text.secondary", fontStyle: "italic" }}
          >
            Generating response…
          </Typography>
        </Box>
      )}

      <div ref={messagesEndRef} />
    </Stack>
  );
};
