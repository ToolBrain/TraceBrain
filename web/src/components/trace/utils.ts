// Parse LLM content from JSON string and extract the last message's role and content
export function parseLLMContent(newContent: string): { subtitle: string; content: string } {
  const parsed = JSON.parse(newContent);
  const lastItem = parsed[parsed.length - 1];
  return {
    subtitle: lastItem.role,
    content: lastItem.content
  };
}