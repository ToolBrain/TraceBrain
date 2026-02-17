import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogActions,
  IconButton,
  Button,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Checkbox,
  FormControlLabel,
  Tooltip,
} from "@mui/material";
import {
  ArrowCircleUp,
  Close,
  ErrorOutline,
  HelpOutline,
} from "@mui/icons-material";
import FeedbackForm from "./FeedbackForm";
import ConfidenceIndicator from "../dashboard/ConfidenceIndicator";
import StatusChip, { type ChipStatus } from "../dashboard/StatusChip";
import {
  submitTraceFeedback,
  evaluateTrace,
  signalTraceIssue,
} from "../utils/api";
import { useSettings } from "../../contexts/SettingsContext";
import type { Feedback } from "../../types/trace";

interface TraceModalProps {
  open: boolean;
  onClose: () => void;
  type: "feedback" | "evaluate";
  id: string;
  feedback?: Feedback | null;
}

const ReviewToggle = ({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
}) => (
  <Box display="flex" alignItems="center" gap={0.5}>
    <FormControlLabel
      control={
        <Checkbox
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
        />
      }
      label="Mark for review"
      sx={{ mr: 0 }}
    />
    <Tooltip title="Flag this trace for automated task generation." arrow>
      <IconButton size="small">
        <HelpOutline fontSize="small" />
      </IconButton>
    </Tooltip>
  </Box>
);

