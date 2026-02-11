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
} from "@mui/material";
import { Close, ErrorOutline } from "@mui/icons-material";
import FeedbackForm from "./FeedbackForm";
import { submitTraceFeedback, evaluateTrace } from "../utils/api";
import { customScrollbar } from "../../styles/customScrollBar";
import { useSettings } from "../../contexts/SettingsContext";

interface TraceModalProps {
  open: boolean;
  onClose: () => void;
  type: "feedback" | "evaluate";
  id: string;
}

const TraceModal: React.FC<TraceModalProps> = ({ open, onClose, type, id }) => {
  const [rating, setRating] = useState<number | null>(null);
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<boolean>(false);
  const { settings } = useSettings();

  useEffect(() => {
    const fetchEvaluation = async () => {
      if (type === "evaluate" && open) {
        setLoading(true);
        setError(false);
        try {
          const data = await evaluateTrace(id, settings.llm.model);

          setRating(data.rating);
          setFeedback(data.feedback);
        } catch (error) {
          console.error("Failed to fetch evaluation:", error);
          setError(true);
        } finally {
          setLoading(false);
        }
      }
    };

    fetchEvaluation();
  }, [type, open, id, settings.llm.model]);

  const handleRetry = () => {
    setError(false);
    setLoading(true);
    evaluateTrace(id, settings.llm.model)
      .then((data) => {
        setRating(data.rating);
        setFeedback(data.feedback);
      })
      .catch((error) => {
        console.error("Failed to fetch evaluation:", error);
        setError(true);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const handleSubmitFeedback = async () => {
    if (rating === null) return;
    submitTraceFeedback(id, rating, feedback);
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
                <Alert severity="error" sx={{ width: "100%" }}>
                  Something went wrong while generating the evaluation. Please
                  try again.
                </Alert>
                <Button variant="contained" size="large" onClick={handleRetry}>
                  Retry
                </Button>
              </Box>
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
          </Box>
        );
    }
  };

  const renderActions = () => {
    if (type === "evaluate" && (loading || error)) {
      return null;
    }

    switch (type) {
      case "feedback":
        return (
          <>
            <Button onClick={onClose}>Cancel</Button>
            <Button
              variant="contained"
              onClick={handleSubmitFeedback}
              disabled={rating === null}
            >
              Submit
            </Button>
          </>
        );
      case "evaluate":
        return (
          <>
            <Button onClick={onClose}>Cancel</Button>
            <Button
              variant="contained"
              onClick={handleSubmitFeedback}
              disabled={rating === null}
            >
              Submit
            </Button>
          </>
        );
    }
  };

  return (
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

      <DialogContent sx={{ ...customScrollbar }}>
        {renderContent()}
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>{renderActions()}</DialogActions>
    </Dialog>
  );
};

export default TraceModal;
