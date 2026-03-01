import { Chip } from "@mui/material";

export const ALLOWED_ERROR_TYPES = [
  "logic_loop",
  "hallucination",
  "invalid_tool_usage",
  "tool_execution_error",
  "format_error",
  "misinterpretation",
  "context_overflow",
  "general_failure",
] as const;

export type ErrorType = (typeof ALLOWED_ERROR_TYPES)[number];

export const ERROR_TYPE_STYLES: Record<
  ErrorType,
  { color: string; bg: string; border: string; label: string }
> = {
  logic_loop: {
    color: "#7f1d1d",
    bg: "#fecaca",
    border: "#dc2626",
    label: "LOOP ERROR",
  },
  hallucination: {
    color: "#6b21a8",
    bg: "#faf5ff",
    border: "#c084fc",
    label: "HALLUCINATION",
  },
  invalid_tool_usage: {
    color: "#92400e",
    bg: "#fef3c7",
    border: "#f59e0b",
    label: "INVALID TOOL",
  },
  tool_execution_error: {
    color: "#7c2d12",
    bg: "#fff7ed",
    border: "#f97316",
    label: "EXECUTION ERROR",
  },
  format_error: {
    color: "#1e40af",
    bg: "#dbeafe",
    border: "#3b82f6",
    label: "FORMAT ERROR",
  },
  misinterpretation: {
    color: "#065f46",
    bg: "#d1fae5",
    border: "#10b981",
    label: "MISINTERPRETATION",
  },
  context_overflow: {
    color: "#0c4a6e",
    bg: "#e0f2fe",
    border: "#38bdf8",
    label: "CONTEXT OVERFLOW",
  },
  general_failure: {
    color: "#374151",
    bg: "#f3f4f6",
    border: "#9ca3af",
    label: "GENERAL FAILURE",
  },
};

interface ErrorTypeChipProps {
  errorType: ErrorType;
  secondary?: boolean;
}

const ErrorTypeChip: React.FC<ErrorTypeChipProps> = ({ errorType, secondary = false }) => {
  const styles = ERROR_TYPE_STYLES[errorType];

  return (
    <Chip
      label={styles.label}
      size="small"
      sx={{
        fontWeight: 600,
        fontSize: "0.75rem",
        borderRadius: "1rem",
        color: styles.color,
        backgroundColor: styles.bg,
        border: `1px solid ${styles.border}`,
        minWidth: 100,
        textAlign: "center",
        opacity: secondary ? 0.7 : 1,
      }}
    />
  );
};

export default ErrorTypeChip;