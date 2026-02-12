import React from "react";
import { Box, Typography } from "@mui/material";

const HomeTitle: React.FC = () => {
  return (
    <Box sx={{ textAlign: "center", position: "relative", userSelect: "none" }}>
      <Typography
        sx={{
          fontFamily: "sans-serif",
          fontSize: { xs: "3.5rem", sm: "5rem", md: "6rem" },
          fontWeight: 400,
          letterSpacing: "0.25em",
          lineHeight: 1,
          background: (theme) =>
            theme.palette.mode === "dark"
              ? "linear-gradient(135deg, #ffffff 0%, #a0a0a0 50%, #ffffff 100%)"
              : "linear-gradient(135deg, #111111 0%, #555555 50%, #111111 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
        }}
      >
        TRACEBRAIN
      </Typography>

      <Box
        sx={{
          mt: 1.5,
          mx: "auto",
          width: "100%",
          height: "2px",
          background: (theme) =>
            theme.palette.mode === "dark"
              ? "linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)"
              : "linear-gradient(90deg, transparent, rgba(0,0,0,0.2), transparent)",
        }}
      />
    </Box>
  );
};

export default HomeTitle;
