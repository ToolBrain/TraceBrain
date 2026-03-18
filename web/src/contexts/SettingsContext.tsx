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
    autoEvaluate: boolean;
    batchSize: number;
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
  llm: { model: "gemini-2.5-flash", autoEvaluate: true, batchSize: 5 },
  chatLLM: { model: "gemini-2.5-flash" },
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
        const merged = fillDefaults(DEFAULT_SETTINGS, data);
        const hasNewKeys = JSON.stringify(merged) !== JSON.stringify(data);

        setSettings(merged);
        setIsLoading(false);

        if (hasNewKeys) {
          fetch("/api/v1/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(merged),
          }).catch((err) => console.error("Failed to save default settings:", err));
        }
      })
      .catch(() => {
        fetch("/api/v1/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(DEFAULT_SETTINGS),
        }).catch((err) => console.error("Failed to save default settings:", err));

        setSettings(DEFAULT_SETTINGS);
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
