import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Box,
  Typography,
  Paper,
  Collapse,
} from "@mui/material";
import {
  Flag,
  KeyboardArrowDown,
  KeyboardArrowRight,
  Layers,
} from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import type { Trace } from "../../types/trace";
import React from "react";
import { spanGetOutput, spanHasError } from "../utils/spanUtils";
import StatusChip, { ALLOWED_STATUSES, type ChipStatus } from "./StatusChip";
import { traceGetPriority, traceGetStatus } from "../utils/traceUtils";
import ConfidenceIndicator from "./ConfidenceIndicator";

interface TraceListProps {
  traces: Trace[];
}

const TraceList: React.FC<TraceListProps> = ({ traces }) => {
  const nav = useNavigate();
  const [expandedTraces, setExpandedTraces] = useState<Set<string>>(new Set());

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString("en-GB", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  };

  const getTraceStartTime = (trace: Trace): string => {
    const startTimes = trace.spans.map((span) =>
      new Date(span.start_time).getTime(),
    );
    return new Date(Math.min(...startTimes)).toISOString();
  };

  const getTraceDuration = (trace: Trace): number => {
    const spanTimes = trace.spans.map((span) => ({
      start: new Date(span.start_time).getTime(),
      end: new Date(span.end_time).getTime(),
    }));
    const start = Math.min(...spanTimes.map((t) => t.start));
    const end = Math.max(...spanTimes.map((t) => t.end));
    return (end - start) / 1000;
  };

  const getTraceStatus = (trace: Trace): ChipStatus => {
    const status = traceGetStatus(trace);

    if (!status) return "running";

    return (ALLOWED_STATUSES as readonly string[]).includes(status)
      ? (status as ChipStatus)
      : "running";
  };

  const toggleTrace = (traceId: string) => {
    setExpandedTraces((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(traceId)) {
        newSet.delete(traceId);
      } else {
        newSet.add(traceId);
      }
      return newSet;
    });
  };

  const handleSpanClick = (
    traceId: string,
    spanId: string,
    e: React.MouseEvent,
  ) => {
    e.stopPropagation();
    nav(`/trace/${traceId}?span=${spanId}`);
  };

  const handleTraceClick = (traceId: string) => {
    nav(`/trace/${traceId}`);
  };

  return (
    <TableContainer
      component={Paper}
      sx={{
        border: "1px solid",
        borderColor: "divider",
        height: "100%",
      }}
    >
      <Table>
        <TableHead>
          <TableRow
            sx={{
              bgcolor: "background.default",
              position: "sticky",
              top: 0,
              zIndex: 1,
            }}
          >
            <TableCell sx={{ width: "2%", fontWeight: 600 }}></TableCell>
            <TableCell sx={{ width: "16%", fontWeight: 600 }}>
              Timestamp
            </TableCell>
            <TableCell sx={{ width: "12%", fontWeight: 600 }}>Type</TableCell>
            <TableCell sx={{ width: "15%", fontWeight: 600 }}>Status</TableCell>
            <TableCell sx={{ width: "15%", fontWeight: 600 }}>
              Duration
            </TableCell>
            <TableCell sx={{ width: "25%", fontWeight: 600 }}>
              Trace ID
            </TableCell>
            <TableCell sx={{ width: "15%", fontWeight: 600 }}>
              AI Confidence
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {traces.length === 0 ? (
            <TableRow>
              <TableCell colSpan={7} sx={{ textAlign: "center", py: 4 }}>
                No traces found.
              </TableCell>
            </TableRow>
          ) : (
            traces.map((trace) => {
              const isExpanded = expandedTraces.has(trace.trace_id);
              const startTime = getTraceStartTime(trace);
              const duration = getTraceDuration(trace);
              const status = getTraceStatus(trace);
              const priority = traceGetPriority(trace);

              const confidence = 1;
              const suggestion_status = "pending_review";

              return (
                <React.Fragment key={trace.trace_id}>
                  <TableRow
                    hover
                    sx={{
                      cursor: "pointer",
                      "&:hover": { bgcolor: "action.hover" },
                      "& > td": { p: 2 },
                      "& > td:first-of-type": { p: 1 },
                    }}
                    onClick={() => handleTraceClick(trace.trace_id)}
                  >
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleTrace(trace.trace_id);
                        }}
                      >
                        {isExpanded ? (
                          <KeyboardArrowDown />
                        ) : (
                          <KeyboardArrowRight />
                        )}
                      </IconButton>
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="body2"
                        sx={{ fontFamily: "monospace", fontSize: "0.875rem" }}
                      >
                        {formatDateTime(startTime)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">Trace</Typography>
                      <Typography variant="caption" color="text.secondary">
                        <Layers
                          fontSize="inherit"
                          sx={{ color: "text.secondary" }}
                        />
                        {trace.spans.length}
                        {"\t"}
                        <Flag
                          fontSize="inherit"
                          sx={{
                            color:
                              priority >= 4
                                ? "error.main" // (4-5) High priority
                                : priority >= 3
                                  ? "warning.main" // (3) Medium priority
                                  : "error.light", // (1-2) Low priority
                          }}
                        />
                        {priority}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <StatusChip status={status} />
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="body2"
                        sx={{ fontFamily: "monospace" }}
                      >
                        {duration.toFixed(2)}s
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography
                        variant="body2"
                        sx={{
                          fontFamily: "monospace",
                          fontSize: "0.75rem",
                          color: "text.secondary",
                        }}
                      >
                        {trace.trace_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <ConfidenceIndicator
                        confidence={confidence}
                        status={suggestion_status}
                      />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ p: 0, border: 0 }} colSpan={7}>
                      <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                        <Box sx={{ bgcolor: "action.hover", py: 1 }}>
                          <Table
                            size="small"
                            sx={{ width: "100%", tableLayout: "fixed" }}
                          >
                            <colgroup>
                              <col style={{ width: "2%" }} />
                              <col style={{ width: "16%" }} />
                              <col style={{ width: "12%" }} />
                              <col style={{ width: "15%" }} />
                              <col style={{ width: "15%" }} />
                              <col style={{ width: "25%" }} />
                              <col style={{ width: "15%" }} />
                            </colgroup>
                            <TableBody>
                              {trace.spans.map((span) => {
                                const spanDuration = (
                                  (new Date(span.end_time).getTime() -
                                    new Date(span.start_time).getTime()) /
                                  1000
                                ).toFixed(2);
                                const spanStatus: "success" | "error" =
                                  spanHasError(span) ? "error" : "success";

                                return (
                                  <TableRow
                                    key={span.span_id}
                                    onClick={(e) =>
                                      handleSpanClick(
                                        trace.trace_id,
                                        span.span_id,
                                        e,
                                      )
                                    }
                                    sx={{
                                      cursor: "pointer",
                                      "&:hover": { bgcolor: "action.hover" },
                                      "& > td": { p: 2 },
                                      "& > td:first-of-type": { p: 1 },
                                    }}
                                  >
                                    <TableCell></TableCell>
                                    <TableCell>
                                      <Typography
                                        variant="body2"
                                        sx={{
                                          fontFamily: "monospace",
                                          fontSize: "0.75rem",
                                          color: "text.secondary",
                                        }}
                                      >
                                        {formatDateTime(span.start_time)}
                                      </Typography>
                                    </TableCell>
                                    <TableCell>
                                      <Typography
                                        variant="body2"
                                        sx={{ fontSize: "0.875rem" }}
                                      >
                                        {span.name}
                                      </Typography>
                                      <Typography
                                        variant="caption"
                                        color="text.secondary"
                                        sx={{
                                          display: "block",
                                          overflow: "hidden",
                                          textOverflow: "ellipsis",
                                          whiteSpace: "nowrap",
                                        }}
                                      >
                                        {spanGetOutput(span)}
                                      </Typography>
                                    </TableCell>
                                    <TableCell>
                                      <StatusChip
                                        status={spanStatus}
                                        secondary
                                      />
                                    </TableCell>
                                    <TableCell>
                                      <Typography
                                        variant="body2"
                                        sx={{
                                          fontFamily: "monospace",
                                          fontSize: "0.75rem",
                                        }}
                                      >
                                        {spanDuration}s
                                      </Typography>
                                    </TableCell>
                                    <TableCell>
                                      <Typography
                                        variant="body2"
                                        sx={{
                                          fontFamily: "monospace",
                                          fontSize: "0.75rem",
                                          color: "text.secondary",
                                          overflow: "hidden",
                                          textOverflow: "ellipsis",
                                          whiteSpace: "nowrap",
                                        }}
                                      >
                                        {span.span_id}
                                      </Typography>
                                    </TableCell>
                                    <TableCell></TableCell>
                                  </TableRow>
                                );
                              })}
                            </TableBody>
                          </Table>
                        </Box>
                      </Collapse>
                    </TableCell>
                  </TableRow>
                </React.Fragment>
              );
            })
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default TraceList;
