import React, { useEffect, useState } from "react";
import { Box, Tab, Tabs } from "@mui/material";
import type { Span, Trace } from "../../types/trace";
import SpanDetails from "./SpanDetails";
import TraceDiff from "./TraceDiff";

interface InspectorPanelProps {
  span: Span | null;
  trace: Trace | null;
  traces: Trace[];
}

const InspectorPanel: React.FC<InspectorPanelProps> = ({ span, trace, traces }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [selectedTraceIds, setSelectedTraceIds] = useState<string[]>([]);

  useEffect(() => {
    setSelectedTraceIds((prev) =>
      prev.length === 0 ? traces.slice(0, 2).map((t) => t.trace_id) : prev,
    );
  }, [traces]);

  return (
    <Box
      sx={{
        width: "75%",
        bgcolor: "background.paper",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        minHeight: 0,
        overflow: "hidden",
      }}
    >
      <Tabs
        value={activeTab}
        onChange={(_, v) => setActiveTab(v)}
        sx={{ borderBottom: 1, borderColor: "divider", bgcolor: "background.default" }}
      >
        <Tab label="Info" />
        <Tab
          label={
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.75 }}>
              Compare
              {traces.length > 1 && (
                <Box
                  sx={{
                    lineHeight: 1,
                    bgcolor: "action.selected",
                    color: "text.secondary",
                    borderRadius: "50%",
                    width: 18,
                    height: 18,
                    fontSize: "0.65rem",
                    fontWeight: 700,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  {traces.length}
                </Box>
              )}
            </Box>
          }
        />
      </Tabs>

      {activeTab === 0 && (
        <Box
          sx={{
            flex: 1,
            minHeight: 0,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          <SpanDetails span={span} trace={trace} />
        </Box>
      )}
      {activeTab === 1 && (
        <Box
          sx={{
            flex: 1,
            minHeight: 0,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          <TraceDiff
            traces={traces}
            selectedTraceIds={selectedTraceIds}
            onSelectedTraceIdsChange={setSelectedTraceIds}
          />
        </Box>
      )}
    </Box>
  );
};

export default InspectorPanel;
