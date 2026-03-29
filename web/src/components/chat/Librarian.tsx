import React, { useEffect, useState } from "react";
import { Paper, Stack, Typography, TextField, IconButton, Fab, Divider } from "@mui/material";
import { Send, Remove, DeleteOutline, ChatBubble } from "@mui/icons-material";
import { useChat } from "../../contexts/ChatContext";
import { ChatMessages } from "./ChatMessages";
import { ChatSuggestions } from "./ChatSuggestions";
import { LibrarianLogoAvatar } from "./Icons";

export const Librarian: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const { messages, suggestions, isLoading, sendMessage, clearMessages, clearSuggestions } =
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
            bottom: { xs: 8, sm: 24 },
            right: { xs: 8, sm: 24 },
            width: { xs: "calc(100vw - 16px)", sm: 420 },
            height: { xs: "min(82vh, 680px)", sm: 640 },
            display: "flex",
            flexDirection: "column",
            borderRadius: 3,
            overflow: "hidden",
            zIndex: 1200,
            border: "1px solid",
            borderColor: "divider",
            boxShadow: "0 14px 36px rgba(15, 23, 42, 0.28)",
            "@keyframes chatOpenIn": {
              from: { opacity: 0, transform: "translateY(12px) scale(0.98)" },
              to: { opacity: 1, transform: "translateY(0) scale(1)" },
            },
            animation: "chatOpenIn 180ms ease-out",
          }}
        >
          <Stack
            direction="row"
            alignItems="center"
            spacing={2}
            sx={{
              p: 1.5,
              bgcolor: "primary.dark",
              backgroundImage:
                "linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0))",
              color: "primary.contrastText",
            }}
          >
            <LibrarianLogoAvatar />
            <Stack flex={1}>
              <Typography variant="h6" sx={{ fontWeight: 600, userSelect: "none" }}>
                TraceBrain Librarian
              </Typography>
            </Stack>

            <IconButton size="small" onClick={handleClearSession} sx={{ color: "inherit" }}>
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
              onDismiss={clearSuggestions}
            />
          )}

          <Divider />

          <Stack
            direction="row"
            spacing={1}
            sx={{
              p: 1.5,
              bgcolor: "background.paper",
            }}
          >
            <TextField
              fullWidth
              placeholder={isLoading ? "Waiting for Librarian..." : "Type your message..."}
              variant="outlined"
              multiline
              maxRows={3}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              disabled={isLoading}
              slotProps={{
                input: {
                  endAdornment: (
                    <IconButton
                      size="small"
                      color="primary"
                      onClick={handleSend}
                      disabled={isLoading || !input.trim()}
                      sx={{ alignSelf: "flex-end", mb: 0.5 }}
                    >
                      <Send fontSize="small" />
                    </IconButton>
                  ),
                },
              }}
              sx={{
                "& .MuiOutlinedInput-root": {
                  borderRadius: 2.5,
                },
              }}
            />
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
