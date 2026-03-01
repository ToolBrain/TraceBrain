import { Chip } from "@mui/material";
import { Schedule, VerifiedUser } from "@mui/icons-material";

export const ALLOWED_STATUSES = [
  "running",
  "completed",
  "needs_review",
  "failed",
  "success",
  "error",
  "pending",
  "pending_review",
  "auto_verified",
  "high",
  "medium",
  "low",
] as const;

export type ChipStatus = (typeof ALLOWED_STATUSES)[number];

export const STATUS_STYLES: Record<
  ChipStatus,
  { color: string; bg: string; border: string; label: string }
> = {
  running: {
    color: "#0c4a6e",
    bg: "#e0f2fe",
    border: "#38bdf8",
    label: "RUNNING",
  },
  success: {
    color: "#155724",
    bg: "#e9f4ea",
    border: "#34c759",
    label: "SUCCESS",
  },
  completed: {
    color: "#065f46",
    bg: "#d1fae5",
    border: "#10b981",
    label: "COMPLETED",
  },
  needs_review: {
    color: "#7c2d12",
    bg: "#fff7ed",
    border: "#f97316",
    label: "REVIEW",
  },
  error: {
    color: "#721c24",
    bg: "#fbe9eb",
    border: "#ff4d4f",
    label: "ERROR",
  },
  failed: {
    color: "#991b1b",
    bg: "#fee2e2",
    border: "#ef4444",
    label: "FAILED",
  },
  pending: {
    color: "#92400e",
    bg: "#fef3c7",
    border: "#f59e0b",
    label: "PENDING",
  },
  pending_review: {
    color: "#7c2d12",
    bg: "#fff7ed",
    border: "#f97316",
    label: "PENDING REVIEW",
  },
  auto_verified: {
    color: "#065f46",
    bg: "#d1fae5",
    border: "#10b981",
    label: "AUTO VERIFIED",
  },
  high: {
    color: "#991b1b",
    bg: "#fee2e2",
    border: "#ef4444",
    label: "HIGH",
  },
  medium: {
    color: "#92400e",
    bg: "#fed7aa",
    border: "#f97316",
    label: "MEDIUM",
  },
  low: {
    color: "#1e40af",
    bg: "#dbeafe",
    border: "#3b82f6",
    label: "LOW",
  },
};

const PULSE_LIST: ChipStatus[] = ["needs_review", "pending_review", "high"];

const STATUS_ICONS: Partial<Record<ChipStatus, React.ReactElement>> = {
  pending_review: <Schedule sx={{ fontSize: 16 }} />,
  auto_verified: <VerifiedUser sx={{ fontSize: 16 }} />,
};

interface StatusChipProps {
  status: ChipStatus;
  secondary?: boolean;
}

const StatusChip: React.FC<StatusChipProps> = ({
  status,
  secondary = false,
}) => {
  const styles = STATUS_STYLES[status];
  const shouldPulse = PULSE_LIST.includes(status);

  return (
    <Chip
      label={styles.label}
      size="small"
      icon={STATUS_ICONS[status]}
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
        ...(shouldPulse && {
          animation: "pulse 1.5s ease-out infinite",
          "@keyframes pulse": {
            "0%": {
              boxShadow: `0 0 0 0 ${styles.border}66`,
            },
            "100%": {
              boxShadow: `0 0 0 0.5rem ${styles.border}00`,
            },
          },
        }),
      }}
    />
  );
};

export default StatusChip;
