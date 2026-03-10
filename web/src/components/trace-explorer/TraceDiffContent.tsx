import React, { useState } from "react";
import { Box, Chip, Typography } from "@mui/material";
import { CheckCircleOutline, ErrorOutline, RemoveCircleOutline } from "@mui/icons-material";
import type { Span, Trace } from "../../types/trace";
import {
  spanGetType,
  spanGetToolName,
  spanHasError,
  spanGetUsage,
  spanGetInput,
  spanGetOutput,
  spanGetSystemPrompt,
  spanGetDuration,
} from "../utils/spanUtils";
import { parseLLMContent, formatDuration } from "../utils/utils";
import SpanContent from "./SpanContent";
import TokenUsageBar from "./TokenUsageBar";

interface TraceDiffContentProps {
  traceA: Trace;
  traceB: Trace;
  labelA: string;
  labelB: string;
}

type RowStatus = "match" | "mismatch" | "unique";

interface AlignedRow {
  key: string;
  spanA: Span | null;
  spanB: Span | null;
  depthA: number;
  depthB: number;
  status: RowStatus;
}

// Flatten spans
const flattenSpans = (spans: Span[]): { span: Span; depth: number }[] => {
  const seen = new Set<string>();
  const unique = spans.filter((span) => {
    if (seen.has(span.span_id)) return false;
    seen.add(span.span_id);
    return true;
  });
  const spansByParent = new Map<string | null, Span[]>();
  unique.forEach((span) => {
    const siblings = spansByParent.get(span.parent_id) ?? [];
    siblings.push(span);
    spansByParent.set(span.parent_id, siblings);
  });
  const ordered: { span: Span; depth: number }[] = [];
  const traverse = (parentId: string | null, depth: number) => {
    (spansByParent.get(parentId) ?? []).forEach((span) => {
      ordered.push({ span, depth });
      traverse(span.span_id, depth + 1);
    });
  };
  traverse(null, 0);
  return ordered;
};

// Normalize tool name for comparison by stripping error indicators
const normalizeToolName = (name: string) =>
  name.replace(/\s*\(ERROR\)/gi, "").replace(/\s*with Error/gi, "").trim();

// Align spans from two traces
const alignSpans = (spansA: Span[], spansB: Span[]): AlignedRow[] => {
  const flatA = flattenSpans(spansA);
  const flatB = flattenSpans(spansB);
  const rows: AlignedRow[] = [];
  const usedB = new Set<string>();

  flatA.forEach(({ span: spanA, depth: depthA }) => {
    const matchEntry = flatB.find((e) => !usedB.has(e.span.span_id) && spanGetType(e.span) === spanGetType(spanA));
    if (matchEntry) {
      usedB.add(matchEntry.span.span_id);
      const isMismatch =
        spanHasError(spanA) !== spanHasError(matchEntry.span) ||
        (spanGetType(spanA) === "tool_execution" &&
          normalizeToolName(spanGetToolName(spanA)) !== normalizeToolName(spanGetToolName(matchEntry.span)));
      rows.push({
        key: `a-${spanA.span_id}`,
        spanA,
        spanB: matchEntry.span,
        depthA,
        depthB: matchEntry.depth,
        status: isMismatch ? "mismatch" : "match",
      });
    } else {
      rows.push({ key: `a-${spanA.span_id}`, spanA, spanB: null, depthA, depthB: depthA, status: "unique" });
    }
  });

  flatB
    .filter((e) => !usedB.has(e.span.span_id))
    .forEach(({ span: spanB, depth: depthB }) => {
      rows.push({ key: `b-${spanB.span_id}`, spanA: null, spanB, depthA: depthB, depthB, status: "unique" });
    });

  return rows;
};

const STATUS_CONFIG: Record<
  RowStatus,
  { bg: string; border: string; label: string; labelColor: string }
> = {
  match: {
    bg: "rgba(34,197,94,0.05)",
    border: "success.light",
    label: "MATCH",
    labelColor: "success.main",
  },
  mismatch: {
    bg: "rgba(211,47,47,0.05)",
    border: "error.light",
    label: "MISMATCH",
    labelColor: "error.main",
  },
  unique: {
    bg: "rgba(0,0,0,0.03)",
    border: "divider",
    label: "UNIQUE",
    labelColor: "text.secondary",
  },
};

// Span when row is expanded
const SpanFields: React.FC<{ span: Span; trace: Trace }> = ({ span, trace }) => {
  const toolName = spanGetToolName(span);
  const hasError = spanHasError(span);
  const usage = spanGetUsage(span);
  const input = spanGetInput(span);
  const output = spanGetOutput(span);
  const systemPrompt = spanGetSystemPrompt(span, trace);

  return (
    <Box sx={{ p: 2 }}>
      {systemPrompt && (
        <SpanContent
          title="System Prompt"
          subtitle="System"
          content={systemPrompt}
          hasError={hasError}
        />
      )}
      {toolName && <SpanContent title="Tool" subtitle="Tool" content={toolName} hasError={hasError} />}
      {input && (
        (() => {
          const parsed = parseLLMContent(input);
          return parsed ? (
            <SpanContent title="Input" subtitle={parsed.subtitle} content={parsed.content} hasError={hasError} />
          ) : (
            <SpanContent title="Input" subtitle="AI" content={input} hasError={hasError} />
          );
        })()
      )}
      {output && <SpanContent title="Output" subtitle="AI" content={output} hasError={hasError} />}
      {usage && <TokenUsageBar usage={usage} hasError={hasError} />}
    </Box>
  );
};

