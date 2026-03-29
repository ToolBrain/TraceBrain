import {
  createContext,
  useContext,
  useState,
  useEffect,
  useMemo,
  type ReactNode,
} from "react";
import { produce } from "immer";

type ProviderName = "openai" | "gemini" | "anthropic" | "huggingface";

interface LLMSettingsPayload {
  librarian_provider: ProviderName;
  librarian_model: string;
  judge_provider: ProviderName;
  judge_model: string;
  curator_provider: ProviderName;
  curator_model: string;
  openai_api_key: string;
  gemini_api_key: string;
  anthropic_api_key: string;
  huggingface_api_key: string;
}

interface Settings {
  appearance: {
    theme: "light" | "dark";
  };
  refresh: {
    autoRefresh: boolean;
    refreshInterval: number;
  };
  llm: {
    provider: ProviderName;
    model: string;
    autoEvaluate: boolean;
    batchSize: number;
  };
  chatLLM: {
    provider: ProviderName;
    model: string;
  };
  curatorLLM: {
    provider: ProviderName;
    model: string;
  };
  apiKeys: {
    openai: string;
    gemini: string;
    anthropic: string;
    huggingface: string;
  };
}

interface SettingsContextType {
  settings: Settings;
  updateSettings: (updater: (draft: Settings) => void) => void;
  saveSettings: () => Promise<boolean>;
  hasUnsavedChanges: boolean;
  isLoading: boolean;
  isSaving: boolean;
  saveError: string | null;
}

const DEFAULT_SETTINGS: Settings = {
  appearance: { theme: "light" },
  refresh: { autoRefresh: false, refreshInterval: 30 },
  llm: { provider: "gemini", model: "gemini-2.5-flash", autoEvaluate: true },
  chatLLM: { provider: "gemini", model: "gemini-2.5-flash" },
  curatorLLM: { provider: "gemini", model: "gemini-2.5-flash" },
  apiKeys: { openai: "", gemini: "", anthropic: "", huggingface: "" },
};

const fillDefaults = (defaults: any, saved: any): any =>
  Object.keys(defaults).reduce(
    (result, key) => {
      if (!(key in saved)) {
        result[key] = defaults[key];
      } else if (
        typeof defaults[key] === "object" &&
        defaults[key] !== null &&
        !Array.isArray(defaults[key])
      ) {
        result[key] = fillDefaults(defaults[key], saved[key]);
      } else {
        result[key] = saved[key];
      }
      return result;
    },
    { ...saved },
  );

const isProvider = (value: unknown): value is ProviderName =>
  value === "openai" || value === "gemini" || value === "anthropic" || value === "huggingface";

const toBackendPayload = (settings: Settings): LLMSettingsPayload => ({
  librarian_provider: settings.chatLLM.provider,
  librarian_model: settings.chatLLM.model,
  judge_provider: settings.llm.provider,
  judge_model: settings.llm.model,
  curator_provider: settings.curatorLLM.provider,
  curator_model: settings.curatorLLM.model,
  openai_api_key: settings.apiKeys.openai,
  gemini_api_key: settings.apiKeys.gemini,
  anthropic_api_key: settings.apiKeys.anthropic,
  huggingface_api_key: settings.apiKeys.huggingface,
});

const applyBackendSettings = (base: Settings, payload: Partial<LLMSettingsPayload>): Settings =>
  produce(base, (draft) => {
    if (isProvider(payload.judge_provider)) {
      draft.llm.provider = payload.judge_provider;
    }
    if (typeof payload.judge_model === "string" && payload.judge_model.trim()) {
      draft.llm.model = payload.judge_model.trim();
    }
    if (isProvider(payload.librarian_provider)) {
      draft.chatLLM.provider = payload.librarian_provider;
    }
    if (typeof payload.librarian_model === "string" && payload.librarian_model.trim()) {
      draft.chatLLM.model = payload.librarian_model.trim();
    }
    if (isProvider(payload.curator_provider)) {
      draft.curatorLLM.provider = payload.curator_provider;
    }
    if (typeof payload.curator_model === "string" && payload.curator_model.trim()) {
      draft.curatorLLM.model = payload.curator_model.trim();
    }
    if (typeof payload.openai_api_key === "string") {
      draft.apiKeys.openai = payload.openai_api_key.trim();
    }
    if (typeof payload.gemini_api_key === "string") {
      draft.apiKeys.gemini = payload.gemini_api_key.trim();
    }
    if (typeof payload.anthropic_api_key === "string") {
      draft.apiKeys.anthropic = payload.anthropic_api_key.trim();
    }
    if (typeof payload.huggingface_api_key === "string") {
      draft.apiKeys.huggingface = payload.huggingface_api_key.trim();
    }
  });

const SettingsContext = createContext<SettingsContextType | undefined>(
  undefined,
);

export const SettingsProvider = ({ children }: { children: ReactNode }) => {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);
  const [persistedPayload, setPersistedPayload] = useState<string>(
    JSON.stringify(toBackendPayload(DEFAULT_SETTINGS)),
  );
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const hasUnsavedChanges = useMemo(
    () => JSON.stringify(toBackendPayload(settings)) !== persistedPayload,
    [persistedPayload, settings],
  );

  useEffect(() => {
    fetch("/api/v1/settings")
      .then((res) => {
        if (!res.ok) throw new Error("Settings not found");
        return res.json();
      })
      .then((data) => {
        const merged = fillDefaults(DEFAULT_SETTINGS, {});
        const mapped = applyBackendSettings(merged, data || {});

        setSettings(mapped);
        setPersistedPayload(JSON.stringify(toBackendPayload(mapped)));
        setIsLoading(false);
      })
      .catch(() => {
        setSettings(DEFAULT_SETTINGS);
        setPersistedPayload(JSON.stringify(toBackendPayload(DEFAULT_SETTINGS)));
        setIsLoading(false);
      });
  }, []);

  const updateSettings = (updater: (draft: Settings) => void) => {
    setSettings((prev) => {
      const updated = produce(prev, updater);
      return updated;
    });
  };

  const saveSettings = async (): Promise<boolean> => {
    setIsSaving(true);
    setSaveError(null);
    try {
      const response = await fetch("/api/v1/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(toBackendPayload(settings)),
      });

      if (!response.ok) {
        let detail = "Failed to save settings";
        try {
          const errorData = await response.json();
          if (typeof errorData?.detail === "string" && errorData.detail.trim()) {
            detail = errorData.detail;
          }
        } catch {
          // Keep default message when response is not JSON.
        }
        throw new Error(detail);
      }

      const payload = await response.json();
      const merged = applyBackendSettings(settings, payload || {});
      setSettings(merged);
      setPersistedPayload(JSON.stringify(toBackendPayload(merged)));
      return true;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to save settings";
      setSaveError(message);
      return false;
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <SettingsContext.Provider
      value={{
        settings,
        updateSettings,
        saveSettings,
        hasUnsavedChanges,
        isLoading,
        isSaving,
        saveError,
      }}
    >
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context)
    throw new Error("useSettings must be used within SettingsProvider");
  return context;
};
