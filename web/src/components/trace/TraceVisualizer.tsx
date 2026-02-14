import React, { useEffect, useState } from "react";
import { Box } from "@mui/material";
import TraceTree from "./TraceTree";
import SpanDetails from "./SpanDetails";
import type { Trace } from "../../types/trace";
import { useSearchParams } from "react-router-dom";

interface TraceVisualizerProps {
  traces: Trace[];
}

const TraceVisualizer: React.FC<TraceVisualizerProps> = ({ traces }) => {
  const [searchParams] = useSearchParams();
  const preselectedSpan = searchParams.get("span");
  const [selectedSpan, setSelectedSpan] = useState<string | null>(
    preselectedSpan,
  );
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  // Expand parent nodes of preselected span
  useEffect(() => {
    if (!preselectedSpan || traces.length === 0) return;

    const allSpans = traces.flatMap((t) => t.spans);
    const nodesToExpand = new Set<string>();
    let current = allSpans.find((s) => s.span_id === preselectedSpan);

    while (current?.parent_id) {
      nodesToExpand.add(current.parent_id);
      current = allSpans.find((s) => s.span_id === current?.parent_id);
    }

    setExpandedNodes(nodesToExpand);
  }, [traces, preselectedSpan]);

  // Toggle expand of a node
  const toggleExpand = (spanId: string) => {
    const newExpanded = new Set(expandedNodes);
    newExpanded.has(spanId)
      ? newExpanded.delete(spanId)
      : newExpanded.add(spanId);
    setExpandedNodes(newExpanded);
  };

  const allSpans = traces.flatMap((t) => t.spans);
  const selectedSpanData =
    allSpans.find((s) => s.span_id === selectedSpan) || null;

  return (
    <Box sx={{ display: "flex", height: "100%" }}>
      <TraceTree
        traces={traces}
        expandedNodes={expandedNodes}
        selectedSpan={selectedSpan}
        onToggleExpand={toggleExpand}
        onSelectSpan={setSelectedSpan}
      />
      <SpanDetails span={selectedSpanData} />
    </Box>
  );
};

export default TraceVisualizer;
