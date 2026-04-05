import React from "react";
import { Avatar, Box } from "@mui/material";
import { Person } from "@mui/icons-material";
import chatLight from "../../assets/chat-light-bg.png";
import chatDark from "../../assets/chat-dark-bg.png";
import { useSettings } from "../../contexts/SettingsContext";

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
        background: "linear-gradient(145deg, rgba(255,255,255,0.95), rgba(255,255,255,0.75))",
        border: "1px solid",
        borderColor: "divider",
      }}
    >
      <Box
        component="img"
        src={logoSrc}
        alt="TraceBrain Librarian"
        sx={{ width: "80%", height: "80%", display: "block" }}
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
    <Person sx={{ fontSize: Math.max(16, size * 0.58) }} />
  </Avatar>
);
