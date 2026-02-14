import React, { useState } from "react";
import {
  Stack,
  TextField,
  Typography,
  Card,
  CardContent,
  MenuItem,
} from "@mui/material";
import { useSettings } from "../../../contexts/SettingsContext";
import Toggle from "../Toggle";

const EVALUATION_MODELS = [
  { value: "qwen2.5:7b", label: "Qwen 2.5 7B (Local)" },
  { value: "gpt-4o", label: "GPT-4o" },
  { value: "claude-sonnet-4-5-20250929", label: "Claude Sonnet 4.5" },
  { value: "gemini-2.5-flash", label: "Gemini 2.5 Flash" },
];

const CHAT_MODELS = [
  { value: "qwen2.5:7b", label: "Qwen 2.5 7B (Local)" },
  { value: "gpt-4o", label: "GPT-4o" },
  { value: "claude-sonnet-4-5-20250929", label: "Claude Sonnet 4.5" },
  { value: "gemini-2.5-flash", label: "Gemini 2.5 Flash" },
];

type FilterType = "automatic" | "manual";

const AdvancedSection: React.FC = () => {
  const { settings, updateSettings } = useSettings();

  const [activeFilter, setActiveFilter] = useState<FilterType | null>(null);
  const [minSpans, setMinSpans] = useState<number | "">("");
  const [maxDuration, setMaxDuration] = useState<number | "">("");

  const handleFilterToggle = (filter: FilterType) => (checked: boolean) => {
    setActiveFilter(checked ? filter : null);
  };

  return (
    <Stack spacing={3}>
      <Stack spacing={3}>
        {/* AI Evaluation Model */}
        <Stack spacing={0.5}>
          <Typography variant="h6">AI Evaluation</Typography>
          <Typography variant="body2" color="text.secondary">
            Language model used for trace evaluation.
          </Typography>
        </Stack>

        <TextField
          select
          label="Model"
          value={settings.llm.model}
          onChange={(e) =>
            updateSettings((draft) => {
              draft.llm.model = e.target.value;
            })
          }
          helperText="API credentials must be configured for certain models."
        >
          {EVALUATION_MODELS.map(({ value, label }) => (
            <MenuItem key={value} value={value}>
              {label}
            </MenuItem>
          ))}
        </TextField>
      </Stack>

      {/* Chat Model */}
      <Stack spacing={3}>
        <Stack spacing={0.5}>
          <Typography variant="h6">TraceBrain Librarian</Typography>
          <Typography variant="body2" color="text.secondary">
            Language model used for chat.
          </Typography>
        </Stack>

        <TextField
          select
          label="Model"
          value={settings.chatLLM.model}
          onChange={(e) =>
            updateSettings((draft) => {
              draft.chatLLM.model = e.target.value;
            })
          }
          helperText="API credentials must be configured for certain models."
        >
          {CHAT_MODELS.map(({ value, label }) => (
            <MenuItem key={value} value={value}>
              {label}
            </MenuItem>
          ))}
        </TextField>
      </Stack>

      {/* Filters */}
      <Stack>
        <Stack>
          <Typography variant="h6">Trace Filtering</Typography>
          <Typography variant="body2" color="text.secondary">
            Flag traces based on configurable criteria.
          </Typography>
        </Stack>

        <Toggle
          label="Automatic Trace Filtering"
          checked={activeFilter === "automatic"}
          onChange={handleFilterToggle("automatic")}
          tooltip="Filter traces automatically using adaptive metrics."
        />

        <Toggle
          label="Manual Trace Filtering"
          checked={activeFilter === "manual"}
          onChange={handleFilterToggle("manual")}
          tooltip="Define your own filtering criteria using the fields below."
        />

        <Card variant="outlined">
          <CardContent>
            <Typography variant="subtitle1" gutterBottom>
              Manual Trace Filters
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Traces exceeding these thresholds will be flagged.
            </Typography>

            <TextField
              type="number"
              label="Maximum Spans"
              value={minSpans}
              onChange={(e) => setMinSpans(Number(e.target.value))}
              fullWidth
              slotProps={{ htmlInput: { min: 0 } }}
              disabled={activeFilter !== "manual"}
              sx={{ mb: 2 }}
            />

            <TextField
              type="number"
              label="Maximum Duration (ms)"
              value={maxDuration}
              onChange={(e) => setMaxDuration(Number(e.target.value))}
              fullWidth
              slotProps={{ htmlInput: { min: 0 } }}
              disabled={activeFilter !== "manual"}
            />
          </CardContent>
        </Card>
      </Stack>
    </Stack>
  );
};

export default AdvancedSection;
