import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import { useSettings } from "./SettingsContext";
import {
  ChatEngine,
  type Message,
  type Suggestion,
} from "../components/chat/engine/chatEngine";

interface ChatContextType {
  messages: Message[];
  suggestions: Suggestion[];
  isLoading: boolean;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
}

const ChatContext = createContext<ChatContextType | null>(null);

const chatEngine = new ChatEngine("/api/v1");

export function ChatProvider({ children }: { children: ReactNode }) {
  const { settings } = useSettings();
  const [sessionId, setSessionId] = useState<string | null>(() =>
    chatEngine.getSessionId(),
  );
  const [messages, setMessages] = useState<Message[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Persist session ID
  useEffect(() => {
    if (sessionId) {
      chatEngine.setSessionId(sessionId);
    } else {
      chatEngine.clearSessionStorage();
    }
  }, [sessionId]);

  // Load existing session
  useEffect(() => {
    if (!sessionId) return;

    chatEngine
      .fetchSession(sessionId)
      .then((loadedMessages) => setMessages(loadedMessages))
      .catch(() => {
        setSessionId(null);
      });
  }, []);

  async function sendMessage(content: string) {
    setIsLoading(true);
    try {
      const result = await chatEngine.sendMessage({
        content,
        sessionId,
        model: settings.llm.model,
      });

      setSessionId(result.sessionId);
      setMessages((prev) => [
        ...prev,
        { role: "user", content },
        { role: "assistant", content: result.answer },
      ]);
      setSuggestions(result.suggestions ?? []);
    } catch (err) {
      console.error("Chat error:", err);
      setMessages((prev) => [
        ...prev,
        { role: "user", content },
        {
          role: "assistant",
          content: "Something went wrong. Please try again.",
        },
      ]);
      setSuggestions([]);
    } finally {
      setIsLoading(false);
    }
  }

  function clearMessages() {
    setSessionId(null);
    setMessages([]);
    setSuggestions([]);
    chatEngine.clearSessionStorage();
  }

  return (
    <ChatContext.Provider
      value={{
        messages,
        suggestions,
        isLoading,
        sendMessage,
        clearMessages,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat(): ChatContextType {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
}
