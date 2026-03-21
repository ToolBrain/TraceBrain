import React from "react";
import { Box, Typography } from "@mui/material";
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
                  {thought && (
                    <SpanContent
                      key={`${span.span_id}-thought`}
                      title="Thought"
                      subtitle="AI"
                      content={thought}
                      hasError={hasError}
                    />
                  )}
                  {toolCode && (
                    <SpanContent
                      key={`${span.span_id}-tool-code`}
                      title="Tool Call"
                      subtitle="AI"
                      content={toolCode}
                      hasError={hasError}
                    />
                  )}
                  {output && (
                    <SpanContent
                      key={`${span.span_id}-output`}
                      title="Output"
                      subtitle="AI"
                      content={output}
                      hasError={hasError}
                    />
                  )}
                </>
              )}

              {hasError && errorDescription && (
                <SpanContent
                  key={`${span.span_id}-error`}
                  title="Error Description"
                  subtitle="Tool"
                  content={errorDescription}
                  hasError={hasError}
                />
              )}

              {usage && <TokenUsageBar usage={usage} hasError={hasError} />}
            </>
          )}
        </Box>
      </Box>
    </>
  );
};

export default SpanDetails;