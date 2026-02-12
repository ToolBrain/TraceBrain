import { fetchExportCurriculum } from "./api";

// Handle export to JSON
export const handleExportJSON = async () => {
  try {
    const data = await fetchExportCurriculum("json");
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

// Handle export to JSONL
export const handleExportJSONL = async () => {
  try {
    const jsonlContent = await fetchExportCurriculum("jsonl");
    const blob = new Blob([jsonlContent], {
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
