import { Switch, Box, Typography, Tooltip, IconButton } from "@mui/material";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";

interface ToggleProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  tooltip?: string;
}

const Toggle: React.FC<ToggleProps> = ({ label, checked, onChange, tooltip }) => {
  return (
    <Box display="flex" alignItems="center">
      <Switch checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <Typography>{label}</Typography>
      {tooltip && (
        <Tooltip title={tooltip}>
          <IconButton size="small">
            <HelpOutlineIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      )}
    </Box>
  );
}

export default Toggle;