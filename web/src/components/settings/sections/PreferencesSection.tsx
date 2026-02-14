import { Stack, Box, Typography, Slider } from "@mui/material";
import { useSettings } from "../../../contexts/SettingsContext";
import Toggle from "../Toggle";

const PreferencesSection: React.FC = () => {
  const { settings, updateSettings } = useSettings();
  
  return (
    <Stack>
      <Toggle
        label="Dark Mode"
        checked={settings.appearance.theme === "dark"}
        onChange={(checked: boolean) =>
          updateSettings(draft => {
            draft.appearance.theme = checked ? "dark" : "light";
          })
        }
      />
      <Toggle
        label="Auto Refresh"
        checked={settings.refresh.autoRefresh}
        onChange={(checked: boolean) =>
          updateSettings(draft => {
            draft.refresh.autoRefresh = checked;
          })
        }
        tooltip="Automatically refresh data at regular intervals"
      />
      <Box sx={{ mt: 2, px: 2 }}>
        <Typography
          variant="body2"
          gutterBottom
          sx={{
            color: settings.refresh.autoRefresh ? "text.primary" : "text.disabled",
            fontFamily: "monospace",
          }}
        >
          Refresh Interval
        </Typography>
        <Slider
          value={settings.refresh.refreshInterval}
          onChange={(_, value) =>
            updateSettings(draft => {
              draft.refresh.refreshInterval = value as number;
            })
          }
          min={30}
          max={300}
          step={10}
          valueLabelDisplay="auto"
          marks={[
            { value: 30, label: "30s" },
            { value: 60, label: "1m" },
            { value: 120, label: "2m" },
            { value: 180, label: "3m" },
            { value: 240, label: "4m" },
            { value: 300, label: "5m" },
          ]}
          disabled={!settings.refresh.autoRefresh}
          sx={{
            color: settings.refresh.autoRefresh ? "primary.main" : "grey.400",
            "& .MuiSlider-thumb": {
              backgroundColor: settings.refresh.autoRefresh
                ? "primary.main"
                : "grey.400",
            },
            "& .MuiSlider-track": {
              backgroundColor: settings.refresh.autoRefresh
                ? "primary.main"
                : "grey.400",
            },
            "& .MuiSlider-rail": {
              backgroundColor: settings.refresh.autoRefresh ? "grey.300" : "grey.200",
            },
          }}
        />
      </Box>
    </Stack>
  );
};

export default PreferencesSection;