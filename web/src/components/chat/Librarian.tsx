import React, { useEffect, useState } from "react";
import {
  Paper,
  Stack,
  Typography,
  TextField,
  IconButton,
  Fab,
  Divider,
} from "@mui/material";
import { Send, ChatBubble, Remove, DeleteOutline } from "@mui/icons-material";
import { useChat } from "../../contexts/ChatContext";
import { ChatMessages } from "./ChatMessages";
import { ChatSuggestions } from "./ChatSuggestions";
import { AssistantAvatar } from "./Icons";

export const Librarian: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const { messages, suggestions, isLoading, sendMessage, clearMessages } =
    useChat();
  const [selectedSuggestion, setSelectedSuggestion] = useState(false);

  // Sends the message if input is not empty and clears the input
  const handleSend = async () => {
    if (!input.trim()) return;

    await sendMessage(input);
    setInput("");
  };

  // Sends message on when enter is press and allows newline with Shift+Enter
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (value: string) => {
    setInput(value);
    setSelectedSuggestion(true);
  };

  // Handle clear session
  const handleClearSession = () => {
    clearMessages();
    setInput("");
    setSelectedSuggestion(false);
  };

  // Reset state
  useEffect(() => {
    if (suggestions.length > 0) {
      setSelectedSuggestion(false);
    }
  }, [suggestions]);

  return (
    <>
      {isOpen && (
        <Paper
          elevation={8}
          sx={{
            position: "fixed",
            bottom: 24,
            right: 24,
            width: 400,
            height: 600,
            display: "flex",
            flexDirection: "column",
            borderRadius: 2,
            overflow: "hidden",
            zIndex: 1200,
          }}
        >
          <Stack
            direction="row"
            alignItems="center"
            spacing={2}
            sx={{
              p: 2,
              bgcolor: "primary.main",
              color: "primary.contrastText",
            }}
          >
            <AssistantAvatar />
            <Stack flex={1}>
              <Typography
                variant="h6"
                sx={{ fontWeight: 600, userSelect: "none" }}
              >
                TraceBrain Librarian
              </Typography>
            </Stack>

            <IconButton
              size="small"
              onClick={handleClearSession}
              sx={{ color: "inherit" }}
            >
              <DeleteOutline />
            </IconButton>

            <IconButton
              size="small"
              onClick={() => setIsOpen(false)}
              sx={{ color: "inherit" }}
              title="Minimize"
            >
              <Remove />
            </IconButton>
          </Stack>

          <ChatMessages messages={messages} isLoading={isLoading} />

          {!selectedSuggestion && suggestions.length > 0 && (
            <ChatSuggestions
              suggestions={suggestions}
              onSuggestionClick={handleSuggestionClick}
            />
          )}

          <Divider />

          <Stack
            direction="row"
            spacing={1}
            sx={{
              p: 2,
              bgcolor: "background.paper",
            }}
          >
            <TextField
              fullWidth
              placeholder="Type your message..."
              variant="outlined"
              size="small"
              multiline
              maxRows={3}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              disabled={isLoading}
              sx={{
                "& .MuiOutlinedInput-root": {
                  borderRadius: 2,
                },
              }}
            />
            <IconButton
              color="primary"
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              sx={{
                alignSelf: "flex-end",
              }}
            >
              <Send />
            </IconButton>
          </Stack>
        </Paper>
      )}

      {!isOpen && (
        <Fab
          color="primary"
          aria-label="chat"
          onClick={() => setIsOpen(true)}
          sx={{
            position: "fixed",
            bottom: 24,
            right: 24,
            zIndex: 1200,
          }}
        >
          <ChatBubble />
        </Fab>
      )}
    </>
  );
};
