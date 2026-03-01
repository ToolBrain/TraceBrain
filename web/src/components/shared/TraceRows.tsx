import React from "react";
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableRow,
  Typography,
} from "@mui/material";
import { Flag, Layers, Token } from "@mui/icons-material";
import type { Trace } from "../../types/trace";
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
import { useNavigate } from "react-router-dom";

interface TraceRowsProps {
  traces: Trace[];
  episodeId: string;
}

const TraceRows: React.FC<TraceRowsProps> = ({ traces, episodeId }) => {
  const nav = useNavigate();

  const handleTraceClick = (traceId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    nav(`/trace/${episodeId}?type=episode&trace=${traceId}`);
  };
  return (
    <Table size="small" sx={{ width: "100%", tableLayout: "fixed" }}>
      <colgroup>
        <col style={{ width: "5%" }} />
        <col style={{ width: "15%" }} />
        <col style={{ width: "15%" }} />
        <col style={{ width: "13%" }} />
        <col style={{ width: "13%" }} />
        <col style={{ width: "10%" }} />
        <col style={{ width: "15%" }} />
        <col style={{ width: "14%" }} />
      </colgroup>
      <TableBody>
        {traces.map((trace) => {
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
            <TableRow
              key={trace.trace_id}
              hover
              onClick={(e) => handleTraceClick(trace.trace_id, e)}
              sx={{ cursor: "pointer", "& td": { py: 2 } }}
            >
              <TableCell />
              <TableCell>
                <Typography
                  variant="body2"
                  sx={{
                    fontFamily: "monospace",
                    fontSize: "0.75rem",
                    color: "text.secondary",
                  }}
                >
                  {formatDateTime(startTime)}
                </Typography>
              </TableCell>
              <TableCell>
                <Box
                  sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}
                >
                  <TypeChip type="trace" secondary />

                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ display: "flex", alignItems: "center", gap: 1 }}
                  >
                    {/* Span Count */}
                    <Box
                      sx={{ display: "flex", alignItems: "center", gap: 0.25 }}
                    >
                      <Layers
                        fontSize="inherit"
                        sx={{ color: "text.disabled" }}
                      />
                      {trace.spans.length}
                    </Box>

                    {/* Priority */}
                    <Box
                      sx={{ display: "flex", alignItems: "center", gap: 0.25 }}
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
                      sx={{ display: "flex", alignItems: "center", gap: 0.25 }}
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
                <StatusChip status={status} secondary />
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
                    fontSize: "0.75rem",
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
                    fontSize: "0.75rem",
                    color: "text.secondary",
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
          );
        })}
      </TableBody>
    </Table>
  );
};

export default TraceRows;