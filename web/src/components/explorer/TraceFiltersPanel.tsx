import React from "react";
import {
  Box,
  Radio,
  RadioGroup,
  FormControlLabel,
  TextField,
  Stack,
  Rating,
  Typography,
  ButtonBase,
  Divider,
} from "@mui/material";
import FilterChip from "./FilterChip";
import type { TraceFilters } from "./types";
import { ERROR_TYPE_STYLES, type ErrorType } from "../shared/ErrorTypeChip";
import { STATUS_STYLES } from "../shared/StatusChip";
import { toTitleCase } from "../utils/utils";

const STATUS_KEYS = ["running", "completed", "needs_review", "failed"] as const;
const ERROR_KEYS = Object.keys(ERROR_TYPE_STYLES) as (keyof typeof ERROR_TYPE_STYLES)[];

const DATE_PRESETS = [
  { label: "Today", days: 0 },
  { label: "Yesterday", days: 1 },
  { label: "Last week", days: 7 },
  { label: "Last month", days: 28 },
  { label: "Last 3 months", days: 90 },
  { label: "Last 12 months", days: 365 },
];

const Dot = ({ color }: { color: string }) => (
  <Box
    component="span"
    sx={{
      width: 8,
      height: 8,
      borderRadius: "50%",
      backgroundColor: color,
      display: "inline-block",
      verticalAlign: "middle",
      flexShrink: 0,
    }}
  />
);

interface TraceFiltersPanelProps {
  filters: TraceFilters;
  onChange: (filters: TraceFilters) => void;
}

