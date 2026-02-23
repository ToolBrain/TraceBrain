import { Box, Typography } from "@mui/material";
import { PieChart } from "@mui/x-charts/PieChart";
import { useMemo } from "react";
import type { Trace } from "../../types/trace";
import { ERROR_TYPE_STYLES } from "../shared/ErrorTypeChip";
import { traceGetErrorType, traceGetEvaluation } from "../utils/traceUtils";

interface TraceErrorChartProps {
  traces: Trace[];
}

const TraceErrorChart: React.FC<TraceErrorChartProps> = ({ traces }) => {
  const { pieData, stats } = useMemo(() => {
    const errorCounts: Record<string, number> = {};
    let failedCount = 0;
    let totalConfidence = 0;
    let confidenceCount = 0;

    traces.forEach((trace) => {
      const errorType = traceGetErrorType(trace);
      const evaluation = traceGetEvaluation(trace);

      if (errorType && errorType !== "none") {
        errorCounts[errorType] = (errorCounts[errorType] ?? 0) + 1;
        failedCount++;
      }

      if (evaluation?.confidence !== undefined) {
        totalConfidence += evaluation.confidence;
        confidenceCount++;
      }
    });

    const total = traces.length;
    const failureRate =
      total > 0 ? ((failedCount / total) * 100).toFixed(0) : "0";
    const successRate =
      total > 0 ? (((total - failedCount) / total) * 100).toFixed(0) : "100";
    const avgConfidence =
      confidenceCount > 0
        ? ((totalConfidence / confidenceCount) * 100).toFixed(0)
        : "N/A";
    const errorTypeCount = Object.keys(errorCounts).length;

    const pieData = Object.entries(errorCounts).map(([key, value], id) => ({
      id,
      value,
      label: ERROR_TYPE_STYLES[key].label,
      color: ERROR_TYPE_STYLES[key].border,
    }));

    return {
      pieData,
      stats: {
        total,
        failedCount,
        failureRate,
        successRate,
        avgConfidence,
        errorTypeCount,
      },
    };
  }, [traces]);

  const traceSummary = [
    { label: "Total Traces", value: stats.total },
    { label: "Failed Traces", value: stats.failedCount },
    { label: "Success Rate", value: `${stats.successRate}%` },
    { label: "Failure Rate", value: `${stats.failureRate}%` },
    {
      label: "Average Confidence",
      value: stats.avgConfidence !== "N/A" ? `${stats.avgConfidence}%` : "N/A",
    },
    { label: "Error Types", value: stats.errorTypeCount },
  ];

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 3,
        px: 2,
        py: 1,
        height: "100%",
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 2,
          bgcolor: "action.hover",
          borderRadius: 2,
          p: 1.5,
          flexShrink: 0,
          outline: "1px solid",
          outlineColor: "divider",
        }}
      >
        {/* Pie Chart */}
        <Box sx={{ flexShrink: 0 }}>
          <Typography
            variant="caption"
            color="text.secondary"
            fontWeight={600}
            sx={{ mb: 1, display: "block", textAlign: "center" }}
          >
            ERROR DISTRIBUTION
          </Typography>
          {pieData.length > 0 ? (
            <PieChart
              series={[
                {
                  data: pieData,
                  innerRadius: 60,
                  outerRadius: 95,
                  paddingAngle: 2,
                  cornerRadius: 4,
                },
              ]}
              width={200}
              height={200}
              sx={{ "& .MuiChartsLegend-root": { display: "none" } }}
            />
          ) : (
            <Box sx={{ width: 200, height: 200 }} />
          )}
        </Box>

        {/* Legend */}
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 0.75,
            minWidth: 160,
          }}
        >
          {pieData.map((item) => (
            <Box
              key={item.id}
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 1,
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.75 }}>
                <Box
                  sx={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    bgcolor: item.color,
                    flexShrink: 0,
                  }}
                />
                <Typography variant="caption" color="text.secondary">
                  {item.label}
                </Typography>
              </Box>
              <Typography variant="caption" fontWeight={600}>
                {item.value}
              </Typography>
            </Box>
          ))}
        </Box>
      </Box>

      {/* Statistics */}
      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 1.5,
          flex: 1,
        }}
      >
        {traceSummary.map(({ label, value }) => (
          <Box
            key={label}
            sx={{
              bgcolor: "action.hover",
              borderRadius: 2,
              p: 2,
              display: "flex",
              flexDirection: "column",
              gap: 0.5,
              outline: "1px solid",
              outlineColor: "divider",
            }}
          >
            <Typography variant="caption" color="text.secondary">
              {label}
            </Typography>
            <Typography variant="h6" fontWeight={600} lineHeight={1}>
              {value}
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
};

export default TraceErrorChart;
