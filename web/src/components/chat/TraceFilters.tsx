import { OpenInNew } from "@mui/icons-material";
import { Link } from "@mui/material";
import React from "react";
import { useNavigate } from "react-router-dom";

interface TraceFiltersLinkProps {
  filters?: Record<string, any>;
}

const TraceFiltersLink: React.FC<TraceFiltersLinkProps> = ({ filters }) => {
  const navigate = useNavigate();

  const handleClick = () => {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          params.set(key, String(value));
        }
      });
    }
    navigate(`/explorer?type=traces&${params.toString()}`);
  };

  return (
    <Link
      onClick={handleClick}
      sx={{
        cursor: "pointer",
        fontSize: "0.625rem",
        textDecoration: "none",
        color: "text.secondary",
        display: "flex",
        alignItems: "center",
        gap: 0.5,
        "&:hover": { color: "text.primary" },
        transition: "color 0.2s ease",
      }}
    >
      View in Explorer
      <OpenInNew sx={{ fontSize: 10 }} />
    </Link>
  );
};

export default TraceFiltersLink;