const TraceFiltersPanel: React.FC<TraceFiltersPanelProps> = ({ filters, onChange }) => {
  const set = (patch: Partial<TraceFilters>) => onChange({ ...filters, ...patch });

  const [minRaw, setMinRaw] = React.useState<string>(filters.minConfidence?.toString() ?? "");
  const [maxRaw, setMaxRaw] = React.useState<string>(filters.maxConfidence?.toString() ?? "");

  const commitMin = (raw: string) => {
    if (raw === "") return set({ minConfidence: null });
    const clamped = Math.min(1, Math.max(0, Math.round(Number(raw) * 100) / 100));
    set({ minConfidence: clamped });
    setMinRaw(clamped.toString());
  };

  const commitMax = (raw: string) => {
    if (raw === "") return set({ maxConfidence: null });
    const clamped = Math.min(1, Math.max(0, Math.round(Number(raw) * 100) / 100));
    set({ maxConfidence: clamped });
    setMaxRaw(clamped.toString());
  };

  const selectedStatus = filters.status
    ? STATUS_STYLES[filters.status as keyof typeof STATUS_STYLES]
    : null;
  const selectedError = filters.errorType
    ? ERROR_TYPE_STYLES[filters.errorType as ErrorType]
    : null;
  const confActive = filters.minConfidence != null || filters.maxConfidence != null;
  const dateActive = !!filters.startTime || !!filters.endTime;

  const activeDatePreset = (() => {
    if (!filters.startTime || !filters.endTime) return null;
    const end = new Date(filters.endTime);
    const start = new Date(filters.startTime);
    const diffDays = Math.round((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
    return DATE_PRESETS.find((p) => p.days === diffDays)?.label ?? null;
  })();

  const applyPreset = (days: number) => {
    if (days === 0) {
      const today = new Date().toISOString().slice(0, 10);
      set({ startTime: today, endTime: today });
    } else {
      const end = new Date();
      const start = new Date();
      start.setDate(end.getDate() - days);
      set({ startTime: start.toISOString().slice(0, 10), endTime: end.toISOString().slice(0, 10) });
    }
  };

  return (
    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 2 }}>
      {/* Status */}
      <FilterChip
        title="Status"
        label={selectedStatus ? <>Status: {toTitleCase(selectedStatus.label)}</> : "Status"}
        active={!!filters.status}
        onClear={() => set({ status: "" })}
      >
        <RadioGroup value={filters.status || ""} onChange={(e) => set({ status: e.target.value })}>
          {STATUS_KEYS.map((key) => (
            <FormControlLabel
              key={key}
              value={key}
              control={<Radio size="small" />}
              label={
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Dot color={STATUS_STYLES[key].border} />
                  {toTitleCase(STATUS_STYLES[key].label)}
                </Box>
              }
            />
          ))}
        </RadioGroup>
      </FilterChip>

      {/* Error Type */}
      <FilterChip
        title="Error Type"
        label={selectedError ? <>Error Type: {toTitleCase(selectedError.label)}</> : "Error Type"}
        active={!!filters.errorType}
        onClear={() => set({ errorType: "" })}
      >
        <RadioGroup
          value={filters.errorType || ""}
          onChange={(e) => set({ errorType: e.target.value })}
        >
          {ERROR_KEYS.map((key) => (
            <FormControlLabel
              key={key}
              value={key}
              control={<Radio size="small" />}
              label={
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Dot color={ERROR_TYPE_STYLES[key].border} />
                  {toTitleCase(ERROR_TYPE_STYLES[key].label)}
                </Box>
              }
            />
          ))}
        </RadioGroup>
      </FilterChip>

      {/* Minimum Rating */}
      <FilterChip
        title="Min Rating"
        label={filters.minRating != null ? <>Min Rating: {filters.minRating}</> : "Min Rating"}
        active={filters.minRating != null}
        onClear={() => set({ minRating: null })}
      >
        <RadioGroup
          value={filters.minRating ?? ""}
          onChange={(e) => set({ minRating: e.target.value ? Number(e.target.value) : null })}
        >
          {[1, 2, 3, 4, 5].map((star) => (
            <FormControlLabel
              key={star}
              value={star}
              control={<Radio size="small" />}
              label={<Rating value={star} readOnly size="small" />}
            />
          ))}
        </RadioGroup>
      </FilterChip>

      {/* Confidence */}
      <FilterChip
        title="Confidence"
        label={
          confActive ? (
            <>
              Confidence: {(filters.minConfidence ?? 0).toFixed(2)}–
              {(filters.maxConfidence ?? 1).toFixed(2)}
            </>
          ) : (
            "Confidence"
          )
        }
        active={confActive}
        onClear={() => {
          set({ minConfidence: null, maxConfidence: null });
          setMinRaw("");
          setMaxRaw("");
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <TextField
            label="Min"
            type="number"
            size="small"
            value={minRaw}
            onChange={(e) => setMinRaw(e.target.value)}
            slotProps={{
              htmlInput: { min: 0, max: 1, step: 0.01, onBlur: () => commitMin(minRaw) },
            }}
            sx={{ width: 90 }}
          />
          <Typography variant="body2" color="text.disabled">
            -
          </Typography>
          <TextField
            label="Max"
            type="number"
            size="small"
            value={maxRaw}
            onChange={(e) => setMaxRaw(e.target.value)}
            slotProps={{
              htmlInput: { min: 0, max: 1, step: 0.01, onBlur: () => commitMax(maxRaw) },
            }}
            sx={{ width: 90 }}
          />
        </Box>
      </FilterChip>

      {/* Date Range */}
      <FilterChip
        title="Date Range"
        label={
          dateActive
            ? (activeDatePreset ?? (
                <>
                  {filters.startTime
                    ? new Date(filters.startTime).toLocaleDateString("en-GB", {
                        day: "numeric",
                        month: "short",
                        year: "numeric",
                      })
                    : "…"}
                  {" - "}
                  {filters.endTime
                    ? new Date(filters.startTime).toLocaleDateString("en-GB", {
                        day: "numeric",
                        month: "short",
                        year: "numeric",
                      })
                    : "…"}
                </>
              ))
            : "Date Range"
        }
        active={dateActive}
        onClear={() => set({ startTime: "", endTime: "" })}
      >
        <Stack spacing={1.5} sx={{ width: 200 }}>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 0.25 }}>
            {DATE_PRESETS.map((preset) => (
              <ButtonBase
                key={preset.label}
                disableRipple
                onClick={() => applyPreset(preset.days)}
                sx={{
                  px: 1,
                  py: 0.75,
                  borderRadius: 2,
                  justifyContent: "flex-start",
                  fontWeight: activeDatePreset === preset.label ? 600 : 400,
                  color: activeDatePreset === preset.label ? "primary.main" : "text.primary",
                  backgroundColor: activeDatePreset === preset.label ? "primary.50" : "transparent",
                  "&:hover": { backgroundColor: "action.hover" },
                }}
              >
                {preset.label}
              </ButtonBase>
            ))}
          </Box>

          <Divider />

          <Stack spacing={1}>
            <TextField
              label="From"
              type="date"
              size="small"
              value={filters.startTime?.slice(0, 10) ?? ""}
              onChange={(e) => set({ startTime: e.target.value })}
              slotProps={{ inputLabel: { shrink: true } }}
            />
            <TextField
              label="To"
              type="date"
              size="small"
              value={filters.endTime?.slice(0, 10) ?? ""}
              onChange={(e) => set({ endTime: e.target.value })}
              slotProps={{ inputLabel: { shrink: true } }}
            />
          </Stack>
        </Stack>
      </FilterChip>

      {/* Clear all */}
      {(!!filters.status ||
        !!filters.errorType ||
        filters.minRating != null ||
        confActive ||
        dateActive) && (
        <ButtonBase
          disableRipple
          onClick={() =>
            onChange({
              status: "",
              errorType: "",
              minRating: null,
              minConfidence: null,
              maxConfidence: null,
              startTime: "",
              endTime: "",
            })
          }
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

export default TraceFiltersPanel;
