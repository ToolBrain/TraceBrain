import React from "react";
import { Box, Typography } from "@mui/material";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import type { Span, Trace } from "../../types/trace";
import { parseLLMContent } from "../utils/utils";
import SpanContent from "./SpanContent";
import TokenUsageBar from "./TokenUsageBar";
import {
  spanGetType,
  spanGetToolName,
  spanHasError,
  spanGetUsage,
  spanGetInput,
  spanGetOutput,
  spanGetSystemPrompt,
  spanGetThought,
  spanGetToolCode,
  spanGetErrorDescription,
} from "../utils/spanUtils";
import EvaluationPanel from "./EvaluationPanel";

interface SpanDetailsProps {
  span: Span | null;
  trace: Trace | null;
}

const SpanDetails: React.FC<SpanDetailsProps> = ({ span, trace }) => {
  // Capturing JSON span attributes
  const spanType = span ? spanGetType(span) : "unknown";
  const toolName = span ? spanGetToolName(span) : "";
  const hasError = span ? spanHasError(span) : false;
  const errorDescription = span ? spanGetErrorDescription(span) : "";
  const usage = span ? spanGetUsage(span) : null;
  const input = span ? spanGetInput(span) : "";
  const output = span ? spanGetOutput(span) : "";
  const thought = span ? spanGetThought(span) : "";
  const toolCode = span ? spanGetToolCode(span) : "";
  const systemPrompt = spanGetSystemPrompt(span, trace);

  return (
    <>
      <EvaluationPanel trace={trace} />

      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Box
          sx={{
            py: 1.5,
            px: 2,
            borderBottom: 1,
            borderColor: "divider",
            bgcolor: "background.default",
            display: "flex",
            alignItems: "center",
            gap: 1,
          }}
        >
          <Typography variant="h6">Span Properties</Typography>
        </Box>

        <Box sx={{ flex: 1, minHeight: 0, overflowY: "auto", p: 2 }}>
          {!span && (
            <Box sx={{ textAlign: "center", color: "text.secondary" }}>
              Select a span to view details
            </Box>
          )}

          {span && (
            <>
              {hasError && errorDescription && (
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 1,
                    px: 1.5,
                    py: 1,
                    mb: 2,
                    bgcolor: "rgba(220, 38, 38, 0.04)",
                    border: "1px solid",
                    borderColor: "rgba(220, 38, 38, 0.15)",
                    borderRadius: 1,
                  }}
                >
                  <ErrorOutlineIcon fontSize="small" sx={{ color: "error.main" }} />
                  <Typography variant="caption" sx={{ color: "error.main", lineHeight: 1 }}>
                    {errorDescription}
                  </Typography>
                </Box>
              )}

              {spanType !== "llm_inference" && spanType !== "tool_execution" ? (
                <Box sx={{ textAlign: "center", color: "text.secondary" }}>
                  No properties to display for this span
                </Box>
              ) : (
                <>
                  <SpanContent
                    key={`${span.span_id}-system-prompt`}
                    title="System Prompt"
                    subtitle="System"
                    content={systemPrompt}
                    hasError={hasError}
                  />

                  {spanType === "tool_execution" && (
                    <>
                      <SpanContent
                        key={`${span.span_id}-tool`}
                        title="Tool"
                        subtitle="Tool"
                        content={toolName}
                        hasError={hasError}
                      />
                      <SpanContent
                        key={`${span.span_id}-input`}
                        title="Input"
                        subtitle="AI"
                        content={input}
                        hasError={hasError}
                      />
                      <SpanContent
                        key={`${span.span_id}-output`}
                        title="Output"
                        subtitle="Tool"
                        content={output}
                        hasError={hasError}
                      />
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
                                key={`${span.span_id}-input`}
                                title="Input"
                                subtitle={parsed.subtitle}
                                content={parsed.content}
                                hasError={hasError}
                              />
                            )
                          );
                        })()}
                      <SpanContent
                        key={`${span.span_id}-thought`}
                        title="Thought"
                        subtitle="AI"
                        content={thought}
                        hasError={hasError}
                      />
                      <SpanContent
                        key={`${span.span_id}-tool-code`}
                        title="Tool Call"
                        subtitle="AI"
                        content={toolCode}
                        hasError={hasError}
                      />
                      <SpanContent
                        key={`${span.span_id}-output`}
                        title="Output"
                        subtitle="AI"
                        content={output}
                        hasError={hasError}
                      />
                    </>
                  )}

                  {usage && <TokenUsageBar usage={usage} hasError={hasError} />}
                </>
              )}
            </>
          )}
        </Box>
      </Box>
    </>
  );
};

export default SpanDetails;
