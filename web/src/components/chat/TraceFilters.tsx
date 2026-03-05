import { Box, Link } from "@mui/material";
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
    <Box sx={{ display: "flex", justifyContent: "flex-end", mt: 1 }}>
      <Link onClick={handleClick} sx={{ cursor: "pointer" }}>
        View in Explorer
      </Link>
    </Box>
  );
};

export default TraceFiltersLink;
