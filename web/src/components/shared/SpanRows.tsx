import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableRow,
  Typography,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import type { Span } from "../../types/trace";
import { formatDateTime } from "../utils/utils";
import {
  spanGetDuration,
  spanGetOutput,
  spanHasError,
} from "../utils/spanUtils";
import StatusChip from "./StatusChip";

interface SpanRowsProps {
  spans: Span[];
  traceId: string;
}

const SpanRows: React.FC<SpanRowsProps> = ({ spans, traceId }) => {
  const nav = useNavigate();

  const handleSpanClick = (spanId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    nav(`/trace/${traceId}?span=${spanId}`);
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
        {spans.map((span) => {
          const spanDuration = spanGetDuration(span);
          const spanStatus: "success" | "error" = spanHasError(span)
            ? "error"
            : "success";
          return (
            <TableRow
              key={span.span_id}
              hover
              onClick={(e) => handleSpanClick(span.span_id, e)}
              sx={{ cursor: "pointer", "& td": { py: 2 } }}
            >
              <TableCell />
              <TableCell sx={{ fontFamily: "monospace" }}>
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
                <Typography variant="body2" sx={{ fontSize: "0.875rem" }}>
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
                <StatusChip status={spanStatus} secondary />
              </TableCell>
              <TableCell />
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
              <TableCell sx={{ fontFamily: "monospace" }}>
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
              <TableCell />
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
};

export default SpanRows;