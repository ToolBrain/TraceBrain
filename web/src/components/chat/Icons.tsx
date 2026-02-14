import React from "react";
import { Avatar } from "@mui/material";
import { School, Person } from "@mui/icons-material";

export const AssistantAvatar: React.FC = () => (
  <Avatar
    sx={{
      bgcolor: "primary.light",
      width: 32,
      height: 32,
    }}
  >
    <School sx={{ fontSize: 20 }} />
  </Avatar>
);

export const UserAvatar: React.FC = () => (
  <Avatar
    sx={{
      bgcolor: "primary.light",
      width: 32,
      height: 32,
    }}
  >
    <Person sx={{ fontSize: 20 }} />
  </Avatar>
);
