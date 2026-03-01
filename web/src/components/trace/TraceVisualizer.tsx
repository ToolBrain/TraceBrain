import React, { useEffect, useState } from "react";
import { Box } from "@mui/material";
import TraceTree from "./TraceTree";
import SpanDetails from "./SpanDetails";
import type { Trace } from "../../types/trace";
import { useSearchParams, useParams } from "react-router-dom";

interface TraceVisualizerProps {
  traces: Trace[];
}

interface SelectedSpan {
  traceId: string;
  spanId: string;
}

const TraceVisualizer: React.FC<TraceVisualizerProps> = ({ traces }) => {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const preselectedSpan = searchParams.get("span");
  const isEpisodeView = searchParams.get("type") === "episode";
  const preselectedTrace = isEpisodeView ? searchParams.get("trace") : id;

  const [selectedSpan, setSelectedSpan] = useState<SelectedSpan | null>(
    preselectedSpan && preselectedTrace
      ? { traceId: preselectedTrace, spanId: preselectedSpan }
      : null,
  );
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  // Select first span of preselected trace once traces load
  useEffect(() => {
    if (!preselectedTrace || preselectedSpan || traces.length === 0) return;
    const trace = traces.find((t) => t.trace_id === preselectedTrace);
    const firstSpan = trace?.spans[0]?.span_id ?? null;
    if (firstSpan)
      setSelectedSpan({ traceId: preselectedTrace, spanId: firstSpan });
  }, [traces, preselectedTrace]);

  // Expand parent nodes of preselected span
  useEffect(() => {
    if (!preselectedSpan || !preselectedTrace || traces.length === 0) return;
    const trace = traces.find((t) => t.trace_id === preselectedTrace);
    if (!trace) return;
    const nodesToExpand = new Set<string>();
    let current = trace.spans.find((s) => s.span_id === preselectedSpan);
    while (current?.parent_id) {
      nodesToExpand.add(`${preselectedTrace}:${current.parent_id}`);
      current = trace.spans.find((s) => s.span_id === current?.parent_id);
    }
    setExpandedNodes(nodesToExpand);
  }, [traces, preselectedSpan, preselectedTrace]);

  // Toggle expand of a node
  const toggleExpand = (traceId: string, spanId: string) => {
    const key = `${traceId}:${spanId}`;
    const newExpanded = new Set(expandedNodes);
    newExpanded.has(key) ? newExpanded.delete(key) : newExpanded.add(key);
    setExpandedNodes(newExpanded);
  };

  // Find the trace that owns the selected span
  const activeTrace = selectedSpan
    ? (traces.find((t) => t.trace_id === selectedSpan.traceId) ?? null)
    : null;

  // Find the selected span within its trace
  const selectedSpanData = selectedSpan
    ? (activeTrace?.spans.find((s) => s.span_id === selectedSpan.spanId) ??
      null)
    : null;

  return (
    <Box sx={{ display: "flex", height: "100%" }}>
      <TraceTree
        traces={traces}
        expandedNodes={expandedNodes}
        selectedSpan={selectedSpan}
        onToggleExpand={toggleExpand}
        onSelectSpan={setSelectedSpan}
      />
      <SpanDetails span={selectedSpanData} trace={activeTrace} />
    </Box>
  );
};

export default TraceVisualizer;