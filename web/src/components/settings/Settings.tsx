import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  List,
  ListItemButton,
  ListItemText,
  Snackbar,
  Typography,
} from "@mui/material";
import PreferencesSection from "./sections/PreferencesSection";
import AdvancedSection from "./sections/AdvancedSection";
import DataManagementSection from "./sections/DataManagementSection";
import { useSettings } from "../../contexts/SettingsContext";

type SectionKey = "preferences" | "advanced" | "data";

type SystemInfo = {
  database_type: string;
  embedding_provider: string;
  embedding_model: string;
};

type Section = {
  label: string;
  component: React.FC;
};

const SECTIONS: Record<SectionKey, Section> = {
  preferences: {
    label: "Preferences",
    component: PreferencesSection,
  },
  advanced: {
    label: "Advanced",
    component: AdvancedSection,
  },
  data: {
    label: "Data Management",
    component: DataManagementSection
  }
};

const SECTION_KEYS: SectionKey[] = ["preferences", "advanced", "data"];

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

const Settings: React.FC = () => {
  const [selectedSection, setSelectedSection] = useState<SectionKey>("preferences");
  const [saveSuccessOpen, setSaveSuccessOpen] = useState(false);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const { saveSettings, isSaving, hasUnsavedChanges, saveError } = useSettings();

  const CurrentSection = SECTIONS[selectedSection].component;

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
    <Box sx={{ display: "flex", height: "100%", overflow: "hidden" }}>
      <Box sx={{ width: 240, borderRight: 1, pr: 2, borderColor: "divider" }}>
        <List>
          {SECTION_KEYS.map((key) => (
            <ListItemButton
              key={key}
              selected={selectedSection === key}
              onClick={() => setSelectedSection(key)}
              sx={{
                borderBottomWidth: 2,
                borderBottomStyle: "solid",
                borderBottomColor:
                  selectedSection === key
                    ? "primary.main"
                    : "transparent",
              }}
            >
              <ListItemText
                primary={SECTIONS[key].label}
                slotProps={{
                  primary: { sx: { fontWeight: 700, textAlign: "center" } },
                }}
              />
            </ListItemButton>
          ))}
        </List>
      </Box>
      <Box sx={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
        <Box sx={{ flex: 1, p: 3, minHeight: 0, overflowY: "auto" }}>
          <Alert
            severity="info"
            variant="outlined"
            sx={{ mb: 3, borderRadius: 2, alignItems: "flex-start" }}
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
              Embedding is infrastructure-level. Keep one embedding engine per database lifecycle; changing provider/model requires full re-embedding migration.
            </Typography>
          </Alert>
          <CurrentSection />
        </Box>
        <Box
          sx={{
            borderTop: 1,
            borderColor: "divider",
            px: 3,
            py: 2,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 2,
          }}
        >
          <Typography variant="body2" color={saveError ? "error.main" : "text.secondary"}>
            {saveError || "Display preferences are saved locally. Click Save Configuration to sync LLM and API key settings. Embedding configuration is managed via .env as infrastructure."}
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
    </Box>
  );
};

export default Settings;