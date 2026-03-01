import React, { useState } from "react";
import { Popover, Box, Typography, ButtonBase, Divider, Button } from "@mui/material";
import KeyboardArrowDownRounded from "@mui/icons-material/KeyboardArrowDownRounded";
import KeyboardArrowUpRounded from "@mui/icons-material/KeyboardArrowUpRounded";

interface FilterChipProps {
  label: React.ReactNode;
  title: React.ReactNode;
  active?: boolean;
  onClear?: () => void;
  children: React.ReactNode;
}

const FilterChip: React.FC<FilterChipProps> = ({ label, title, onClear, children, active }) => {
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const open = Boolean(anchorEl);

  const handleClick = (e: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(open ? null : e.currentTarget);
  };

  const handleClear = () => {
    onClear?.();
    setAnchorEl(null);
  };

  return (
    <>
      <ButtonBase
        onClick={handleClick}
        disableRipple
        sx={{
          px: 1.5,
          py: 0.625,
          borderRadius: 2,
          outline: "2px solid",
          outlineColor: active ? "primary.main" : "divider",
          color: active ? "primary.main" : "text.primary",
          "&:hover": { backgroundColor: "action.hover" },
        }}
      >
        {label}
        {open ? (
          <KeyboardArrowUpRounded sx={{ fontSize: 18, ml: 0.5 }} />
        ) : (
          <KeyboardArrowDownRounded sx={{ fontSize: 18, ml: 0.5 }} />
        )}
      </ButtonBase>

      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
        transformOrigin={{ vertical: "top", horizontal: "left" }}
        slotProps={{
          paper: {
            elevation: 0,
            sx: {
              borderRadius: 2,
              border: "1px solid",
              borderColor: "divider",
              minWidth: 180,
              mt: 0.5
            },
          },
        }}
      >
        <Box
          sx={{
            px: 2,
            py: 1.25,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Typography sx={{ fontWeight: 600}}>
            {title}
          </Typography>
          {onClear && (
            <Button
              size="small"
              onClick={handleClear}
              disableRipple
              sx={{ textTransform: "none", minWidth: "auto", px: 0.5, py: 0 }}
            >
              Clear
            </Button>
          )}
        </Box>
        <Divider />
        <Box sx={{ p: 2 }}>{children}</Box>
      </Popover>
    </>
  );
};

export default FilterChip;
