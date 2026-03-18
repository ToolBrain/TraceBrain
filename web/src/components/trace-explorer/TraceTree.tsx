import React from "react";
import { Box, Typography, IconButton, Button, useTheme } from "@mui/material";
import {
  ChevronRight,
  ExpandMore,
  ErrorOutline,
  CheckCircleOutline,
} from "@mui/icons-material";
import type { Span, Trace } from "../../types/trace";
import { spanGetDuration, spanHasError } from "../utils/spanUtils";
import { formatDuration } from "../utils/utils";
import { traceGetEpisodeId } from "../utils/traceUtils";
import { useNavigate, useSearchParams } from "react-router-dom";

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

interface SpanNodeProps {
  span: Span;
  traceId: string;
  depth: number;
  isLast?: boolean;
  spansByParent: Map<string | null, Span[]>;
  ancestorLines: number[];
  expandedNodes: Set<string>;
  selectedSpan: SelectedSpan | null;
  onToggleExpand: (traceId: string, spanId: string) => void;
  onSelectSpan: (span: SelectedSpan) => void;
}

const lineWidth = "0.075rem";
const branchWidth = "0.75rem";
const DEPTH_CAP = 4;

const SpanNode: React.FC<SpanNodeProps> = ({
  span,
  traceId,
  depth,
  isLast,
  spansByParent,
  ancestorLines,
  expandedNodes,
  selectedSpan,
  onToggleExpand,
  onSelectSpan,
}) => {
  const theme = useTheme();
  const connectorColor = theme.palette.grey[600];
  const children = spansByParent.get(span.span_id) || [];
  const isExpanded = expandedNodes.has(`${traceId}:${span.span_id}`);
  const isSelected = selectedSpan?.traceId === traceId && selectedSpan?.spanId === span.span_id;
  const hasError = spanHasError(span);

  const childAncestorLines = isLast ? ancestorLines : [...ancestorLines, depth];
  const visualDepth = Math.min(depth, DEPTH_CAP);
  const overCap = depth > DEPTH_CAP;

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
            {!isLast && (
                // Not last child line keeps going
              <Box
                sx={{
                  position: "absolute",
                  left: `${visualDepth * 1.5}rem`,
                  top: 0,
                  bottom: 0,
                  width: lineWidth,
                  bgcolor: connectorColor,
                  pointerEvents: "none",
                }}
              />
            )}
              {/* Curve into node */}
            <Box
              sx={{
                position: "absolute",
                left: `${visualDepth * 1.5}rem`,
                top: isLast ? 0 : "calc(50% - 0.5rem)",
                height: isLast ? "50%" : "0.5rem",
                width: branchWidth,
                ...(isLast && { borderLeft: `${lineWidth} solid` }),
                borderBottom: `${lineWidth} solid`,
                borderColor: connectorColor,
                borderBottomLeftRadius: "0.5rem",
                pointerEvents: "none",
              }}
            />
          </>
        )}

          {/* Ancestor continuation lines */}
        {ancestorLines.map((ancestorDepth) => (
          <Box
            key={ancestorDepth}
            sx={{
              position: "absolute",
              left: `${Math.min(ancestorDepth, DEPTH_CAP) * 1.5}rem`,
              top: 0,
              bottom: 0,
              width: lineWidth,
              bgcolor: connectorColor,
              pointerEvents: "none",
            }}
          />
        ))}

        <Box sx={{ width: `${visualDepth * 1.5}rem` }} />

        {children.length > 0 ? (
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              onToggleExpand(traceId, span.span_id);
            }}
            sx={{ mr: 1, p: 0 }}
          >
            {isExpanded ? <ExpandMore fontSize="small" /> : <ChevronRight fontSize="small" />}
          </IconButton>
        ) : (
          <Box sx={{ width: "1.25rem", mr: 1 }} />
        )}

        {hasError ? (
          <ErrorOutline fontSize="small" color="error" />
        ) : (
          <CheckCircleOutline fontSize="small" color="success" />
        )}

        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            ml: 1,
            flex: 1,
            overflow: "hidden",
            gap: 0.75,
          }}
        >
          <Typography
            variant="body2"
            sx={{
              fontWeight: 500,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {span.name}
          </Typography>
          {overCap && (
            <Typography
              variant="caption"
              sx={{
                ml: 0.75,
                mr: 1,
                px: 1,
                borderRadius: 2,
                bgcolor: "action.selected",
                color: "text.disabled",
                fontFamily: "monospace",
                flexShrink: 0,
              }}
            >
              +{depth - DEPTH_CAP}
            </Typography>
          )}
        </Box>

        <Typography variant="caption" color="text.secondary" fontFamily="monospace">
          {formatDuration(parseFloat(spanGetDuration(span)))}
        </Typography>
      </Box>

      {isExpanded &&
        children.map((child, idx) => (
          <SpanNode
            key={child.span_id}
            span={child}
            traceId={traceId}
            depth={depth + 1}
            isLast={idx === children.length - 1}
            spansByParent={spansByParent}
            ancestorLines={childAncestorLines}
            expandedNodes={expandedNodes}
            selectedSpan={selectedSpan}
            onToggleExpand={onToggleExpand}
            onSelectSpan={onSelectSpan}
          />
        ))}
    </>
  );
};

const TraceTree: React.FC<TraceTreeProps> = ({
  traces,
  expandedNodes,
  selectedSpan,
  onToggleExpand,
  onSelectSpan,
}) => {
  const [searchParams] = useSearchParams();
  const isEpisode = searchParams.get("type") === "episode";
  const episodeId = traceGetEpisodeId(traces[0]);
  const nav = useNavigate();

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
          py: 1,
          px: 2,
          borderBottom: 1,
          borderColor: "divider",
          bgcolor: "background.default",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Typography variant="h6">Trace Details</Typography>
        {!isEpisode && (
          <Button
            variant="text"
            size="small"
            endIcon={<ChevronRight style={{ fontSize: 16 }} />}
            sx={{
              color: "text.secondary",
              fontSize: "0.75rem",
              "& .MuiButton-endIcon": { ml: 0.5 },
            }}
            onClick={() => nav(`/trace/${episodeId}?type=episode`)}
          >
            View Episode
          </Button>
        )}
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
                  <SpanNode
                    key={span.span_id}
                    span={span}
                    traceId={t.trace_id}
                    depth={0}
                    isLast={idx === arr.length - 1}
                    spansByParent={spansByParent}
                    ancestorLines={[]}
                    expandedNodes={expandedNodes}
                    selectedSpan={selectedSpan}
                    onToggleExpand={onToggleExpand}
                    onSelectSpan={onSelectSpan}
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
