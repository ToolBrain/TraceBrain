import React from "react";
import { Box, Typography, Chip } from "@mui/material";
import type { Span, Trace } from "../../types/trace";
import { parseLLMContent } from "./utils";
import SpanContent from "./SpanContent";
import TokenUsageBar from "./TokenUsageBar";
import AIEvaluation from "./AIEvaluation";
import {
  spanGetType,
  spanGetToolName,
  spanHasError,
  spanGetUsage,
  spanGetInput,
  spanGetOutput,
  spanGetSystemPrompt,
} from "../utils/spanUtils";
import { traceGetEvaluation } from "../utils/traceUtils";

interface TraceDetailsProps {
  span: Span | null;
  trace: Trace | null;
}

const TraceDetails: React.FC<TraceDetailsProps> = ({ span, trace }) => {
  // Show trace details when trace is selected
  if (trace) {
    const evaluation = traceGetEvaluation(trace);

    return (
      <Box
        sx={{ width: "75%", bgcolor: "background.paper", overflowY: "auto" }}
      >
        <Box
          sx={{
            p: 2,
            borderBottom: 1,
            borderColor: "divider",
            bgcolor: "background.default",
          }}
        >
          <Typography variant="h5">Trace Details</Typography>
        </Box>
        <Box sx={{ p: 2 }}>
          <Typography
            variant="body2"
            sx={{ mb: 2, fontFamily: "monospace", color: "text.secondary" }}
          >
            {"Trace ID: "}
            {trace.trace_id}
          </Typography>
          {evaluation && <AIEvaluation evaluation={evaluation} />}
        </Box>
      </Box>
    );
  }

  // Nothing if neither are selected
  if (!span) {
    return (
      <Box
        sx={{ width: "75%", bgcolor: "background.paper", overflowY: "auto" }}
      >
        <Box
          sx={{
            p: 2,
            borderBottom: 1,
            borderColor: "divider",
            bgcolor: "background.default",
          }}
        >
          <Typography variant="h5">Details</Typography>
        </Box>
        <Box sx={{ p: 2, textAlign: "center", color: "text.secondary" }}>
          Select a trace or span to view details
        </Box>
      </Box>
    );
  }

  // Show span details when span is selected
  const spanType = spanGetType(span);
  const toolName = spanGetToolName(span);
  const hasError = spanHasError(span);
  const usage = spanGetUsage(span);
  const input = spanGetInput(span);
  const output = spanGetOutput(span);
  const systemPrompt = spanGetSystemPrompt(span);

  return (
    <Box sx={{ width: "75%", bgcolor: "background.paper", overflowY: "auto" }}>
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: "divider",
          bgcolor: "background.default",
        }}
      >
        <Typography variant="h5">Span Details</Typography>
      </Box>
      <Box sx={{ p: 2 }}>
        <SpanContent
          title="System Prompt"
          subtitle="System"
          content={systemPrompt}
          hasError={hasError}
        />

        {spanType === "tool_execution" && (
          <>
            {
              <SpanContent
                title="Tool"
                subtitle="Tool"
                content={toolName}
                hasError={hasError}
              />
            }
            {
              <SpanContent
                title="Input"
                subtitle="AI"
                content={input}
                hasError={hasError}
              />
            }
            {
              <SpanContent
                title="Output"
                subtitle="Tool"
                content={output}
                hasError={hasError}
              />
            }
          </>
        )}

        {spanType === "llm_inference" && (
          <>
            {input &&
              (() => {
                const parsed = parseLLMContent(input);
                return (
                  parsed && (
                    <SpanContent
                      title="Input"
                      subtitle={parsed.subtitle}
                      content={parsed.content}
                      hasError={hasError}
                    />
                  )
                );
              })()}
            {output && (
              <SpanContent
                title="Output"
                subtitle="AI"
                content={output}
                hasError={hasError}
              />
            )}
          </>
        )}

        {usage && <TokenUsageBar usage={usage} hasError={hasError} />}
      </Box>
    </Box>
  );
};

export default TraceDetails;
