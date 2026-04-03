import React, { useEffect, useRef } from "react";
import { Stack, Box, Typography, Chip, Skeleton, keyframes } from "@mui/material";
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

const QUICK_STARTERS: Array<{ group: string; items: Array<{ title: string; content: string }> }> = [
  {
    group: "Debug",
    items: [
      { title: "Failed traces today", content: "Show me traces that failed today" },
      { title: "Logic loops", content: "Find me traces with logic loops" },
    ],
  },
  {
    group: "Analytics",
    items: [
      { title: "Average AI confidence", content: "What is the average AI confidence?" },
      { title: "Top error types", content: "What are the top error types?" },
    ],
  },
  {
    group: "Discovery",
    items: [{ title: "Recent successes", content: "Summarize recent traces with no errors" }],
  },
];

const bounce = keyframes`
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-5px); }
`;

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
          <AssistantAvatar size={64} />

          <Stack spacing={0.75} sx={{ maxWidth: 330 }}>
            <Typography variant="h6" sx={{ color: "text.primary", fontWeight: 600 }}>
              Hello! How can I help you today?
            </Typography>
            <Typography variant="body2">
              Ask me anything about your agent traces errors, performance, patterns, or summaries.
            </Typography>
          </Stack>

          <Stack spacing={1.25} sx={{ width: "100%", maxWidth: 360, mt: 0.5 }}>
            {QUICK_STARTERS.map((group) => (
              <Stack key={group.group} spacing={0.75} alignItems="flex-start">
                <Typography variant="caption" sx={{ fontWeight: 700, color: "text.secondary" }}>
                  {group.group}
                </Typography>
                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.75 }}>
                  {group.items.map((item) => (
                    <Chip
                      key={item.title}
                      label={item.title}
                      variant="outlined"
                      size="small"
                      onClick={() => onQuickStarterClick(item.content)}
                      sx={{
                        borderRadius: 3,
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
                  Status: Connected to {systemInfo?.database_type ?? "Unknown"} |{" "}
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
            }}
          >
            {[0, 0.16, 0.32].map((delay) => (
              <Box
                key={delay}
                sx={{
                  width: 7,
                  height: 7,
                  borderRadius: "50%",
                  bgcolor: "primary.main",
                  animation: `${bounce} 1s infinite ease-in-out`,
                  animationDelay: `${delay}s`,
                }}
              />
            ))}
          </Box>
          <Typography variant="body2" sx={{ color: "text.secondary", fontStyle: "italic" }}>
            Librarian is thinking…
          </Typography>
        </Box>
      )}

      <div ref={messagesEndRef} />
    </Stack>
  );
};
