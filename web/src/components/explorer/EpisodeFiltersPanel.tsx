import React from "react";
import { Box, TextField, Typography, ButtonBase } from "@mui/material";
import FilterChip from "./FilterChip";
import type { EpisodeFilters } from "./types";

interface EpisodesFiltersPanelProps {
  filters: EpisodeFilters;
  onChange: (filters: EpisodeFilters) => void;
}

const EpisodesFiltersPanel: React.FC<EpisodesFiltersPanelProps> = ({ filters, onChange }) => {
  const set = (patch: Partial<EpisodeFilters>) => onChange({ ...filters, ...patch });

  const [raw, setRaw] = React.useState<string>(filters.minConfidenceLt?.toString() ?? "");

  const commit = (value: string) => {
    if (value === "") return set({ minConfidenceLt: null });
    const clamped = Math.min(1, Math.max(0, Math.round(Number(value) * 100) / 100));
    set({ minConfidenceLt: clamped });
    setRaw(clamped.toString());
  };

  const confActive = filters.minConfidenceLt != null;

  return (
    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 2 }}>
      {/* Confidence */}
      <FilterChip
        title="Confidence"
        label={confActive ? <>Confidence: &lt; {filters.minConfidenceLt!.toFixed(2)}</> : "Confidence"}
        active={confActive}
        onClear={() => {
          set({ minConfidenceLt: null });
          setRaw("");
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Below
          </Typography>
          <TextField
            label="Max"
            type="number"
            size="small"
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
            slotProps={{
              htmlInput: { min: 0, max: 1, step: 0.01, onBlur: () => commit(raw) },
            }}
            sx={{ width: 90 }}
          />
        </Box>
      </FilterChip>

      {confActive && (
        <ButtonBase
          disableRipple
          onClick={() => {
            onChange({ minConfidenceLt: null });
            setRaw("");
          }}
          sx={{
            px: 1,
            color: "text.secondary",
            "&:hover": { color: "text.primary" },
          }}
        >
          Clear all
        </ButtonBase>
      )}
    </Box>
  );
};

export default EpisodesFiltersPanel;