import { useState } from "react";
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

const Settings: React.FC = () => {
  const [selectedSection, setSelectedSection] = useState<SectionKey>("preferences");
  const [saveSuccessOpen, setSaveSuccessOpen] = useState(false);
  const { saveSettings, isSaving, hasUnsavedChanges, saveError } = useSettings();

  const CurrentSection = SECTIONS[selectedSection].component;

  const handleSave = async () => {
    const success = await saveSettings();
    if (success) {
      setSaveSuccessOpen(true);
    }
  };

  return (
    <Box sx={{ display: "flex", height: "100%", minHeight: 0 }}>
      <Box
        sx={{
          width: 240,
          borderRight: 1,
          pr: 2,
          borderColor: "divider",
          overflowY: "auto",
        }}
      >
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
            {saveError || "Changes are saved only when you click Save Configuration."}
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