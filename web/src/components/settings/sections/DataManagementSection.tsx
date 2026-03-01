import { useState } from "react";
import {
  Stack, Typography, Button, MenuItem, TextField,
  Dialog, DialogTitle, DialogContent, DialogContentText,
  DialogActions, Box, Snackbar, Alert,
} from "@mui/material";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import { deleteTraces } from "../../utils/api";

const TIME_RANGES = [
  { value: "1h", label: "Last 1 hour" },
  { value: "12h", label: "Last 12 hours" },
  { value: "24h", label: "Last 24 hours" },
  { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" },
  { value: "all", label: "All time" },
];

const DataManagementSection: React.FC = () => {
  const [selectedRange, setSelectedRange] = useState("1h");
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: "success" | "error" }>({
    open: false,
    message: "",
    severity: "success",
  });

  const selectedLabel = TIME_RANGES.find((r) => r.value === selectedRange)?.label;

  const handleDelete = async () => {
    setConfirmOpen(false);
    try {
      const data = await deleteTraces(selectedRange);
      setSnackbar({
        open: true,
        message: `Deleted ${data.deleted} trace${data.deleted !== 1 ? "s" : ""}`,
        severity: "success",
      });
    } catch {
      setSnackbar({ open: true, message: "Failed to delete traces", severity: "error" });
    }
  };

  return (
    <Stack spacing={3}>
      <Stack spacing={0.5}>
        <Typography variant="h6">TraceStore</Typography>
        <Typography variant="body2" color="text.secondary">
          Permanently delete collected trace data for a given time range.
        </Typography>
      </Stack>

      <Stack spacing={2}>
        <TextField
          select
          label="Time range"
          value={selectedRange}
          onChange={(e) => setSelectedRange(e.target.value)}
        >
          {TIME_RANGES.map(({ value, label }) => (
            <MenuItem key={value} value={value}>
              {label}
            </MenuItem>
          ))}
        </TextField>

        <Stack direction="row" alignItems="center" spacing={2}>
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteOutlineIcon />}
            onClick={() => setConfirmOpen(true)}
          >
            Delete
          </Button>
          <Typography variant="body2" color="text.secondary">
            This action cannot be undone.
          </Typography>
        </Stack>
      </Stack>

      <Dialog open={confirmOpen} onClose={() => setConfirmOpen(false)}>
        <DialogTitle>Delete Trace History?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            You are about to permanently delete all trace data for <Box component="span" sx={{ fontWeight: "bold" }}>
              {selectedLabel?.toLowerCase()}
            </Box>
            . This cannot be recovered.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmOpen(false)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleDelete}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar((s) => ({ ...s, open: false }))}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Stack>
  );
};

export default DataManagementSection;