import React, { useEffect, useRef } from "react";
import { Stack, Box, Typography, Chip, Skeleton } from "@mui/material";
import { ChatMessage } from "./ChatMessage";
import type { Message } from "./engine/chatEngine";
import { AssistantAvatar } from "./Icons";

interface SystemInfo {
  database_type: string;
  trace_count: number;
  model_name: string;
}

interface ChatMessagesProps {
  messages: Message[];
  isLoading: boolean;
  systemInfo: SystemInfo | null;
  isSystemInfoLoading: boolean;
  onQuickStarterClick: (query: string) => void;
}

const QUICK_STARTERS: Array<{ group: string; items: string[] }> = [
  {
    group: "Debug",
    items: ["Show me traces that failed today", "Find logic loops"],
  },
  {
    group: "Analytics",
    items: ["Average AI confidence", "Top error types"],
  },
  {
    group: "Discovery",
    items: ["Summarize recent successes"],
  },
];

export const ChatMessages: React.FC<ChatMessagesProps> = ({
  messages,
  isLoading,
  systemInfo,
  isSystemInfoLoading,
  onQuickStarterClick,
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
        <Stack
          spacing={2}
          sx={{
            alignItems: "center",
            justifyContent: "center",
            height: "100%",
            textAlign: "center",
            color: "text.secondary",
            px: 1,
          }}
        >
          <AssistantAvatar size={67} />

          <Stack spacing={0.75} sx={{ maxWidth: 330 }}>
            <Typography variant="h6" sx={{ color: "text.primary", fontWeight: 600 }}>
              Hello! How can I help you today?
            </Typography>
            <Typography variant="body2">
              Ask me to query, summarize, or analyze your agent&apos;s traces using natural language.
            </Typography>
          </Stack>

          <Stack spacing={1.25} sx={{ width: "100%", maxWidth: 360, mt: 0.5 }}>
            {QUICK_STARTERS.map((group) => (
              <Stack key={group.group} spacing={0.75} alignItems="flex-start">
                <Typography variant="caption" sx={{ fontWeight: 700, color: "text.secondary" }}>
                  {group.group}
                </Typography>
                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.75 }}>
                  {group.items.map((query) => (
                    <Chip
                      key={query}
                      label={query}
                      variant="outlined"
                      size="small"
                      onClick={() => onQuickStarterClick(query)}
                      sx={{
                        borderRadius: 2,
                        fontWeight: 500,
                        bgcolor: "background.paper",
                        "&:hover": {
                          borderColor: "primary.main",
                          color: "primary.main",
                          bgcolor: "action.hover",
                        },
                      }}
                    />
                  ))}
                </Box>
              </Stack>
            ))}
          </Stack>

          <Box
            sx={{
              width: "100%",
              maxWidth: 360,
              mt: 1,
              px: 1.25,
              py: 1,
              borderRadius: 2,
              border: "1px solid",
              borderColor: "divider",
              bgcolor: "background.paper",
            }}
          >
            {isSystemInfoLoading ? (
              <Stack spacing={0.5}>
                <Skeleton variant="text" width="92%" height={18} />
                <Skeleton variant="text" width="60%" height={16} />
              </Stack>
            ) : (
              <Stack spacing={0.25}>
                <Typography variant="caption" sx={{ color: "text.secondary" }}>
                  Status: Connected to {systemInfo?.database_type ?? "Unknown"} | {" "}
                  {(systemInfo?.trace_count ?? 0).toLocaleString()} traces indexed
                </Typography>
                <Typography variant="caption" sx={{ color: "text.secondary" }}>
                  Model: {systemInfo?.model_name || "Not configured"}
                </Typography>
              </Stack>
            )}
          </Box>
        </Stack>
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
