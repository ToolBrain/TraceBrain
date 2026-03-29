import React, { useState } from "react";
import { Box, Typography, ButtonBase, IconButton, Tooltip, Divider } from "@mui/material";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import CheckIcon from "@mui/icons-material/Check";
import WarningAmberRoundedIcon from "@mui/icons-material/WarningAmberRounded";

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
  const [copied, setCopied] = useState(false);
  const errorColor = "rgba(220, 38, 38, 0.04)";
  const successColor = "rgba(34, 197, 94, 0.04)";
  const warningColor = "rgba(245, 158, 11, 0.04)";
  const borderColor = hasError ? "rgba(220, 38, 38, 0.3)" : "rgba(34, 197, 94, 0.3)";
  const warningBorderColor = "rgba(245, 158, 11, 0.4)";

  const isMissing = content === null || content === undefined;
  const safeContent = content ?? "";
  const isLong = safeContent.length > 400;
  const showCopy = safeContent.length > 0;

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
          bgcolor: isMissing ? warningColor : hasError ? errorColor : successColor,
          border: 1,
          borderColor: isMissing ? warningBorderColor : borderColor,
          borderStyle: isMissing ? "dashed" : "solid",
          position: "relative",
          "&:hover .copy-btn": { opacity: 1 },
        }}
      >
        {subtitle && (
          <>
            <Box
              sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1 }}
            >
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 0.5,
                  cursor: isLong ? "pointer" : "default",
                }}
                onClick={() => isLong && setExpanded((v) => !v)}
              >
                {isLong &&
                  (expanded ? (
                    <KeyboardArrowUpIcon fontSize="small" sx={{ color: "text.secondary" }} />
                  ) : (
                    <KeyboardArrowDownIcon fontSize="small" sx={{ color: "text.secondary" }} />
                  ))}
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
              </Box>
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
                    {copied ? (
                      <CheckIcon sx={{ fontSize: 16 }} />
                    ) : (
                      <ContentCopyIcon sx={{ fontSize: 16 }} />
                    )}
                  </IconButton>
                </Tooltip>
              )}
            </Box>
            <Divider sx={{ mx: -2.5, mb: 1.5, borderColor: isMissing ? warningBorderColor : borderColor, borderStyle: isMissing ? "dashed" : "solid" }} />
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
              {copied ? (
                <CheckIcon sx={{ fontSize: 16 }} />
              ) : (
                <ContentCopyIcon sx={{ fontSize: 16 }} />
              )}
            </IconButton>
          </Tooltip>
        )}

        {isMissing ? (
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <WarningAmberRoundedIcon sx={{ fontSize: 16, color: "warning.main" }} />
            <Typography variant="body2" sx={{ color: "warning.main", fontStyle: "italic" }}>
              No data available
            </Typography>
          </Box>
        ) : (
          <>
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
                  fontWeight: 600,
                  "&:hover": { color: "text.primary" },
                }}
              >
                {expanded ? (
                  <KeyboardArrowUpIcon fontSize="small" />
                ) : (
                  <KeyboardArrowDownIcon fontSize="small" />
                )}
                {expanded ? "Show less" : "Show more"}
              </ButtonBase>
            )}
          </>
        )}
      </Box>
    </Box>
  );
};

export default SpanContent;