// Span difference row
const SpanCell: React.FC<{ span: Span | null; depth: number; label: string; labelColor: string }> = ({
  span,
  depth,
  label,
  labelColor,
}) => {
if (!span) {
    return (
      <Box
        sx={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          gap: 1,
          pl: 2 + depth * 2,
          pr: 2,
          py: 1.25,
          opacity: 0.35,
          height: "100%",
        }}
      >
        <RemoveCircleOutline sx={{ fontSize: 16 }} />
        <Typography variant="caption" sx={{ fontStyle: "italic" }}>
          No match
        </Typography>
      </Box>
    );
  }

  const hasError = spanHasError(span);
  const type = spanGetType(span);

  return (
    <Box
      sx={{ flex: 1, display: "flex", alignItems: "center", gap: 1, pl: 2 + depth * 2, pr: 2, py: 1.25, minWidth: 0 }}
    >
      {hasError ? (
        <ErrorOutline sx={{ fontSize: 16, color: "error.main", flexShrink: 0 }} />
      ) : (
        <CheckCircleOutline sx={{ fontSize: 16, color: "success.main", flexShrink: 0 }} />
      )}
      <Box sx={{ minWidth: 0 }}>
        <Typography
          variant="caption"
          sx={{
            fontWeight: 600,
            display: "block",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {span.name}
        </Typography>
        <Typography variant="caption" color="text.disabled">
          {type} - {formatDuration(parseFloat(spanGetDuration(span)))}
        </Typography>
      </Box>
      <Typography
        variant="caption"
        sx={{ ml: "auto", flexShrink: 0, color: labelColor, fontWeight: 600, fontSize: "0.75rem" }}
      >
        {label}
      </Typography>
    </Box>
  );
};

// Chip showing summary counts
const SummaryChip: React.FC<{ status: RowStatus; count: number }> = ({ status, count }) => {
  const config = STATUS_CONFIG[status];
  return (
    <Chip
      variant="outlined"
      size="medium"
      label={
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
          <Typography variant="caption" sx={{ fontWeight: 700, color: config.labelColor }}>
            {count}
          </Typography>
          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            {config.label.charAt(0) + config.label.slice(1).toLowerCase()}
          </Typography>
        </Box>
      }
      sx={{ bgcolor: config.bg, borderColor: config.border, borderRadius: 2 }}
    />
  );
};

const TraceDiffContent: React.FC<TraceDiffContentProps> = ({ traceA, traceB, labelA, labelB }) => {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set());

  const rows = alignSpans(traceA.spans, traceB.spans);

  const counts = rows.reduce(
    (acc, row) => ({ ...acc, [row.status]: acc[row.status] + 1 }),
    { match: 0, mismatch: 0, unique: 0 } as Record<RowStatus, number>
  );

  const toggleRow = (key: string) => {
    setExpandedKeys((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0, overflow: "hidden", m: 2, border: 1, borderColor: "divider", borderRadius: 2 }}>
      <Box sx={{ flexShrink: 0 }}>

        {/* Summary counts */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            px: 2,
            py: 1.5,
            borderBottom: 1,
            borderColor: "divider",
          }}
        >
          <SummaryChip status="match" count={counts.match} />
          <SummaryChip status="mismatch" count={counts.mismatch} />
          <SummaryChip status="unique" count={counts.unique} />
        </Box>

      </Box>

      {/* Compare spans */}
      <Box sx={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
        {/* Column headers */}
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            borderBottom: 1,
            borderColor: "divider",
            position: "sticky",
            top: 0,
            zIndex: 1,
            bgcolor: "background.paper",
          }}
        >
          <Box sx={{ borderRight: 1, borderColor: "divider", px: 2, py: 1 }}>
            <Typography variant="caption" sx={{ fontWeight: 700, color: "text.secondary" }}>
              {labelA}
            </Typography>
          </Box>
          <Box sx={{ px: 2, py: 1 }}>
            <Typography variant="caption" sx={{ fontWeight: 700, color: "text.secondary" }}>
              {labelB}
            </Typography>
          </Box>
        </Box>
        {rows.map((row) => {
          const config = STATUS_CONFIG[row.status];
          const isExpanded = expandedKeys.has(row.key);

          return (
            <Box key={row.key}>
              {/* Row */}
              <Box
                onClick={() => toggleRow(row.key)}
                sx={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  bgcolor: isExpanded ? config.bg : "transparent",
                  cursor: "pointer",
                  transition: "background 0.15s ease",
                  "&:hover": { bgcolor: config.bg },
                }}
              >
                <Box sx={{ borderRight: 1, borderBottom: 1, borderColor: "divider" }}>
                  <SpanCell span={row.spanA} depth={row.depthA} label={config.label} labelColor={config.labelColor} />
                </Box>
                <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
                  <SpanCell span={row.spanB} depth={row.depthB} label={config.label} labelColor={config.labelColor} />
                </Box>
              </Box>

              {/* Expanded detail */}
              {isExpanded && (
                <Box
                  sx={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    bgcolor: config.bg,
                    borderBottom: 1,
                    borderColor: "divider",
                  }}
                >
                  <Box sx={{ borderRight: 1, borderColor: "divider", bgcolor: "action.hover" }}>
                    {row.spanA && <SpanFields span={row.spanA} trace={traceA} />}
                  </Box>
                  <Box sx={{ bgcolor: "action.hover" }}>
                    {row.spanB && <SpanFields span={row.spanB} trace={traceB} />}
                  </Box>
                </Box>
              )}
            </Box>
          );
        })}
      </Box>
    </Box>
  );
};

export default TraceDiffContent;