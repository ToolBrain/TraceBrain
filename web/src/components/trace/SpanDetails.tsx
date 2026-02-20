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
  const usage = span ? spanGetUsage(span) : null;
  const input = span ? spanGetInput(span) : "";
  const output = span ? spanGetOutput(span) : "";
  const systemPrompt = span ? spanGetSystemPrompt(span) : "";

  return (
    <Box
      sx={{
        width: "75%",
        bgcolor: "background.paper",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        minHeight: 0,
        overflow: "hidden",
      }}
    >
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
            p: 2,
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
                title="System Prompt"
                subtitle="System"
                content={systemPrompt}
                hasError={hasError}
              />

              {spanType === "tool_execution" && (
                <>
                  <SpanContent
                    title="Tool"
                    subtitle="Tool"
                    content={toolName}
                    hasError={hasError}
                  />
                  <SpanContent
                    title="Input"
                    subtitle="AI"
                    content={input}
                    hasError={hasError}
                  />
                  <SpanContent
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
            </>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default SpanDetails;
