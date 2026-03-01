import { useState } from "react";
import {
  Box,
  List,
  ListItemButton,
  ListItemText,
} from "@mui/material";
import PreferencesSection from "./sections/PreferencesSection";
import AdvancedSection from "./sections/AdvancedSection";
import DataManagementSection from "./sections/DataManagementSection";

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

  const CurrentSection = SECTIONS[selectedSection].component;

  return (
    <Box sx={{ display: "flex", height: "100%" }}>
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
      <Box sx={{ flex: 1, p: 3 }}>
        <CurrentSection />
      </Box>
    </Box>
  );
};

export default Settings;