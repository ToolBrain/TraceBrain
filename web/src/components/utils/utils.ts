// Export to JSON
export const exportJSON = async (data: any) => {
  try {
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `data-${new Date().toISOString()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error("Error exporting JSON:", error);
  }
};

// Export to JSONL
export const exportJSONL = async (data: any) => {
  try {
    const blob = new Blob([data], {
      type: "application/jsonl",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `data-${new Date().toISOString()}.jsonl`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error("Error exporting JSONL:", error);
  }
};

export const formatDateTime = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleString("en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
};

// Parse LLM content from JSON string and extract the last message's role and content
export function parseLLMContent(newContent: string): {
  subtitle: string;
  content: string;
} {
  try {
    const parsed = JSON.parse(newContent);
    if (Array.isArray(parsed) && parsed.length > 0) {
      const lastItem = parsed[parsed.length - 1];
      if (lastItem && typeof lastItem === "object") {
        return {
          subtitle: String(lastItem.role ?? ""),
          content: String(lastItem.content ?? ""),
        };
      }
    }
  } catch {
    // Fallback to raw content when parsing fails.
  }
  return { subtitle: "", content: newContent };
}

export const getConfidenceColor = (
  aiConfidence: number | null,
): "inherit" | "error" | "warning" | "success" =>
  aiConfidence === null
    ? "inherit"
    : aiConfidence < 0.5
      ? "error"
      : aiConfidence < 0.8
        ? "warning"
        : "success";

export const getPriorityColor = (priority: number | null): string => {
  if (priority === null) return "error.light";
  return priority >= 4
    ? "error.main" // (4-5) High priority
    : priority >= 3
      ? "warning.main" // (3) Medium priority
      : "error.light"; // (1-2) Low priority
};

export const toTitleCase = (s: string) => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();

export const formatDuration = (seconds: number): string => {
  if (seconds < 0.01) return `${(seconds * 1000).toFixed(0)}ms`;
  if (seconds < 60) return `${seconds.toFixed(2)}s`;
  const m = Math.floor(seconds / 60);
  const s = (seconds % 60).toFixed(0);
  return `${m}m ${s}s`;
};