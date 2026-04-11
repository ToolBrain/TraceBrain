import React, { useEffect, useState } from "react";
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  CircularProgress,
  Stack,
  Slider,
  Snackbar,
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
  huggingface: [
    "Qwen/Qwen2.5-72B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen3-4B-Instruct-2507",
  ],
} as const;

type SystemInfo = {
  database_type: string;
  embedding_provider: string;
  embedding_model: string;
};

const formatEmbeddingProvider = (provider: string | undefined): string => {
  const normalized = (provider || "").trim().toLowerCase();
  if (!normalized) return "Unknown";
  if (normalized === "openai") return "OpenAI";
  if (normalized === "gemini") return "Gemini";
  if (normalized === "anthropic") return "Anthropic";
  if (normalized === "huggingface") return "Hugging Face";
  if (normalized === "local") return "Local";
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
};

const AdvancedSection: React.FC = () => {
  const { settings, updateSettings, saveSettings, isSaving, hasUnsavedChanges, saveError } = useSettings();
  const [saveSuccessOpen, setSaveSuccessOpen] = useState(false);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);

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

  const handleSave = async () => {
    const success = await saveSettings();
    if (success) {
      setSaveSuccessOpen(true);
    }
  };

  useEffect(() => {
    let isMounted = true;

    const loadSystemInfo = async () => {
      try {
        const response = await fetch("/api/v1/system/info");
        if (!response.ok) {
          throw new Error(`Failed to load system info: ${response.statusText}`);
        }
        const payload = (await response.json()) as SystemInfo;
        if (isMounted) {
          setSystemInfo(payload);
        }
      } catch {
        if (isMounted) {
          setSystemInfo(null);
        }
      }
    };

    void loadSystemInfo();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <Stack spacing={3}>
      <Alert
        severity="info"
        variant="outlined"
        sx={{ borderRadius: 2, alignItems: "flex-start", bgcolor: "action.hover" }}
      >
        <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 0.5 }}>
          System Info
        </Typography>
        <Typography variant="body2">
          Database: {systemInfo?.database_type || "Unknown"}
        </Typography>
        <Typography variant="body2" sx={{ mb: 0.5 }}>
          Embedding Engine: {formatEmbeddingProvider(systemInfo?.embedding_provider)} ({systemInfo?.embedding_model || "Unknown"}) - Active
        </Typography>
        <Typography variant="caption" color="text.secondary">
          Embedding is infrastructure-level. Keep one embedding engine for the full database lifecycle. Changing the provider or model requires a full re-embedding migration.
        </Typography>
      </Alert>

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
                const newProvider = e.target.value as typeof draft.llm.provider;
                draft.llm.provider = newProvider;
                draft.llm.model = MODEL_PRESETS[newProvider][0];
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
            slotProps={{ input: { endAdornment: keyAdornment(settings.llm.provider) } }}
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
              const newProvider = e.target.value as typeof draft.chatLLM.provider;
              draft.chatLLM.provider = newProvider;
              draft.chatLLM.model = MODEL_PRESETS[newProvider][0];
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
          slotProps={{ input: { endAdornment: keyAdornment(settings.chatLLM.provider) } }}
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
              const newProvider = e.target.value as typeof draft.curatorLLM.provider;
              draft.curatorLLM.provider = newProvider;
              draft.curatorLLM.model = MODEL_PRESETS[newProvider][0];
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
          slotProps={{ input: { endAdornment: keyAdornment(settings.curatorLLM.provider) } }}
        />
      </Stack>

      <Box
        sx={{
          borderTop: 1,
          borderColor: "divider",
          pt: 2,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 2,
        }}
      >
        <Typography variant="body2" color={saveError ? "error.main" : "text.secondary"}>
          {saveError || "Display preferences are saved locally. Click Save Configuration to sync LLM and API key settings."}
        </Typography>
        <Button
          variant="contained"
          color="primary"
          size="large"
          onClick={handleSave}
          disabled={isSaving || !hasUnsavedChanges}
          startIcon={isSaving ? <CircularProgress size={16} color="inherit" /> : null}
        >
          {isSaving ? "Saving..." : "Save Configuration"}
        </Button>
      </Box>

      <Snackbar
        open={saveSuccessOpen}
        autoHideDuration={2500}
        onClose={() => setSaveSuccessOpen(false)}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert
          onClose={() => setSaveSuccessOpen(false)}
          severity="success"
          variant="filled"
          sx={{ width: "100%" }}
        >
          Configuration saved successfully.
        </Alert>
      </Snackbar>
    </Stack>
  );
};

export default AdvancedSection;
