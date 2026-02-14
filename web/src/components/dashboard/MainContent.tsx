import {
  Box,
  TextField,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Button,
} from "@mui/material";
import {
  Search,
  ArrowDownward,
  ArrowUpward,
  Clear,
  Refresh,
  PlaylistAddCheck,
} from "@mui/icons-material";
import { useMemo, useState } from "react";
import TraceList from "./TraceList";
import type { Trace } from "../../types/trace";
import { traceGetEvaluation, traceGetPriority } from "../utils/traceUtils";
import { batchEvaluateTraces } from "../utils/api";

interface MainContentProps {
  traces: Trace[];
  onFetchTraces: () => void;
  graph: React.ReactElement;
}

const sortOptions = [
  { value: "datetime", label: "DateTime" },
  { value: "duration", label: "Duration" },
  { value: "confidence", label: "Confidence" },
  { value: "priority", label: "Priority" },
];

const MainContent: React.FC<MainContentProps> = ({
  traces,
  onFetchTraces,
  graph,
}) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("datetime");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const handleEvaluateTraces = async () => {
    try {
      await batchEvaluateTraces();
    } catch (error: any) {
      console.error("Failed to start batch evaluation:", error);
    }
  };

  // Sort traces based on sortBy and sortOrder
  const sortedTraces = useMemo(() => {
    // Filter traces by searchQuery
    const filteredTraces = traces.filter((trace) =>
      trace.trace_id.toLowerCase().includes(searchQuery.toLowerCase()),
    );

    const tracesWithMetrics = filteredTraces.map((trace) => {
      // Calculate trace start time and duration from spans
      const spanTimes = trace.spans.map((span) => ({
        start: new Date(span.start_time).getTime(),
        end: new Date(span.end_time).getTime(),
      }));

      const startTime = Math.min(...spanTimes.map((t) => t.start));
      const endTime = Math.max(...spanTimes.map((t) => t.end));
      const duration = endTime - startTime;
      const priority = traceGetPriority(trace);
      const evaluation = traceGetEvaluation(trace);
      const confidence = evaluation?.confidence ?? 0.5; // set undefined confidence to average

      return { trace, startTime, duration, priority, confidence };
    });

    return tracesWithMetrics
      .sort((a, b) => {
        let compareValue = 0;

        if (sortBy === "datetime") {
          compareValue = a.startTime - b.startTime;
        } else if (sortBy === "duration") {
          compareValue = a.duration - b.duration;
        } else if (sortBy === "priority") {
          compareValue = a.priority - b.priority;
        } else if (sortBy === "confidence") {
          compareValue = a.confidence - b.confidence;
        }

        return sortOrder === "asc" ? compareValue : -compareValue;
      })
      .map((item) => item.trace);
  }, [traces, sortBy, sortOrder, searchQuery]);

  return (
    <Box
      sx={{ p: 3, height: "100%", display: "flex", flexDirection: "column" }}
    >
      {graph}
      <Box
        sx={{
          display: "flex",
          gap: 2,
          mb: 2,
          alignItems: "center",
        }}
      >
        <FormControl size="small">
          <InputLabel>Sort By</InputLabel>
          <Select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            label="Sort By"
            IconComponent={() => (
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  setSortOrder(sortOrder === "asc" ? "desc" : "asc");
                }}
                sx={{ mr: 1 }}
              >
                {sortOrder === "asc" ? (
                  <ArrowUpward fontSize="small" />
                ) : (
                  <ArrowDownward fontSize="small" />
                )}
              </IconButton>
            )}
          >
            {sortOptions.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <Button
          onClick={onFetchTraces}
          size="small"
          sx={{
            border: "2px solid",
            borderColor: "gray",
            borderRadius: "4px",
            height: "40px",
            "&:hover": {
              borderColor: "text.primary",
              bgcolor: "action.hover",
            },
          }}
        >
          <Refresh fontSize="small" />
        </Button>

        <Button
          variant="outlined"
          onClick={handleEvaluateTraces}
          size="small"
          startIcon={<PlaylistAddCheck />}
          sx={{
            borderRadius: "4px",
            height: "40px",
            fontWeight: 600,
          }}
        >
          Evaluate Traces
        </Button>

        <TextField
          size="small"
          sx={{ width: "20%", maxWidth: 300, ml: "auto" }}
          placeholder="Search ID..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          slotProps={{
            input: {
              endAdornment: (
                <InputAdornment position="end">
                  {searchQuery && (
                    <IconButton
                      size="small"
                      onMouseDown={(e) => {
                        e.preventDefault();
                        setSearchQuery("");
                      }}
                      edge="end"
                      sx={{ mr: 0.5 }}
                    >
                      <Clear fontSize="small" />
                    </IconButton>
                  )}
                  <Search fontSize="small" />
                </InputAdornment>
              ),
            },
          }}
        />
      </Box>

      <TraceList traces={sortedTraces} />
    </Box>
  );
};

export default MainContent;
