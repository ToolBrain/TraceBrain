import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { BrowserRouter } from "react-router-dom";
import { AppProvider } from "@toolpad/core/AppProvider";
import { SettingsProvider } from "./contexts/SettingsContext";
import { ChatProvider } from "./contexts/ChatContext.tsx";

createRoot(document.getElementById("root")!).render(
  <BrowserRouter>
    <AppProvider>
      <SettingsProvider>
        <ChatProvider>
          <App />
        </ChatProvider>
      </SettingsProvider>
    </AppProvider>
  </BrowserRouter>,
);
