import React, { useState } from "react";
import { Box, Typography, ButtonBase, IconButton, Tooltip } from "@mui/material";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import CheckIcon from "@mui/icons-material/Check";

const COLLAPSED_HEIGHT = 100;

interface SpanContentProps {
  title: string;
  subtitle?: string | null;
  content: string | null;
  hasError?: boolean;
  defaultExpanded?: boolean;
}

const SpanContent: React.FC<SpanContentProps> = ({
  title,
  subtitle,
  content,
  hasError,
  defaultExpanded = false,
}) => {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const [copied, setCopied]     = useState(false);
  const errorColor   = "rgba(220, 38, 38, 0.08)";
  const successColor = "rgba(34, 197, 94, 0.08)";
  const safeContent  = content ?? "";
  const isLong       = safeContent.length > 400;
  const showCopy     = safeContent.length > 0;

  const handleCopy = () => {
    navigator.clipboard.writeText(safeContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Box sx={{ mb: 3 }}>
      <Typography
        variant="overline"
        sx={{
          fontWeight: 700,
          letterSpacing: 1,
          color: "text.secondary",
          display: "block",
          mb: 1,
        }}
      >
        {title}
      </Typography>
      <Box
        sx={{
          px: 2.5,
          py: 2,
          borderRadius: 2,
          bgcolor: hasError ? errorColor : successColor,
          border: 1,
          borderColor: hasError ? "error.main" : "success.main",
          position: "relative",
          "&:hover .copy-btn": { opacity: 1 },
        }}
      >
        {subtitle && (
          <>
            <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1 }}>
              <Typography
                variant="subtitle2"
                sx={{
                  fontWeight: 600,
                  color: "text.primary",
                  textTransform: "uppercase",
                }}
              >
                {subtitle}
              </Typography>
              {showCopy && (
                <Tooltip title={copied ? "Copied!" : "Copy"} placement="top">
                  <IconButton
                    className="copy-btn"
                    size="small"
                    onClick={handleCopy}
                    sx={{
                      opacity: 0,
                      transition: "opacity 0.15s",
                      color: copied ? "success.main" : "text.secondary",
                      p: 0.5,
                    }}
                  >
                    {copied ? <CheckIcon sx={{ fontSize: 16 }} /> : <ContentCopyIcon sx={{ fontSize: 16 }} />}
                  </IconButton>
                </Tooltip>
              )}
            </Box>
            <Box sx={{ width: "100%", height: "1px", bgcolor: "divider", mb: 1.5 }} />
          </>
        )}

        {!subtitle && showCopy && (
          <Tooltip title={copied ? "Copied!" : "Copy"} placement="top">
            <IconButton
              className="copy-btn"
              size="small"
              onClick={handleCopy}
              sx={{
                position: "absolute",
                top: 8,
                right: 8,
                opacity: 0,
                transition: "opacity 0.15s",
                color: copied ? "success.main" : "text.secondary",
                p: 0.5,
              }}
            >
              {copied ? <CheckIcon sx={{ fontSize: 16 }} /> : <ContentCopyIcon sx={{ fontSize: 16 }} />}
            </IconButton>
          </Tooltip>
        )}

        <Box
          sx={{
            maxHeight: !expanded && isLong ? COLLAPSED_HEIGHT : "none",
            overflow: "hidden",
          }}
        >
          <Typography
            variant="body2"
            sx={{ lineHeight: 1.75, color: "text.primary", whiteSpace: "pre-wrap" }}
          >
            {safeContent}
          </Typography>
        </Box>

        {isLong && (
          <ButtonBase
            onClick={() => setExpanded((v) => !v)}
            sx={{
              mt: 1,
              display: "flex",
              alignItems: "center",
              gap: 0.5,
              color: "text.secondary",
              fontSize: 12,
              fontWeight: 600,
              "&:hover": { color: "text.primary" },
            }}
          >
            {expanded ? <KeyboardArrowUpIcon fontSize="small" /> : <KeyboardArrowDownIcon fontSize="small" />}
            {expanded ? "Show less" : "Show more"}
          </ButtonBase>
        )}
      </Box>
    </Box>
  );
};

export default SpanContent;
