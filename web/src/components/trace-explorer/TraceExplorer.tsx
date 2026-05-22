import React, { useEffect, useState } from "react";
import { Box } from "@mui/material";
import TraceTree from "./TraceTree";
import { useSearchParams, useParams } from "react-router-dom";
import InspectorPanel from "./InspectorPanel";
import { useQuery } from "@tanstack/react-query";
import { fetchEpisodeTraces, fetchTrace } from "../utils/api";

interface SelectedSpan {
  traceId: string;
  spanId: string;
}

const TraceExplorer: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const preselectedSpan = searchParams.get("span");
  const type = searchParams.get("type");
  const isEpisodeView = type === "episode";
  const preselectedTrace = isEpisodeView ? searchParams.get("trace") : id;

  const { data: traces = [] } = useQuery({
    queryKey: ["traces", type, id],
    queryFn: () =>
      isEpisodeView ? fetchEpisodeTraces(id!) : fetchTrace(id!),
  });

  const [selectedSpan, setSelectedSpan] = useState<SelectedSpan | null>(
    preselectedSpan && preselectedTrace
      ? { traceId: preselectedTrace, spanId: preselectedSpan }
      : null,
  );
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [initialized, setInitialized] = useState(false);

  // Select first span of preselected trace once traces load
  useEffect(() => {
    if (initialized || !preselectedTrace || preselectedSpan || traces.length === 0) return;
    const trace = traces.find((t) => t.trace_id === preselectedTrace);
    const firstSpan = trace?.spans[0]?.span_id ?? null;
    if (firstSpan) {
      setSelectedSpan({ traceId: preselectedTrace, spanId: firstSpan });
      setInitialized(true);
    }
  }, [traces, preselectedTrace]);

  // Expand parent nodes of preselected span
  useEffect(() => {
    if (initialized || !preselectedSpan || !preselectedTrace || traces.length === 0) return;
    const trace = traces.find((t) => t.trace_id === preselectedTrace);
    if (!trace) return;
    const nodesToExpand = new Set<string>();
    let current = trace.spans.find((s) => s.span_id === preselectedSpan);
    while (current?.parent_id) {
      nodesToExpand.add(`${preselectedTrace}:${current.parent_id}`);
      current = trace.spans.find((s) => s.span_id === current?.parent_id);
    }
    setExpandedNodes(nodesToExpand);
    setInitialized(true);
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
      <InspectorPanel span={selectedSpanData} trace={activeTrace} traces={traces} />
    </Box>
  );
};

export default TraceExplorer;