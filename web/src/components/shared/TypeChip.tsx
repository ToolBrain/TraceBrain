import { Chip } from "@mui/material";

const TYPE_STYLES = {
  trace: {
    label: "Trace",
    color: "#3730a3",
    backgroundColor: "#eef2ff",
    borderColor: "#c7d2fe",
  },
  episode: {
    label: "Episode",
    color: "#6b21a8",
    backgroundColor: "#faf5ff",
    borderColor: "#e9d5ff",
  },
} as const;

export type ChipType = keyof typeof TYPE_STYLES;

interface TypeChipProps {
  type: ChipType;
  secondary?: boolean;
}

const TypeChip: React.FC<TypeChipProps> = ({ type, secondary = false }) => {
  const styles = TYPE_STYLES[type];

  return (
    <Chip
      label={styles.label}
      size="small"
      sx={{
        alignSelf: "flex-start",
        height: 24,
        minWidth: 75,
        fontSize: "0.75rem",
        fontWeight: 600,
        color: styles.color,
        backgroundColor: styles.backgroundColor,
        border: "1px solid",
        borderColor: styles.borderColor,
        borderRadius: 3,
        p: 0.5,
        opacity: secondary ? 0.7 : 1,
      }}
    />
  );
};

export default TypeChip;
