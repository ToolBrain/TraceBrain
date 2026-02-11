import React from "react";
import { Box, TextField, Typography, Rating } from "@mui/material";

interface FeedbackFormProps {
  rating: number | null;
  feedback: string;
  onRatingChange: (rating: number | null) => void;
  onFeedbackChange: (value: string) => void;
}

const FeedbackForm: React.FC<FeedbackFormProps> = ({
  rating,
  feedback,
  onRatingChange,
  onFeedbackChange,
}) => {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <Box>
        <Typography
          variant="subtitle2"
          sx={{
            mb: 2.5,
            fontWeight: 600,
            fontSize: "0.875rem",
            color: "text.secondary",
            textTransform: "uppercase",
          }}
        >
          Rating
        </Typography>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1.5,
          }}
        >
          <Rating
            value={rating}
            onChange={(_, newValue) => onRatingChange(newValue)}
            precision={1}
            max={5}
            size="large"
          />
          <Typography variant="caption" sx={{ fontFamily: "monospace" }}>
            {rating !== null ? `${rating}/5` : ""}
          </Typography>
        </Box>
      </Box>

      <Box>
        <Typography
          variant="subtitle2"
          sx={{
            mb: 1.5,
            fontWeight: 600,
            fontSize: "0.875rem",
            color: "text.secondary",
            textTransform: "uppercase",
          }}
        >
          Comments
        </Typography>
        <TextField
          multiline
          rows={10}
          fullWidth
          placeholder="Enter your comments here..."
          value={feedback}
          onChange={(e) => onFeedbackChange(e.target.value)}
          sx={{
            "& .MuiOutlinedInput-root": {
              fontFamily: "monospace",
              fontSize: "0.875rem",
              backgroundColor: "background.paper",
            },
          }}
        />
      </Box>
    </Box>
  );
};

export default FeedbackForm;