const TraceModal: React.FC<TraceModalProps> = ({
  open,
  onClose,
  type,
  id,
  feedback: latestFeedback,
}) => {
  const [rating, setRating] = useState<number | null>(null);
  const [feedback, setFeedback] = useState("");
  const [confidence, setConfidence] = useState<number | null>(null);
  const [evalStatus, setEvalStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [markForReview, setMarkForReview] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [successOpen, setSuccessOpen] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const { settings } = useSettings();
  const [showDetails, setShowDetails] = useState(false);

  const resolveEvalStatus = (status: string | null): ChipStatus | null => {
    if (!status) return null;
    const normalized = status.toLowerCase();
    if (normalized === "pending_review") return "pending_review";
    if (normalized === "auto_verified") return "auto_verified";
    if (normalized === "completed") return "completed";
    return null;
  };

  useEffect(() => {
    const fetchEvaluation = async () => {
      if (type === "evaluate" && open) {
        setLoading(true);
        setError("");
        try {
          const data = await evaluateTrace(id, settings.llm.model);
          setRating(data.rating);
          setFeedback(data.feedback);
          setConfidence(data.confidence ?? null);
          setEvalStatus(data.status ?? null);
        } catch (error: any) {
          console.error("Failed to fetch evaluation:", error);
          setError(error.message);
        } finally {
          setLoading(false);
        }
      }
    };

    fetchEvaluation();
  }, [type, open, id, settings.llm.model]);

  useEffect(() => {
    setRating(null);
    setFeedback("");
    setConfidence(null);
    setEvalStatus(null);
    setError("");
    setShowDetails(false);
    setMarkForReview(false);
    setSubmitting(false);
    setSuccessOpen(false);
    setSuccessMessage("");
  }, [id, type]);

  useEffect(() => {
    if (rating !== null && rating <= 1) {
      setMarkForReview(true);
    } else {
      setMarkForReview(false);
    }
  }, [rating]);

  useEffect(() => {
    if (type !== "feedback") {
      return;
    }

    if (latestFeedback) {
      setRating(latestFeedback.rating ?? null);
      setFeedback(latestFeedback.comment ?? "");
    }
  }, [latestFeedback, type]);

  const handleRetry = () => {
    setError("");
    setLoading(true);
    evaluateTrace(id, settings.llm.model)
      .then((data) => {
        setRating(data.rating);
        setFeedback(data.feedback);
        setConfidence(data.confidence ?? null);
        setEvalStatus(data.status ?? null);
      })
      .catch((error: any) => {
        console.error("Failed to fetch evaluation:", error);
        setError(error.message);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const handleSubmitFeedback = async () => {
    if (rating === null) return;
    setSubmitting(true);
    setError("");
    try {
      if (type === "feedback") {
        await submitTraceFeedback(id, rating, feedback);

        if (rating <= 2 && markForReview) {
          await signalTraceIssue(id, feedback);
        }
      }

      setSuccessMessage(
        type === "evaluate"
          ? "Evaluation captured successfully."
          : "Feedback submitted successfully.",
      );
      setSuccessOpen(true);
    } catch (submitError: any) {
      console.error("Failed to submit feedback:", submitError);
      setError(submitError?.message || "Failed to submit feedback.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleSuccessClose = () => {
    setSuccessOpen(false);
    onClose();
  };

  const renderContent = () => {
    switch (type) {
      case "feedback":
        return (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Provide Feedback
            </Typography>

            <FeedbackForm
              rating={rating}
              feedback={feedback}
              onRatingChange={setRating}
              onFeedbackChange={setFeedback}
            />

            {rating !== null && rating <= 2 && (
              <ReviewToggle
                checked={markForReview}
                onChange={setMarkForReview}
              />
            )}
          </Box>
        );

      case "evaluate":
        if (loading) {
          return (
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                height: "100%",
                minHeight: "40vh",
              }}
            >
              <CircularProgress size={48} />
              <Typography variant="body1" sx={{ mt: 2, fontWeight: 600 }}>
                Generating evaluation...
              </Typography>
            </Box>
          );
        }

        if (error) {
          return (
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                height: "100%",
                minHeight: "40vh",
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: 3,
                  p: 4,
                  borderRadius: 2,
                  backgroundColor: "rgba(244, 67, 54, 0.06)",
                  border: "1px solid",
                  borderColor: "error.light",
                  maxWidth: "500px",
                }}
              >
                <ErrorOutline sx={{ fontSize: 64, color: "error.light" }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Evaluation Failed
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Something went wrong while generating the evaluation. Please
                  try again.
                </Typography>
                {showDetails && (
                  <Alert
                    severity="error"
                    sx={{
                      width: "100%",
                      whiteSpace: "pre-wrap",
                      maxHeight: "150px",
                      wordBreak: "break-word",
                      overflow: "auto",
                    }}
                  >
                    {error}
                  </Alert>
                )}
                <Box sx={{ display: "flex", gap: 2 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setShowDetails(!showDetails)}
                  >
                    {showDetails ? "Hide" : "Show"} Details
                  </Button>
                  <Button
                    variant="contained"
                    size="large"
                    onClick={handleRetry}
                  >
                    Retry
                  </Button>
                </Box>
              </Box>
            </Box>
          );
        }

        if (confidence !== null) {
          return (
            <Box
              sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 2 }}
            >
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                AI Evaluation
              </Typography>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Confidence: {(confidence * 100).toFixed(0)}%
                </Typography>
                <ConfidenceIndicator
                  confidence={confidence}
                  status={
                    (evalStatus as
                      | "pending_review"
                      | "auto_verified"
                      | "completed") || "pending_review"
                  }
                />
                {resolveEvalStatus(evalStatus) && (
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      Evaluation status:
                    </Typography>
                    <StatusChip
                      status={resolveEvalStatus(evalStatus) as ChipStatus}
                      secondary
                    />
                  </Box>
                )}
              </Box>
              <FeedbackForm
                rating={rating}
                feedback={feedback}
                onRatingChange={setRating}
                onFeedbackChange={setFeedback}
              />
            </Box>
          );
        }

        return (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2, pt: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Evaluation Results
            </Typography>

            <FeedbackForm
              rating={rating}
              feedback={feedback}
              onRatingChange={setRating}
              onFeedbackChange={setFeedback}
            />

            {rating !== null && rating <= 2 && (
              <ReviewToggle
                checked={markForReview}
                onChange={setMarkForReview}
              />
            )}
          </Box>
        );
    }
  };

  const renderActions = () => {
    if (type === "evaluate" && (loading || error)) {
      return null;
    }

    return (
      <>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSubmitFeedback}
          disabled={rating === null || submitting}
        >
          {submitting ? "Submitting..." : "Submit"}
        </Button>
      </>
    );
  };

  return (
    <>
      <Dialog
        open={open}
        maxWidth={false}
        slotProps={{
          paper: {
            sx: {
              width: "60vw",
              height: "50vh",
            },
          },
        }}
      >
        <IconButton
          onClick={onClose}
          sx={{
            position: "absolute",
            right: 8,
            top: 8,
          }}
        >
          <Close />
        </IconButton>

        <DialogContent>
          {error && type === "feedback" && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          {renderContent()}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>{renderActions()}</DialogActions>
      </Dialog>

      <Dialog open={successOpen} onClose={handleSuccessClose} maxWidth="xs">
        <DialogContent>
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 2,
              py: 2,
            }}
          >
            <ArrowCircleUp sx={{ fontSize: 64, color: "success.main" }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Success
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center">
              {successMessage}
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions sx={{ justifyContent: "center", pb: 2 }}>
          <Button variant="contained" onClick={handleSuccessClose}>
            OK
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default TraceModal;
