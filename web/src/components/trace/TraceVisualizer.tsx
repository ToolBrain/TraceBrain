import React, { useEffect, useState } from "react";
import { Box } from "@mui/material";
import TraceTree from "./TraceTree";
import TraceDetails from "./TraceDetails";
import type { Trace } from "../../types/trace";
import { useSearchParams } from "react-router-dom";

interface TraceVisualizerProps {
  traces: Trace[];
}

const TraceVisualizer: React.FC<TraceVisualizerProps> = ({ traces }) => {
  const [searchParams] = useSearchParams();
  const preselectedSpan = searchParams.get("span");
  const [selectedId, setSelectedId] = useState<string | null>(
    preselectedSpan || (traces.length > 0 ? traces[0].trace_id : null),
  );
  const [selectedType, setSelectedType] = useState<"trace" | "span">(
    preselectedSpan ? "span" : "trace",
  );

  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (traces.length === 0) return;

    const nodesToExpand = new Set<string>();

    traces.forEach((t) => nodesToExpand.add(t.trace_id));

    // Expand parent nodes of preselected span
    if (preselectedSpan) {
      const allSpans = traces.flatMap((t) => t.spans);
      let current = allSpans.find((s) => s.span_id === preselectedSpan);

      while (current?.parent_id) {
        nodesToExpand.add(current.parent_id);
        current = allSpans.find((s) => s.span_id === current?.parent_id);
      }
    }

    setExpandedNodes(nodesToExpand);
  }, [traces, preselectedSpan]);

  // Toggle expand of a node
  const toggleExpand = (id: string) => {
    const newExpanded = new Set(expandedNodes);
    newExpanded.has(id) ? newExpanded.delete(id) : newExpanded.add(id);
    setExpandedNodes(newExpanded);
  };

  const handleSelect = (id: string, type: "trace" | "span") => {
    setSelectedId(id);
    setSelectedType(type);
  };

  // Get selected data
  const allSpans = traces.flatMap((t) => t.spans);
  const selectedSpan =
    selectedType === "span"
      ? allSpans.find((s) => s.span_id === selectedId) || null
      : null;
  const selectedTrace =
    selectedType === "trace"
      ? traces.find((t) => t.trace_id === selectedId) || null
      : null;

  return (
    <Box sx={{ display: "flex", height: "100%" }}>
      <TraceTree
        traces={traces}
        expandedNodes={expandedNodes}
        selectedId={selectedId}
        selectedType={selectedType}
        onToggleExpand={toggleExpand}
        onSelect={handleSelect}
      />
      <TraceDetails span={selectedSpan} trace={selectedTrace} />
    </Box>
  );
};

export default TraceVisualizer;
