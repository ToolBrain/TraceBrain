import {
  Box,
  Chip,
  Dialog,
  DialogContent,
  IconButton,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { Close, ContentCopy, Source } from "@mui/icons-material";
import { useState } from "react";

interface TraceSourcesDialogProps {
  sources: string[];
}

const TraceSources: React.FC<TraceSourcesDialogProps> = ({ sources }) => {
  const [open, setOpen] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [hoveredSource, setHoveredSource] = useState<string | null>(null);

  const handleCopy = (source: string) => {
    navigator.clipboard.writeText(source);
    setCopiedId(source);
    setTimeout(() => setCopiedId(null), 2500);
  };

  return (
    <Box sx={{ mt: 1 }}>
      <Chip
        icon={<Source sx={{ fontSize: 12 }} />}
        label={`${sources.length} Sources`}
        size="small"
        variant="outlined"
        onClick={() => setOpen(true)}
        sx={{
          height: 24,
          fontSize: "0.625rem",
          borderColor: "divider",
          bgcolor: "background.paper",
          cursor: "pointer",
          "& .MuiChip-icon": { fontSize: 12 },
          p: 0.5,
        }}
      />

      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        slotProps={{
          paper: {
            sx: {
            maxWidth: "40vw",
            bgcolor: "background.paper",
            backgroundImage: "none",
            border: "1px solid",
            borderColor: "divider",
            borderRadius: 2,
          }},
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            px: 2.5,
            pt: 2,
            pb: 1.5,
            borderBottom: "1px solid",
            borderColor: "divider",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Source sx={{ fontSize: 16, color: "text.secondary" }} />
            <Typography variant="subtitle2" fontWeight={600}>
              Referenced Traces
            </Typography>
            <Box
              sx={{
                px: 0.75,
                py: 0.1,
                borderRadius: 1,
                bgcolor: "action.selected",
              }}
            >
              <Typography variant="caption" color="text.secondary">
                {sources.length}
              </Typography>
            </Box>
          </Box>
          <IconButton size="small" onClick={() => setOpen(false)}>
            <Close sx={{ fontSize: 16 }} />
          </IconButton>
        </Box>

        <DialogContent sx={{ p: 2, maxHeight: 360, overflowY: "auto" }}>
          <Stack spacing={0.75}>
            {sources.map((source, index) => (
              <Box
                key={index}
                onMouseEnter={() => setHoveredSource(source)}
                onMouseLeave={() => setHoveredSource(null)}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  px: 1.5,
                  py: 1,
                  borderRadius: 1.5,
                  border: "1px solid",
                  borderColor: hoveredSource === source ? "primary.main" : "divider",
                  bgcolor: hoveredSource === source ? "action.hover" : "background.default",
                  transition: "all 0.25s ease",
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    fontFamily: "monospace",
                    fontSize: "0.75rem",
                    color: "text.secondary",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    flex: 1,
                    mr: 1,
                  }}
                >
                  {source}
                </Typography>
                <Tooltip title={copiedId === source ? "Copied!" : "Copy ID"} placement="left">
                  <IconButton
                    size="small"
                    onClick={() => handleCopy(source)}
                    sx={{
                      opacity: hoveredSource === source ? 1 : 0,
                      transition: "opacity 0.25s ease",
                      color: copiedId === source ? "success.main" : "text.secondary",
                      p: 0.25,
                    }}
                  >
                    <ContentCopy sx={{ fontSize: 12 }} />
                  </IconButton>
                </Tooltip>
              </Box>
            ))}
          </Stack>
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default TraceSources;