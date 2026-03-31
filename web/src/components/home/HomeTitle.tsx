import React from "react";
import { Box, Typography } from "@mui/material";
import { useSettings } from "../../contexts/SettingsContext";
import lightOwl from "../../assets/light-owl.png";
import darkOwl from "../../assets/dark-owl.png";

const HomeTitle: React.FC = () => {
  const { settings } = useSettings();
  const isDark = settings.appearance.theme === "dark";
  const mascotSrc = isDark ? darkOwl : lightOwl;

  return (
    <Box sx={{ textAlign: "center", position: "relative", userSelect: "none", width: "100%" }}>
      <Box
        sx={{
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          gap: { xs: 1.5, sm: 2.5, md: 3 },
        }}
      >
        <Box
          component="img"
          src={mascotSrc}
          alt="TraceBrain mascot"
          sx={{
            width: { xs: 56, sm: 72, md: 84 },
            height: "auto",
          }}
        />

        <Typography
          sx={{
            fontFamily: "sans-serif",
            fontSize: { xs: "2.5rem", sm: "4.5rem", md: "6rem" },
            fontWeight: 400,
            letterSpacing: { xs: "0.12em", sm: "0.2em", md: "0.25em" },
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
      </Box>


      <Box
        sx={{
          mt: { xs: 1, sm: 1.5 },
          mx: "auto",
          width: "min(720px, 90%)",
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
