import React, { useState } from "react";
import { Stack, TextField, Typography, Card, CardContent, MenuItem, Slider } from "@mui/material";
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

const AdvancedSection: React.FC = () => {
  const { settings, updateSettings } = useSettings();

  return (
    <Stack spacing={3}>
      {/* AI Evaluation Model */}
      <Stack spacing={3}>
        <Stack spacing={0.5}>
          <Typography variant="h6">AI Evaluation</Typography>
          <Typography variant="body2" color="text.secondary">
            Language model used for trace evaluation.
          </Typography>
        </Stack>

        <Stack spacing={1}>
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

          <Toggle
            label="Auto Evaluate"
            checked={settings.llm.autoEvaluate}
            onChange={(checked) =>
              updateSettings((draft) => {
                draft.llm.autoEvaluate = checked;
              })
            }
            tooltip="Automatically evaluate incoming traces."
          />

          <Stack spacing={0.5}>
            <Typography variant="subtitle2">Batch Size</Typography>
            <Typography variant="body2" color="text.secondary">
              Number of traces to evaluate at once.
            </Typography>
            <Slider
              value={settings.llm.batchSize ?? 5}
              onChange={(_, value) =>
                updateSettings((draft) => {
                  draft.llm.batchSize = value as number;
                })
              }
              min={5}
              max={25}
              step={1}
              marks={[
                { value: 5, label: "5" },
                { value: 10, label: "10" },
                { value: 15, label: "15" },
                { value: 20, label: "20" },
                { value: 25, label: "25" },
              ]}
              valueLabelDisplay="auto"
            />
          </Stack>
        </Stack>
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
    </Stack>
  );
};

export default AdvancedSection;