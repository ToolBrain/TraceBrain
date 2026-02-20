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
  Token,
} from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import type { Trace } from "../../types/trace";
import React from "react";
import {
  spanGetDuration,
  spanGetOutput,
  spanHasError,
} from "../utils/spanUtils";
import StatusChip, {
  ALLOWED_STATUSES,
  type ChipStatus,
} from "../shared/StatusChip";
import {
  traceGetDuration,
  traceGetEvaluation,
  traceGetPriority,
  traceGetStartTime,
  traceGetStatus,
  traceGetTotalTokens,
} from "../utils/traceUtils";
import ConfidenceIndicator from "./ConfidenceIndicator";
import { formatDateTime, getPriorityColor } from "../utils/utils";
import TypeChip from "../shared/TypeChip";

interface TraceListProps {
  traces: Trace[];
}

const TraceList: React.FC<TraceListProps> = ({ traces }) => {
  const nav = useNavigate();
  const [expandedTraces, setExpandedTraces] = useState<Set<string>>(new Set());

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
            <TableCell sx={{ width: "12%", fontWeight: 600 }}>
              Details
            </TableCell>
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
              <TableCell
                colSpan={7}
                sx={{ textAlign: "center", py: 4, color: "text.secondary" }}
              >
                No traces found.
              </TableCell>
            </TableRow>
          ) : (
            traces.map((trace) => {
              const isExpanded = expandedTraces.has(trace.trace_id);
              const startTime = traceGetStartTime(trace);
              const duration = traceGetDuration(trace);
              const status = getTraceStatus(trace);
              const priority = traceGetPriority(trace);
              const totalTokens = traceGetTotalTokens(trace) ?? "N/A";

              const evaluation = traceGetEvaluation(trace);
              const confidence = evaluation?.confidence;
              const suggestion_status = evaluation?.status;
              const isAnalyzing = !evaluation;

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
                            <Layers
                              fontSize="inherit"
                              sx={{ color: "text.disabled" }}
                            />
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
                            <Token
                              fontSize="inherit"
                              sx={{ color: "text.disabled" }}
                            />
                            {totalTokens}
                          </Box>
                        </Typography>
                      </Box>
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
                        isAnalyzing={isAnalyzing}
                      />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ p: 0, border: 0 }} colSpan={7}>
                      <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                        <Box sx={{ bgcolor: "action.hover" }}>
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
                                const spanDuration = spanGetDuration(span);
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
