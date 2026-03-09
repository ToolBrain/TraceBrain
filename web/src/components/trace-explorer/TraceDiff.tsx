import React from "react";
import { Box, Chip, Typography } from "@mui/material";
import { ArrowForward, DifferenceOutlined } from "@mui/icons-material";
import type { Trace } from "../../types/trace";
import { traceGetStatus } from "../utils/traceUtils";
import TraceDiffContent from "./TraceDiffContent";

interface TraceDiffProps {
  traces: Trace[];
  selectedTraceIds: string[];
  onSelectedTraceIdsChange: (ids: string[]) => void;
}

const TraceDiff: React.FC<TraceDiffProps> = ({ traces, selectedTraceIds, onSelectedTraceIdsChange }) => {
  const onSelectTrace = (traceId: string) => {
    onSelectedTraceIdsChange(
      selectedTraceIds.includes(traceId)
        ? selectedTraceIds.filter((id) => id !== traceId)
        : selectedTraceIds.length === 2
          ? [selectedTraceIds[1], traceId]
          : [...selectedTraceIds, traceId]
    );
  };

  const traceA = selectedTraceIds[0]
    ? (traces.find((t) => t.trace_id === selectedTraceIds[0]) ?? null)
    : null;
  const traceB = selectedTraceIds[1]
    ? (traces.find((t) => t.trace_id === selectedTraceIds[1]) ?? null)
    : null;
  const labelA = `Trace ${traces.findIndex((t) => t.trace_id === selectedTraceIds[0]) + 1}`;
  const labelB = `Trace ${traces.findIndex((t) => t.trace_id === selectedTraceIds[1]) + 1}`;

  return (
    <Box
      sx={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column", overflow: "hidden" }}
    >
      <Box
        sx={{
          p: 1.5,
          display: "flex",
          alignItems: "center",
          borderBottom: "1px solid",
          borderColor: "divider",
          gap: 1,
          flexWrap: "wrap",
        }}
      >
        {traces.map((trace, idx) => {
          const status = traceGetStatus(trace);
          const isActive = selectedTraceIds.includes(trace.trace_id);
          return (
            <React.Fragment key={trace.trace_id}>
              <Chip
                onClick={() => onSelectTrace(trace.trace_id)}
                label={
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 0.75,
                      fontFamily: "monospace",
                    }}
                  >
                    <Box
                      sx={{
                        width: 8,
                        height: 8,
                        borderRadius: 1,
                        flexShrink: 0,
                        bgcolor:
                          status === "completed"
                            ? "success.main"
                            : status === "failed"
                              ? "error.main"
                              : "text.disabled",
                      }}
                    />
                    {`Trace ${idx + 1}`}
                  </Box>
                }
                variant="outlined"
                sx={{
                  borderColor: "transparent",
                  outline: "2px solid",
                  outlineColor: isActive ? "primary.main" : "divider",
                  borderRadius: 2,
                  "&:hover": { bgcolor: "action.hover" },
                }}
              />
              {idx < traces.length - 1 && (
                <ArrowForward sx={{ fontSize: 16, color: "text.disabled" }} />
              )}
            </React.Fragment>
          );
        })}
      </Box>

      {traceA && traceB ? (
        <TraceDiffContent traceA={traceA} traceB={traceB} labelA={labelA} labelB={labelB} />
      ) : (
        <Box
          sx={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 1,
          }}
        >
          <DifferenceOutlined sx={{ fontSize: 36, color: "text.disabled" }} />
          <Typography sx={{ color: "text.secondary" }}>Nothing to Compare</Typography>
        </Box>
      )}
    </Box>
  );
};

export default TraceDiff;
