import React, { useState } from "react";
import {
  Box,
  Collapse,
  IconButton,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import {
  Flag,
  KeyboardArrowDown,
  KeyboardArrowRight,
  Layers,
  Token,
} from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import type { Trace } from "../../types/trace";
import SpanRows from "./SpanRows";
import {
  traceGetDuration,
  traceGetErrorType,
  traceGetEvaluation,
  traceGetPriority,
  traceGetStartTime,
  traceGetStatus,
  traceGetTotalTokens,
} from "../utils/traceUtils";
import { formatDateTime, getPriorityColor } from "../utils/utils";
import StatusChip from "./StatusChip";
import TypeChip from "./TypeChip";
import ErrorTypeChip from "./ErrorTypeChip";
import ConfidenceIndicator from "./ConfidenceIndicator";

const TraceRow: React.FC<{ trace: Trace }> = ({ trace }) => {
  const [open, setOpen] = useState(false);
  const nav = useNavigate();
  const duration = traceGetDuration(trace);
  const startTime = traceGetStartTime(trace);
  const status = traceGetStatus(trace);
  const priority = traceGetPriority(trace);
  const totalTokens = traceGetTotalTokens(trace) ?? "N/A";
  const errorType = traceGetErrorType(trace);
  const evaluation = traceGetEvaluation(trace);
  const confidence = evaluation?.confidence;
  const suggestion_status = evaluation?.status;
  const isAnalyzing = !evaluation;

  return (
    <React.Fragment>
      <TableRow
        hover
        onClick={() => nav(`/trace/${trace.trace_id}`)}
        sx={{ cursor: "pointer" }}
      >
        <TableCell>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              setOpen((v) => !v);
            }}
          >
            {open ? <KeyboardArrowDown /> : <KeyboardArrowRight />}
          </IconButton>
        </TableCell>
        <TableCell>
          <Typography
            variant="body2"
            sx={{
              fontFamily: "monospace",
            }}
          >
            {formatDateTime(startTime)}
          </Typography>
        </TableCell>
        <TableCell>
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              gap: 0.5,
            }}
          >
            <TypeChip type="trace" />

            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: "flex", alignItems: "center", gap: 1 }}
            >
              {/* Span Count */}
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 0.25,
                }}
              >
                <Layers fontSize="inherit" sx={{ color: "text.disabled" }} />
                {trace.spans.length}
              </Box>

              {/* Priority */}
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 0.25,
                }}
              >
                <Flag
                  fontSize="inherit"
                  sx={{
                    color: getPriorityColor(priority),
                  }}
                />
                {priority}
              </Box>

              {/* Token Usage */}
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 0.25,
                }}
              >
                <Token fontSize="inherit" sx={{ color: "text.disabled" }} />
                {totalTokens}
              </Box>
            </Typography>
          </Box>
        </TableCell>
        <TableCell>
          <StatusChip status={status} />
        </TableCell>
        <TableCell>
          {errorType && errorType !== "none" ? (
            <ErrorTypeChip errorType={errorType} />
          ) : (
            <Typography variant="body2" sx={{ color: "text.disabled" }}>
              —
            </Typography>
          )}
        </TableCell>
        <TableCell>
          <Typography
            variant="body2"
            sx={{
              fontFamily: "monospace",
            }}
          >
            {duration}s
          </Typography>
        </TableCell>
        <TableCell>
          <Typography
            variant="body2"
            sx={{
              fontFamily: "monospace",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {trace.trace_id}
          </Typography>
        </TableCell>
        <TableCell>
          <ConfidenceIndicator
            confidence={confidence}
            status={suggestion_status}
            isAnalyzing={isAnalyzing}
          />
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell sx={{ p: 0, border: 0 }} colSpan={8}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ bgcolor: "action.hover" }}>
              <SpanRows spans={trace.spans} traceId={trace.trace_id} />
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </React.Fragment>
  );
};

interface TracesTableProps {
  traces: Trace[];
  loading?: boolean;
}

const TracesTable: React.FC<TracesTableProps> = ({ traces, loading }) => (
  <Table sx={{ width: "100%", tableLayout: "fixed" }}>
    <TableHead>
      <TableRow
        sx={{
          "& th": {
            fontWeight: 700,
            color: "text.secondary",
            fontSize: "0.75rem",
            textTransform: "uppercase",
            letterSpacing: 0.5,
          },
        }}
      >
        <TableCell sx={{ width: "5%" }} />
        <TableCell sx={{ width: "15%" }}>Timestamp</TableCell>
        <TableCell sx={{ width: "15%" }}>Details</TableCell>
        <TableCell sx={{ width: "13%" }}>Status</TableCell>
        <TableCell sx={{ width: "13%" }}>Error Type</TableCell>
        <TableCell sx={{ width: "10%" }}>Duration</TableCell>
        <TableCell sx={{ width: "15%" }}>Trace ID</TableCell>
        <TableCell sx={{ width: "14%" }}>AI Confidence</TableCell>
      </TableRow>
    </TableHead>
    <TableBody>
      {loading ? (
        Array.from({ length: 10 }).map((_, i) => (
          <TableRow key={i}>
            {Array.from({ length: 8 }).map((_, j) => (
              <TableCell key={j}>
                <Skeleton sx={{ my: 1.75 }} />
              </TableCell>
            ))}
          </TableRow>
        ))
      ) : traces.length === 0 ? (
        <TableRow>
          <TableCell colSpan={8} align="center" sx={{ py: 6 }}>
            <Typography variant="body2" color="text.disabled">
              No recent activity.
            </Typography>
          </TableCell>
        </TableRow>
      ) : (
        traces.map((trace) => <TraceRow key={trace.trace_id} trace={trace} />)
      )}
    </TableBody>
  </Table>
);

export default TracesTable;