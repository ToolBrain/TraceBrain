import React from "react";
import { Avatar, Box } from "@mui/material";
import { Person } from "@mui/icons-material";
import { useSettings } from "../../contexts/SettingsContext";
import chatLight from "../../assets/chat-light.png";
import chatDark from "../../assets/chat-dark.png";

interface AvatarProps {
  size?: number;
}

export const LibrarianLogoAvatar: React.FC<AvatarProps> = ({ size = 36 }) => {
  const { settings } = useSettings();
  const isDark = settings.appearance.theme === "dark";
  const logoSrc = isDark ? chatDark : chatLight;

  return (
    <Avatar
      sx={{
        width: size,
        height: size,
        bgcolor: "white",
        border: "1px solid",
        borderColor: isDark ? "rgba(255,255,255,0.55)" : "divider",
        boxShadow: isDark
          ? "0 8px 16px rgba(0,0,0,0.45), 0 0 0 2px rgba(255,255,255,0.08)"
          : "0 4px 10px rgba(15, 23, 42, 0.12)",
      }}
    >
      <Box
        component="img"
        src={logoSrc}
        alt="TraceBrain Librarian"
        sx={{ width: "90%", height: "90%", objectFit: "cover", display: "block" }}
      />
    </Avatar>
  );
};

export const AssistantAvatar: React.FC<AvatarProps> = ({ size = 32 }) => (
  <LibrarianLogoAvatar size={size} />
);

export const UserAvatar: React.FC<AvatarProps> = ({ size = 32 }) => (
  <Avatar
    sx={{
      bgcolor: "primary.main",
      color: "primary.contrastText",
      width: size,
      height: size,
      border: "1px solid",
      borderColor: "primary.light",
    }}
  >
    <Person sx={{ fontSize: Math.max(20, size * 0.5) }} />
  </Avatar>
);
