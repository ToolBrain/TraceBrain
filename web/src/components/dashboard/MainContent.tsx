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
  Snackbar,
  Alert,
  CircularProgress,
} from "@mui/material";
import {
  Search,
  ArrowDownward,
  ArrowUpward,
  Clear,
  Refresh,
  PlaylistAddCheck,
  BarChart,
  BarChartOutlined,
} from "@mui/icons-material";
import { useMemo, useState } from "react";
import TraceList from "./TraceList";
import type { Trace } from "../../types/trace";
import { traceGetEvaluation, traceGetPriority } from "../utils/traceUtils";
import { batchEvaluateTraces } from "../utils/api";
import { useQueryClient } from "@tanstack/react-query";
import { useSettings } from "../../contexts/SettingsContext";

interface MainContentProps {
  traces: Trace[];
  view: React.ReactElement;
}

const sortOptions = [
  { value: "datetime", label: "DateTime" },
  { value: "duration", label: "Duration" },
  { value: "confidence", label: "Confidence" },
  { value: "priority", label: "Priority" },
];

const MainContent: React.FC<MainContentProps> = ({ traces, view }) => {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("datetime");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [analyzingIds, setAnalyzingIds] = useState<Set<string>>(new Set());
  const [showView, setShowView] = useState(true);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success" as "success" | "error" | "info" | "warning",
  });
  const { settings } = useSettings();

  const handleEvaluateTraces = async () => {
    setIsEvaluating(true);
    setAnalyzingIds(
      new Set(
        traces
          .filter((t) => !traceGetEvaluation(t))
          .slice(0, settings.llm.batchSize)
          .map((t) => t.trace_id),
      ),
    );
    try {
      const result = await batchEvaluateTraces(settings.llm.batchSize);
      const processed = Number(result?.processed ?? 0);
      const failed = Number(result?.failed ?? 0);

      const message =
        processed === 0 && failed === 0
          ? "No traces pending evaluation."
          : processed > 0 && failed > 0
            ? `Evaluated ${processed} trace(s) successfully, ${failed} failed.`
            : processed > 0
              ? `Evaluated ${processed} trace(s) successfully.`
              : `Evaluation failed for ${failed} trace(s).`;

      const severity =
        processed === 0 && failed === 0
          ? "info"
          : failed > 0 && processed === 0
            ? "error"
            : failed > 0
              ? "warning"
              : "success";

      setSnackbar({ open: true, message, severity });

      if (processed > 0) {
        await queryClient.invalidateQueries({ queryKey: ["dashboard-traces"] });
      }
    } catch (error: any) {
      console.error("Failed to evaluate traces:", error);
      setSnackbar({
        open: true,
        message: "Failed to evaluate traces",
        severity: "error",
      });
    } finally {
      setAnalyzingIds(new Set());
      setIsEvaluating(false);
    }
  };

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ["dashboard-traces"] });
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

      return {
        trace: { ...trace, isAnalyzing: analyzingIds.has(trace.trace_id) },
        startTime,
        duration,
        priority,
        confidence,
      };
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
  }, [traces, sortBy, sortOrder, searchQuery, analyzingIds]);

  return (
    <Box sx={{ p: 3, height: "100%", display: "flex", flexDirection: "column" }}>
      <Box sx={{ display: showView ? "block" : "none" }}>{view}</Box>

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
          variant="outlined"
          onClick={handleRefresh}
          size="small"
          sx={{
            borderRadius: 1,
            height: "2.5rem",
            "&:hover": {
              borderColor: "text.primary",
              bgcolor: "action.hover",
            },
          }}
        >
          <Refresh fontSize="small" />
        </Button>

        <Button
          variant="contained"
          onClick={handleEvaluateTraces}
          disabled={isEvaluating}
          size="small"
          startIcon={
            isEvaluating ? <CircularProgress size={16} color="inherit" /> : <PlaylistAddCheck />
          }
          sx={{
            borderRadius: 1,
            height: "2.5rem",
            fontWeight: 600,
          }}
        >
          {isEvaluating ? "Evaluating..." : "Batch Evaluate"}
        </Button>

        <TextField
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

        <IconButton
          size="small"
          onClick={() => setShowView((prev) => !prev)}
          sx={{
            color: showView ? "primary.main" : "text.secondary",
            bgcolor: "action.hover",
            "&:hover": { bgcolor: "action.selected" },
          }}
        >
          {showView ? <BarChart fontSize="medium" /> : <BarChartOutlined fontSize="medium" />}
        </IconButton>
      </Box>

      <TraceList traces={sortedTraces} loading={isEvaluating} />

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert
          severity={snackbar.severity}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default MainContent;
