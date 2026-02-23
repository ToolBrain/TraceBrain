import React from "react";
import { Box, Typography, IconButton } from "@mui/material";
import {
  ChevronRight,
  ExpandMore,
  ErrorOutline,
  CheckCircleOutline,
  Schedule,
} from "@mui/icons-material";
import type { Span, Trace } from "../../types/trace";
import { spanGetDuration, spanHasError } from "../utils/spanUtils";

interface SelectedSpan {
  traceId: string;
  spanId: string;
}

interface TraceTreeProps {
  traces: Trace[];
  expandedNodes: Set<string>;
  selectedSpan: SelectedSpan | null;
  onToggleExpand: (traceId: string, spanId: string) => void;
  onSelectSpan: (span: SelectedSpan) => void;
}

const TraceTree: React.FC<TraceTreeProps> = ({
  traces,
  expandedNodes,
  selectedSpan,
  onToggleExpand,
  onSelectSpan,
}) => {
  const SpanRow = ({
    span,
    traceId,
    depth,
    isLast,
    spansByParent,
  }: {
    span: Span;
    traceId: string;
    depth: number;
    isLast?: boolean;
    spansByParent: Map<string | null, Span[]>;
  }) => {
    const children = spansByParent.get(span.span_id) || [];
    const isExpanded = expandedNodes.has(`${traceId}:${span.span_id}`);
    const isSelected = selectedSpan?.traceId === traceId && selectedSpan?.spanId === span.span_id;
    const hasError = spanHasError(span);

    return (
      <>
        <Box
          onClick={() => onSelectSpan({ traceId, spanId: span.span_id })}
          sx={{
            display: "flex",
            alignItems: "center",
            py: 1,
            px: 1.5,
            position: "relative",
            cursor: "pointer",
            bgcolor: isSelected ? "primary.50" : "transparent",
            borderLeft: "0.125rem solid",
            borderLeftColor: isSelected ? "primary.main" : "transparent",
            "&:hover": { bgcolor: isSelected ? "primary.50" : "action.hover" },
          }}
        >
          {depth > 0 && (
            <>
              <Box
                sx={{
                  position: "absolute",
                  left: `${depth * 1.5}rem`,
                  top: 0,
                  bottom: isLast ? "50%" : 0,
                  width: "0.0625rem",
                  bgcolor: "divider",
                }}
              />
              <Box
                sx={{
                  position: "absolute",
                  left: `${depth * 1.5}rem`,
                  top: "50%",
                  width: "0.75rem",
                  height: "0.0625rem",
                  bgcolor: "divider",
                }}
              />
            </>
          )}

          <Box sx={{ width: `${depth * 1.5}rem` }} />

          {children.length > 0 ? (
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onToggleExpand(traceId, span.span_id);
              }}
              sx={{ mr: 1, p: 0 }}
            >
              {isExpanded ? (
                <ExpandMore fontSize="small" />
              ) : (
                <ChevronRight fontSize="small" />
              )}
            </IconButton>
          ) : (
            <Box sx={{ width: "1.25rem", mr: 1 }} />
          )}

          {hasError ? (
            <ErrorOutline fontSize="small" color="error" />
          ) : (
            <CheckCircleOutline fontSize="small" color="success" />
          )}

          <Typography variant="body2" sx={{ fontWeight: 500, ml: 1, flex: 1 }}>
            {span.name}
          </Typography>

          <Schedule fontSize="small" sx={{ fontSize: "1rem", mr: 0.5 }} />
          <Typography variant="caption" color="text.secondary">
            {spanGetDuration(span)}
          </Typography>
        </Box>

        {isExpanded &&
          children.map((child, idx) => (
            <SpanRow
              key={child.span_id}
              span={child}
              traceId={traceId}
              depth={depth + 1}
              isLast={idx === children.length - 1}
              spansByParent={spansByParent}
            />
          ))}
      </>
    );
  };

  return (
    <Box
      sx={{
        width: "25%",
        bgcolor: "background.paper",
        borderRight: 1,
        borderColor: "divider",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: "divider",
          bgcolor: "background.default",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Typography variant="h5">Traces</Typography>
      </Box>

      <Box sx={{ flex: 1, overflowY: "auto" }}>
        {traces.map((t) => {
          const spansByParent = new Map<string | null, Span[]>();
          t.spans.forEach((span) => {
            const siblings = spansByParent.get(span.parent_id) || [];
            siblings.push(span);
            spansByParent.set(span.parent_id, siblings);
          });

          return (
            <React.Fragment key={t.trace_id}>
              {spansByParent
                .get(null)
                ?.map((span, idx, arr) => (
                  <SpanRow
                    key={span.span_id}
                    span={span}
                    traceId={t.trace_id}
                    depth={0}
                    isLast={idx === arr.length - 1}
                    spansByParent={spansByParent}
                  />
                ))}
            </React.Fragment>
          );
        })}
      </Box>
    </Box>
  );
};

export default TraceTree;