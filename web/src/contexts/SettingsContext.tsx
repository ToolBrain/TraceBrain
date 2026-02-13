import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import { produce } from "immer";

interface Settings {
  appearance: {
    theme: "light" | "dark";
  };
  refresh: {
    autoRefresh: boolean;
    refreshInterval: number;
  };
  llm: {
    model: string;
  };
  chatLLM: {
    model: string;
  };
}

interface SettingsContextType {
  settings: Settings;
  updateSettings: (updater: (draft: Settings) => void) => void;
  isLoading: boolean;
}

const DEFAULT_SETTINGS: Settings = {
  appearance: { theme: "light" },
  refresh: { autoRefresh: false, refreshInterval: 30 },
  llm: { model: "gemini-2.5-flash" },
  chatLLM: { model: "gemini-2.5-flash" },
};

const SettingsContext = createContext<SettingsContextType | undefined>(
  undefined,
);

export const SettingsProvider = ({ children }: { children: ReactNode }) => {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetch("/api/v1/settings")
      .then((res) => {
        if (!res.ok) throw new Error("Settings not found");
        return res.json();
      })
      .then((data) => {
        setSettings({ ...DEFAULT_SETTINGS, ...data });
        setIsLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load settings:", err);
        setIsLoading(false);
      });
  }, []);

  const updateSettings = (updater: (draft: Settings) => void) => {
    setSettings((prev) => {
      const updated = produce(prev, updater);

      fetch("/api/v1/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updated),
      }).catch((err) => console.error("Failed to save settings:", err));

      return updated;
    });
  };

  return (
    <SettingsContext.Provider value={{ settings, updateSettings, isLoading }}>
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
