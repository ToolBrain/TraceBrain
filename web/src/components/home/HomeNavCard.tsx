import React from "react";
import { Box, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { type SvgIconComponent } from "@mui/icons-material";

interface HomeNavCardProps {
  title: string;
  description: string;
  route: string;
  Icon: SvgIconComponent;
}

const HomeNavCard: React.FC<HomeNavCardProps> = ({
  title,
  description,
  route,
  Icon,
}) => {
  const navigate = useNavigate();

  return (
    <Box
      onClick={() => navigate(route)}
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: 2.5,
        p: 5,
        borderRadius: 2,
        cursor: "pointer",
        border: "1px solid",
        borderColor: "divider",
        backgroundColor: "background.paper",
        "&:hover": {
          borderColor: "primary.main",
          backgroundColor: "action.hover",
        },
        userSelect: "none",
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          width: 64,
          height: 64,
          borderRadius: 2,
          backgroundColor: "action.hover",
          color: "primary.main",
        }}
      >
        <Icon sx={{ fontSize: 32 }} />
      </Box>

      <Typography variant="h6" sx={{ fontWeight: 600 }}>
        {title}
      </Typography>

      <Typography
        variant="body1"
        color="text.secondary"
        sx={{ lineHeight: 1.5 }}
      >
        {description}
      </Typography>
    </Box>
  );
};

export default HomeNavCard;
