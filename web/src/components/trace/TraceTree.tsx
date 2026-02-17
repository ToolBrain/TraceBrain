import React, { useState } from "react";
import { Box, Typography, IconButton, Button } from "@mui/material";
import {
  ChevronRight,
  ExpandMore,
  ErrorOutline,
  CheckCircleOutline,
  Schedule,
  ThumbUpOutlined,
  AutoAwesome,
  AccountTree,
} from "@mui/icons-material";
import type { Span, Trace } from "../../types/trace";
import TraceModal from "./TraceModal";
import { useParams } from "react-router-dom";
import { spanGetDuration, spanHasError } from "../utils/spanUtils";
import { traceGetLatestFeedback } from "../utils/traceUtils";

interface TraceTreeProps {
  traces: Trace[];
  expandedNodes: Set<string>;
  selectedId: string | null;
  selectedType: "trace" | "span";
  onToggleExpand: (id: string) => void;
  onSelect: (id: string, type: "trace" | "span") => void;
}

const TraceTree: React.FC<TraceTreeProps> = ({
  traces,
  expandedNodes,
  selectedId,
  selectedType,
  onToggleExpand,
  onSelect,
}) => {
  const [openModal, setOpenModal] = useState<"feedback" | "evaluate" | null>(
    null,
  );
  const { id } = useParams<{ id: string }>() as { id: string };

  const spansByTrace = React.useMemo(() => {
    const map = new Map<string, Map<string | null, Span[]>>();
    traces.forEach((t) => {
      const spansByParent = new Map<string | null, Span[]>();
      t.spans.forEach((span) => {
        const siblings = spansByParent.get(span.parent_id) || [];
        siblings.push(span);
        spansByParent.set(span.parent_id, siblings);
      });
      map.set(t.trace_id, spansByParent);
    });
    return map;
  }, [traces]);

  const SpanRow = ({
    span,
    depth,
    isLast,
    spansByParent,
  }: {
    span: Span;
    depth: number;
    isLast?: boolean;
    spansByParent: Map<string | null, Span[]>;
  }) => {
    const children = spansByParent.get(span.span_id) || [];
    const isExpanded = expandedNodes.has(span.span_id);
    const isSelected = selectedType === "span" && selectedId === span.span_id;
    const hasError = spanHasError(span);

    return (
      <>
        <Box
          onClick={() => onSelect(span.span_id, "span")}
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
                onToggleExpand(span.span_id);
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
          const spansByParent = spansByTrace.get(t.trace_id)!;
          const isTraceExpanded = expandedNodes.has(t.trace_id);
          const isTraceSelected =
            selectedType === "trace" && selectedId === t.trace_id;
          const rootSpans = spansByParent.get(null) || [];

          return (
            <React.Fragment key={t.trace_id}>
              <Box
                onClick={() => onSelect(t.trace_id, "trace")}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  py: 1,
                  px: 1.5,
                  cursor: "pointer",
                  bgcolor: isTraceSelected ? "primary.50" : "transparent",
                  borderLeft: "0.125rem solid",
                  borderLeftColor: isTraceSelected
                    ? "primary.main"
                    : "transparent",
                  "&:hover": {
                    bgcolor: isTraceSelected ? "primary.50" : "action.hover",
                  },
                }}
              >
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    onToggleExpand(t.trace_id);
                  }}
                  sx={{ mr: 1, p: 0 }}
                >
                  {isTraceExpanded ? (
                    <ExpandMore fontSize="small" />
                  ) : (
                    <ChevronRight fontSize="small" />
                  )}
                </IconButton>

                <AccountTree fontSize="small" color="primary" />
              </Box>

              {isTraceExpanded &&
                rootSpans.map((span, idx) => (
                  <SpanRow
                    key={span.span_id}
                    span={span}
                    depth={1}
                    isLast={idx === rootSpans.length - 1}
                    spansByParent={spansByParent}
                  />
                ))}
            </React.Fragment>
          );
        })}
      </Box>

      <Box
        sx={{
          p: 1.5,
          borderTop: 1,
          borderColor: "divider",
          display: "flex",
          gap: 1,
          justifyContent: "end",
          flexWrap: "wrap",
        }}
      >
        <Button
          variant="outlined"
          size="medium"
          startIcon={<ThumbUpOutlined fontSize="small" />}
          onClick={() => setOpenModal("feedback")}
        >
          Feedback
        </Button>
        <Button
          variant="outlined"
          size="medium"
          startIcon={<AutoAwesome fontSize="small" />}
          onClick={() => setOpenModal("evaluate")}
        >
          AI Evaluate
        </Button>
      </Box>

      {openModal && (
        <TraceModal
          open={true}
          onClose={() => setOpenModal(null)}
          type={openModal}
          id={id}
          feedback={traceGetLatestFeedback(traces[0])}
        />
      )}
    </Box>
  );
};

export default TraceTree;
