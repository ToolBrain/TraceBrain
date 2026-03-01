export interface MessageContent {
  answer: string;
  suggestions?: Suggestion[];
  sources?: string[];
}

export interface Message {
  role: "user" | "assistant";
  content: MessageContent;
}

export interface Suggestion {
  label: string;
  value: string;
}

interface SendMessageRequest {
  content: string;
  sessionId: string | null;
  model: string;
}

interface SendMessageResponse {
  sessionId: string;
  answer: string;
  suggestions: Suggestion[];
  sources?: string[];
}

export class ChatEngine {
  private baseUrl: string;
  private storage: Storage;
  private readonly SESSION_KEY = "chat_session_id";

  constructor(baseUrl: string, storage: Storage = localStorage) {
    this.baseUrl = baseUrl;
    this.storage = storage;
  }

  async fetchSession(sessionId: string): Promise<Message[]> {
    const response = await fetch(
      `${this.baseUrl}/librarian_sessions/${sessionId}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      },
    );

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error("Session not found");
      }
      throw new Error(`Failed to fetch session: ${response.statusText}`);
    }

    const data = await response.json();

    return data.messages
      .filter((msg: any) => msg.role === "user" || msg.role === "assistant")
      .map((msg: any) => ({
        role: msg.role,
        content: msg.content,
      }));
  }

  async sendMessage(params: SendMessageRequest): Promise<SendMessageResponse> {
    const { content, sessionId, model } = params;

    const response = await fetch(`${this.baseUrl}/natural_language_query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: content,
        session_id: sessionId,
        model_id: model,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to send message: ${response.statusText}`);
    }

    const data = await response.json();

    return {
      sessionId: data.session_id,
      answer: data.answer,
      suggestions: data.suggestions || [],
      sources: data.sources || undefined,
    };
  }

  getSessionId(): string | null {
    return this.storage.getItem(this.SESSION_KEY);
  }

  setSessionId(sessionId: string): void {
    this.storage.setItem(this.SESSION_KEY, sessionId);
  }

  clearSessionStorage(): void {
    this.storage.removeItem(this.SESSION_KEY);
  }

  buildUserMessage(content: string): Message {
    return {
      role: "user",
      content: { answer: content },
    };
  }

  buildAssistantMessage(response: SendMessageResponse): Message {
    return {
      role: "assistant",
      content: {
        answer: response.answer,
        suggestions: response.suggestions,
        sources: response.sources,
      },
    };
  }
}
