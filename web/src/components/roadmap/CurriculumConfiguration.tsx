import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Button,
  FormControl,
  Select,
  MenuItem,
  Popover,
  Checkbox,
  ListItemText,
  Slider,
  Chip,
} from "@mui/material";

const ERROR_TYPE_OPTIONS = [
  { value: "logic_loop", label: "Logic Loop" },
  { value: "hallucination", label: "Hallucination" },
  { value: "invalid_tool_usage", label: "Invalid Tool Usage" },
  { value: "tool_execution_error", label: "Tool Execution Error" },
  { value: "format_error", label: "Format Error" },
  { value: "misinterpretation", label: "Misinterpretation" },
  { value: "context_overflow", label: "Context Overflow" },
  { value: "general_failure", label: "General Failure" },
];

const STORAGE_KEY = "curriculum";

interface CurriculumConfigurationProps {
  anchorEl: HTMLButtonElement | null;
  onClose: () => void;
  onConfirm: (errorTypes: string[], taskLimit: number) => void;
}

const CurriculumConfiguration: React.FC<CurriculumConfigurationProps> = ({
  anchorEl,
  onClose,
  onConfirm,
}) => {
  // draft settings
  const [draftErrorTypes, setDraftErrorTypes] = useState<string[]>([]);
  const [draftTaskLimit, setDraftTaskLimit] = useState<number>(5);

  useEffect(() => {
    if (anchorEl) {
      const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
      setDraftErrorTypes(stored.errorTypes ?? []);
      setDraftTaskLimit(stored.taskLimit ?? 5);
    }
  }, [anchorEl]);

  return (
    <>
      {/* Configuration menu */}
      <Popover
        open={Boolean(anchorEl)}
        anchorEl={anchorEl}
        onClose={onClose}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        transformOrigin={{ vertical: "top", horizontal: "right" }}
        slotProps={{
          paper: {
            sx: {
              width: 300,
              mt: 0.75,
              overflow: "hidden",
              border: 1,
              borderColor: "divider",
            },
          },
        }}
      >
        <Box
          sx={{
            px: 2,
            py: 1.5,
            borderBottom: 1,
            borderColor: "divider",
            bgcolor: "action.hover",
          }}
        >
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            Curriculum Configurations
          </Typography>
        </Box>

        <Box
          sx={{
            p: 2,
            display: "flex",
            flexDirection: "column",
            gap: 2.5,
          }}
        >
          {/* Multiple select error types */}
          <Box>
            <Typography
              variant="caption"
              sx={{
                fontWeight: 600,
                color: "text.secondary",
                textTransform: "uppercase",
                letterSpacing: 0.5,
              }}
            >
              Filter by Error Type
            </Typography>
            <FormControl fullWidth size="small" sx={{ mt: 0.75 }}>
              <Select
                multiple
                displayEmpty
                value={draftErrorTypes}
                onChange={(e) =>
                  setDraftErrorTypes(
                    typeof e.target.value === "string"
                      ? e.target.value.split(",")
                      : e.target.value,
                  )
                }
                renderValue={(selected) =>
                  selected.length === 0 ? (
                    <Typography variant="body2" color="text.disabled">
                      Any
                    </Typography>
                  ) : (
                    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                      {selected.map((val) => (
                        <Chip
                          key={val}
                          label={
                            ERROR_TYPE_OPTIONS.find((o) => o.value === val)
                              ?.label ?? val
                          }
                          size="small"
                          sx={{ height: 20, fontSize: "0.75rem" }}
                        />
                      ))}
                    </Box>
                  )
                }
                MenuProps={{ PaperProps: { style: { maxHeight: 220 } } }}
              >
                {ERROR_TYPE_OPTIONS.map((option) => (
                  <MenuItem key={option.value} value={option.value} dense>
                    <Checkbox
                      checked={draftErrorTypes.includes(option.value)}
                      size="small"
                      sx={{ py: 0, pl: 0, mr: 0.5 }}
                    />
                    <ListItemText
                      primary={option.label}
                      slotProps={{ primary: { variant: "body2" } }}
                    />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          {/* Task limit */}
          <Box>
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                mb: 1,
              }}
            >
              <Typography
                variant="caption"
                sx={{
                  fontWeight: 600,
                  color: "text.secondary",
                  textTransform: "uppercase",
                  letterSpacing: 0.5,
                }}
              >
                Number of Tasks
              </Typography>
              <Typography
                variant="body2"
                sx={{ fontWeight: 700, fontFamily: "monospace" }}
              >
                {draftTaskLimit}
              </Typography>
            </Box>
            <Slider
              value={draftTaskLimit}
              onChange={(_, val) => setDraftTaskLimit(val as number)}
              min={1}
              max={20}
              step={1}
              marks={[
                { value: 1, label: "1" },
                { value: 10, label: "10" },
                { value: 20, label: "20" },
              ]}
              size="small"
            />
          </Box>
        </Box>

        {/* Confirmation buttons */}
        <Box
          sx={{
            px: 2,
            py: 1.5,
            borderTop: 1,
            borderColor: "divider",
            bgcolor: "action.hover",
            display: "flex",
            justifyContent: "flex-end",
            gap: 1,
          }}
        >
          <Button size="small" variant="outlined" onClick={onClose}>
            Cancel
          </Button>

          <Button
            size="small"
            variant="contained"
            onClick={() => {
              localStorage.setItem(
                STORAGE_KEY,
                JSON.stringify({
                  errorTypes: draftErrorTypes,
                  taskLimit: draftTaskLimit,
                }),
              );
              onConfirm(draftErrorTypes, draftTaskLimit);
            }}
          >
            Confirm
          </Button>
        </Box>
      </Popover>
    </>
  );
};

export default CurriculumConfiguration;
