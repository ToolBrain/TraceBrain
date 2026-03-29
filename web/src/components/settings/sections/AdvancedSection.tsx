import React, { useState } from "react";
import {
  Autocomplete,
  Stack,
  Slider,
  TextField,
  Typography,
  MenuItem,
  IconButton,
  InputAdornment,
} from "@mui/material";
import { Visibility, VisibilityOff } from "@mui/icons-material";
import { useSettings } from "../../../contexts/SettingsContext";
import Toggle from "../Toggle";

const PROVIDERS = [
  { value: "openai", label: "OpenAI" },
  { value: "gemini", label: "Gemini" },
  { value: "anthropic", label: "Anthropic" },
  { value: "huggingface", label: "Hugging Face" },
];

type ProviderValue = (typeof PROVIDERS)[number]["value"];

const MODEL_PRESETS = {
  openai: [
    "gpt-5.4",
    "gpt-5.3-chat-latest",
    "gpt-5.4-mini",
    "gpt-4.1",
    "gpt-4o-mini",
    "gpt-5",
  ],
  gemini: [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite-001",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite",
  ],
  anthropic: [
    "claude-sonnet-4-6",
    "claude-haiku-4-5-20251001",
    "claude-opus-4-6",
    "claude-sonnet-4-5-20250929",
    "claude-opus-4-5-20251101",
  ],
  huggingface: [],
} as const;

const AdvancedSection: React.FC = () => {
  const { settings, updateSettings } = useSettings();

  const [showKeys, setShowKeys] = useState<Record<ProviderValue, boolean>>({
    openai: false,
    gemini: false,
    anthropic: false,
    huggingface: false,
  });

  const toggleKeyVisibility = (provider: ProviderValue) => {
    setShowKeys((prev) => ({ ...prev, [provider]: !prev[provider] }));
  };

  const keyAdornment = (provider: ProviderValue) => (
    <InputAdornment position="end">
      <IconButton
        edge="end"
        onClick={() => toggleKeyVisibility(provider)}
        aria-label={showKeys[provider] ? "Hide API key" : "Show API key"}
      >
        {showKeys[provider] ? <VisibilityOff /> : <Visibility />}
      </IconButton>
    </InputAdornment>
  );

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
            label="Provider"
            value={settings.llm.provider}
            onChange={(e) =>
              updateSettings((draft) => {
                draft.llm.provider = e.target.value as typeof draft.llm.provider;
              })
            }
            helperText="Select which provider powers AI Judge evaluations."
          >
            {PROVIDERS.map(({ value, label }) => (
              <MenuItem key={value} value={value}>
                {label}
              </MenuItem>
            ))}
          </TextField>

          <Autocomplete
            freeSolo
            options={MODEL_PRESETS[settings.llm.provider]}
            value={settings.llm.model}
            onInputChange={(_, newInputValue) =>
              updateSettings((draft) => {
                draft.llm.model = newInputValue;
              })
            }
            onChange={(_, newValue) =>
              updateSettings((draft) => {
                draft.llm.model = typeof newValue === "string" ? newValue : draft.llm.model;
              })
            }
            renderInput={(params) => (
              <TextField
                {...params}
                label="Model ID"
                helperText="Choose a preset or type any custom model ID."
              />
            )}
          />

          <TextField
            type={showKeys[settings.llm.provider] ? "text" : "password"}
            label="API Key"
            value={settings.apiKeys[settings.llm.provider]}
            onChange={(e) =>
              updateSettings((draft) => {
                draft.apiKeys[draft.llm.provider] = e.target.value;
              })
            }
            autoComplete="off"
            helperText="Stored securely in local database. Leave unchanged to keep current key."
            InputProps={{ endAdornment: keyAdornment(settings.llm.provider) }}
          />

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
          label="Provider"
          value={settings.chatLLM.provider}
          onChange={(e) =>
            updateSettings((draft) => {
              draft.chatLLM.provider = e.target.value as typeof draft.chatLLM.provider;
            })
          }
          helperText="Select which provider powers Librarian chat."
        >
          {PROVIDERS.map(({ value, label }) => (
            <MenuItem key={value} value={value}>
              {label}
            </MenuItem>
          ))}
        </TextField>

        <Autocomplete
          freeSolo
          options={MODEL_PRESETS[settings.chatLLM.provider]}
          value={settings.chatLLM.model}
          onInputChange={(_, newInputValue) =>
            updateSettings((draft) => {
              draft.chatLLM.model = newInputValue;
            })
          }
          onChange={(_, newValue) =>
            updateSettings((draft) => {
              draft.chatLLM.model = typeof newValue === "string" ? newValue : draft.chatLLM.model;
            })
          }
          renderInput={(params) => (
            <TextField
              {...params}
              label="Model ID"
              helperText="Choose a preset or type any custom model ID."
            />
          )}
        />

        <TextField
          type={showKeys[settings.chatLLM.provider] ? "text" : "password"}
          label="API Key"
          value={settings.apiKeys[settings.chatLLM.provider]}
          onChange={(e) =>
            updateSettings((draft) => {
              draft.apiKeys[draft.chatLLM.provider] = e.target.value;
            })
          }
          autoComplete="off"
          helperText="Stored securely in local database. Leave unchanged to keep current key."
          InputProps={{ endAdornment: keyAdornment(settings.chatLLM.provider) }}
        />
      </Stack>

      {/* Curriculum Model */}
      <Stack spacing={3}>
        <Stack spacing={0.5}>
          <Typography variant="h6">Automated Curriculum (Curator Agent)</Typography>
          <Typography variant="body2" color="text.secondary">
            Language model used to generate training curriculum from failed traces.
          </Typography>
        </Stack>

        <TextField
          select
          label="Provider"
          value={settings.curatorLLM.provider}
          onChange={(e) =>
            updateSettings((draft) => {
              draft.curatorLLM.provider = e.target.value as typeof draft.curatorLLM.provider;
            })
          }
          helperText="Select which provider powers Curator curriculum generation."
        >
          {PROVIDERS.map(({ value, label }) => (
            <MenuItem key={value} value={value}>
              {label}
            </MenuItem>
          ))}
        </TextField>

        <Autocomplete
          freeSolo
          options={MODEL_PRESETS[settings.curatorLLM.provider]}
          value={settings.curatorLLM.model}
          onInputChange={(_, newInputValue) =>
            updateSettings((draft) => {
              draft.curatorLLM.model = newInputValue;
            })
          }
          onChange={(_, newValue) =>
            updateSettings((draft) => {
              draft.curatorLLM.model = typeof newValue === "string" ? newValue : draft.curatorLLM.model;
            })
          }
          renderInput={(params) => (
            <TextField
              {...params}
              label="Model ID"
              helperText="Choose a preset or type any custom model ID."
            />
          )}
        />

        <TextField
          type={showKeys[settings.curatorLLM.provider] ? "text" : "password"}
          label="API Key"
          value={settings.apiKeys[settings.curatorLLM.provider]}
          onChange={(e) =>
            updateSettings((draft) => {
              draft.apiKeys[draft.curatorLLM.provider] = e.target.value;
            })
          }
          autoComplete="off"
          helperText="Stored securely in local database. Leave unchanged to keep current key."
          InputProps={{ endAdornment: keyAdornment(settings.curatorLLM.provider) }}
        />
      </Stack>
    </Stack>
  );
};

export default AdvancedSection;