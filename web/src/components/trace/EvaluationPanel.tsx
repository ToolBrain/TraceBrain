import React, { useEffect, useMemo, useState } from "react";
import {
  Box,
  Typography,
  Rating,
  TextField,
  Button,
  LinearProgress,
  Chip,
  Alert,
  Dialog,
  DialogContent,
  DialogActions,
  Collapse,
} from "@mui/material";
import { ExpandLess, ExpandMore, ErrorOutline } from "@mui/icons-material";
import type { Trace } from "../../types/trace";
import { traceGetEvaluation } from "../utils/traceUtils";
import { evaluateTrace, submitTraceFeedback } from "../utils/api";
import StatusChip from "../shared/StatusChip";
import { useSettings } from "../../contexts/SettingsContext";
import { getConfidenceColor } from "../utils/utils";

interface EvaluationPanelProps {
  trace: Trace | null;
}

const EvaluationPanel: React.FC<EvaluationPanelProps> = ({ trace }) => {
  const [expertRating, setExpertRating] = useState<number | null>(null);
  const [expertComment, setExpertComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [successOpen, setSuccessOpen] = useState(false);
  const [showEvaluation, setShowEvaluation] = useState(true);

  const [evaluating, setEvaluating] = useState(false);
  const [evalError, setEvalError] = useState<string>("");
  const [showEvalError, setShowEvalError] = useState(false);

  const { settings } = useSettings();

  const evaluation = useMemo(() => {
    if (!trace) return null;
    return traceGetEvaluation(trace) ?? null;
  }, [trace]);

  const aiRating =
    typeof evaluation?.rating === "number" ? evaluation.rating : null;
  const aiFeedback =
    typeof evaluation?.feedback === "string" ? evaluation.feedback : "";
  const aiConfidence =
    typeof evaluation?.confidence === "number" ? evaluation.confidence : null;
  const aiStatus =
    typeof evaluation?.status === "string" ? evaluation.status : null;

  useEffect(() => {
    setSubmitError("");
    setSuccessOpen(false);
    setExpertRating(aiRating);
    setExpertComment(aiFeedback);
    setEvalError("");
    setShowEvalError(false);
  }, [trace?.trace_id]);

  const handleEvaluate = async () => {
    if (!trace) return;
    setEvaluating(true);
    setEvalError("");
    setShowEvalError(false);
    try {
      await evaluateTrace(trace.trace_id, settings.llm.model);
    } catch (e: any) {
      setEvalError(e?.message || "Failed to evaluate trace.");
    } finally {
      setEvaluating(false);
    }
  };

  const handleSubmit = async () => {
    if (!trace || expertRating === null) return;
    setSubmitting(true);
    setSubmitError("");
    try {
      await submitTraceFeedback(trace.trace_id, expertRating, expertComment);
      setSuccessOpen(true);
    } catch (error: any) {
      setSubmitError(error?.message || "Failed to submit validation.");
    } finally {
      setSubmitting(false);
    }
  };

  const confidenceColor = getConfidenceColor(aiConfidence);

  const matchesAISuggestion =
    !!evaluation && expertRating === aiRating && expertComment === aiFeedback;

  const hasEdited =
    !!evaluation && (expertRating !== aiRating || expertComment !== aiFeedback);

  const renderAIAssessment = () => {
    // If currently evaluating
    if (evaluating) {
      return (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
          <LinearProgress />
          <Typography variant="body2" color="text.secondary">
            Processing...
          </Typography>
        </Box>
      );
    }

    // If evaluation resulted in error
    if (evalError) {
      return (
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 2,
            p: 3,
            borderRadius: 2,
            backgroundColor: "rgba(244, 67, 54, 0.06)",
            border: "1px solid",
            borderColor: "error.light",
            minHeight: 220,
            justifyContent: "center",
          }}
        >
          <ErrorOutline sx={{ fontSize: 40, color: "error.light" }} />
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            Evaluation Failed
          </Typography>
          <Typography variant="body2" color="text.secondary" align="center">
            Something went wrong while generating the evaluation. Please try
            again.
          </Typography>
          <Collapse in={showEvalError} sx={{ width: "60%" }}>
            <Alert
              severity="error"
              sx={{
                fontSize: "0.75rem",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                "& .MuiAlert-message": {
                  maxHeight: 120,
                  overflow: "auto",
                  width: "100%",
                },
              }}
            >
              {evalError}
            </Alert>
          </Collapse>
          <Box sx={{ display: "flex", gap: 1 }}>
            <Button
              variant="outlined"
              size="small"
              onClick={() => setShowEvalError((p) => !p)}
            >
              {showEvalError ? "Hide" : "Show"} Details
            </Button>
            <Button variant="contained" size="small" onClick={handleEvaluate}>
              Retry
            </Button>
          </Box>
        </Box>
      );
    }

    // If there exists no evaluation yet
    // Have this for now to enable users to manually initiate AI evaluation in case anything unexpected happens
    if (aiConfidence === null) {
      return (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
          <Button variant="outlined" onClick={handleEvaluate} disabled={!trace}>
            Evaluate
          </Button>
          <Typography variant="body2" color="text.secondary">
            No evaluation yet. Run evaluation to generate AI assessment.
          </Typography>
        </Box>
      );
    }

    // If evaluation exists
    return (
      <>
        <Box>
          <Typography variant="caption" color="text.secondary">
            AI Rating
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Rating
              value={aiRating}
              readOnly
              max={5}
              precision={1}
              size="small"
              sx={{ color: "warning.light" }}
            />
            <Typography variant="caption" color="text.secondary">
              {aiRating !== null ? `${aiRating}/5` : ""}
            </Typography>
          </Box>
        </Box>

        <Box>
          <Typography variant="caption" color="text.secondary">
            Confidence
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Box sx={{ flexGrow: 1 }}>
              <LinearProgress
                variant="determinate"
                value={(aiConfidence ?? 0) * 100}
                color={confidenceColor as "error" | "warning" | "success"}
                sx={{ height: 6, borderRadius: 2 }}
              />
            </Box>
            <Typography variant="caption" color="text.secondary">
              {((aiConfidence ?? 0) * 100).toFixed(0)}%
            </Typography>
          </Box>
        </Box>

        <Box>
          <Typography variant="caption" color="text.secondary">
            AI Rationale
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            {aiFeedback}
          </Typography>
        </Box>

        {aiStatus && (
          <Box>
            <StatusChip status={aiStatus} />
          </Box>
        )}
      </>
    );
  };

  return (
    <>
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: "divider",
          bgcolor: "background.default",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Typography variant="h5">Evaluation and Governance</Typography>
        <Button
          size="small"
          variant="outlined"
          onClick={() => setShowEvaluation((prev) => !prev)}
          startIcon={showEvaluation ? <ExpandLess /> : <ExpandMore />}
        >
          {showEvaluation ? "Collapse" : "Expand"}
        </Button>
      </Box>

      {showEvaluation && (
        <Box
          sx={{
            p: 2,
            borderBottom: 1,
            borderColor: "divider",
            display: "grid",
            gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" },
            gap: 2,
            alignItems: "start",
          }}
        >
          {/* AI Assessment */}
          <Box
            sx={{
              p: 2,
              borderRadius: 2,
              border: "1px dashed",
              borderColor: "divider",
              bgcolor: "action.hover",
              display: "flex",
              flexDirection: "column",
              gap: 2,
            }}
          >
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                AI-Generated Assessment
              </Typography>
              <Chip
                label="AI Draft"
                size="small"
                color="primary"
                sx={{
                  borderColor: "divider",
                  border: "1px solid",
                  p: 1,
                  borderRadius: 2,
                }}
              />
            </Box>

            {renderAIAssessment()}
          </Box>

          {/* Human Validation */}
          <Box
            sx={{
              p: 2,
              borderRadius: 2,
              border: "1px solid",
              borderColor: hasEdited ? "primary.light" : "divider",
              bgcolor: "background.paper",
              display: "flex",
              flexDirection: "column",
              gap: 2,
            }}
          >
            <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
              Human Validation
            </Typography>

            {matchesAISuggestion && (
              <Typography variant="caption" color="success.main">
                Matches AI Suggestion
              </Typography>
            )}
            {hasEdited && (
              <Typography variant="caption" color="text.secondary">
                Edited from AI Suggestion
              </Typography>
            )}

            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Final Rating
              </Typography>
              <Rating
                value={expertRating}
                onChange={(_, value) => setExpertRating(value)}
                max={5}
                precision={1}
                size="medium"
              />
            </Box>

            <Box>
              <Typography variant="caption" color="text.secondary">
                Comment
              </Typography>
              <TextField
                multiline
                minRows={4}
                fullWidth
                value={expertComment}
                onChange={(e) => setExpertComment(e.target.value)}
                placeholder="Adjust the AI rationale if needed..."
                sx={{
                  mt: 1,
                  "& .MuiOutlinedInput-root": {
                    fontFamily: "monospace",
                    fontSize: "0.875rem",
                  },
                }}
              />
            </Box>

            {submitError && <Alert severity="error">{submitError}</Alert>}

            <Button
              variant="contained"
              onClick={handleSubmit}
              disabled={expertRating === null || submitting}
            >
              {submitting ? "Submitting..." : "Verify and Submit"}
            </Button>
          </Box>
        </Box>
      )}

      {/* UI Interaction Feedback */}
      <Dialog open={successOpen} onClose={() => setSuccessOpen(false)}>
        <DialogContent>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              Submitted
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Validation saved successfully.
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button variant="contained" onClick={() => setSuccessOpen(false)}>
            OK
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default EvaluationPanel;
