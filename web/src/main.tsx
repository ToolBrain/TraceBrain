import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { BrowserRouter } from "react-router-dom";
import { AppProvider } from "@toolpad/core/AppProvider";
import { SettingsProvider } from "./contexts/SettingsContext";
import { ChatProvider } from "./contexts/ChatContext.tsx";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient();

createRoot(document.getElementById("root")!).render(
  <BrowserRouter>
    <QueryClientProvider client={queryClient}>
      <AppProvider>
        <SettingsProvider>
          <ChatProvider>
            <App />
          </ChatProvider>
        </SettingsProvider>
      </AppProvider>
    </QueryClientProvider>
  </BrowserRouter>,
);
