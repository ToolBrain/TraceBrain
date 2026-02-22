import {
  Box,
  Checkbox,
  FormControlLabel,
  Typography,
  Collapse,
  IconButton,
  Button,
} from "@mui/material";
import {
  FilterList,
  ExpandMore,
  ExpandLess,
  FilterAltOff,
} from "@mui/icons-material";
import { useState } from "react";
import type { FilterOption } from "./types";

interface SidebarProps {
  filters: Record<string, FilterOption[]>;
  setFilters: (filters: Record<string, FilterOption[]>) => void;
  onClearFilters: () => void;
  hasActiveFilters: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({
  filters,
  setFilters,
  onClearFilters,
  hasActiveFilters,
}) => {
  const [expanded, setExpanded] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(Object.keys(filters).map((key) => [key, true])),
  );

  // Toggle the checked state of a filter option
  const handleFilterChange = (section: string, optionLabel: string) => {
    setFilters({
      ...filters,
      [section]: filters[section].map((option) =>
        option.label === optionLabel
          ? { ...option, checked: !option.checked }
          : option,
      ),
    });
  };

  return (
    <Box>
      <Box
        sx={{
          p: 2,
          fontWeight: 600,
          color: "text.primary",
          textTransform: "uppercase",
          fontFamily: "monospace",
          display: "flex",
          alignItems: "center",
        }}
      >
        <FilterList fontSize="small" sx={{ mr: 1, ml: 1 }} />
        Filters
      </Box>

      {Object.entries(filters).map(([section, options]) => (
        <Box key={section}>
          <Box
            onClick={() =>
              setExpanded((prev) => ({ ...prev, [section]: !prev[section] }))
            }
            sx={{
              p: 1,
              display: "flex",
              alignItems: "center",
              cursor: "pointer",
            }}
          >
            <IconButton size="small">
              {expanded[section] ? (
                <ExpandMore fontSize="small" />
              ) : (
                <ExpandLess fontSize="small" />
              )}
            </IconButton>
            <Typography
              variant="body2"
              sx={{ fontWeight: 600, fontFamily: "monospace" }}
            >
              {section} ({options.filter((o) => o.checked).length})
            </Typography>
          </Box>

          <Collapse in={expanded[section]}>
            <Box sx={{ pl: 4, pr: 2 }}>
              {options.map((option) => (
                <Box
                  key={option.label}
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <FormControlLabel
                    control={
                      <Checkbox
                        size="small"
                        checked={option.checked}
                        onChange={() =>
                          handleFilterChange(section, option.label)
                        }
                      />
                    }
                    label={
                      <Typography
                        variant="body2"
                        sx={{ fontWeight: 600, fontFamily: "monospace" }}
                      >
                        {option.label}
                      </Typography>
                    }
                  />
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ fontWeight: 600 }}
                  >
                    {option.count}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Collapse>
        </Box>
      ))}

      {hasActiveFilters && (
        <Box p={2}>
          <Button
            fullWidth
            size="small"
            onClick={onClearFilters}
            startIcon={<FilterAltOff fontSize="small" />}
            variant="outlined"
            color="inherit"
            sx={{
              borderRadius: 1,
              color: "text.secondary",
              "&:hover": {
                color: "error.main",
                bgcolor: "error.50",
              },
            }}
          >
            Clear filters
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default Sidebar;
