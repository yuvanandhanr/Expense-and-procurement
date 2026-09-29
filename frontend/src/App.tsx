import React from "react";
import { HashRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import { AuthProvider } from "./hooks/useAuth";
import { ThemeProvider } from "./hooks/useTheme";
import { AppRoutes } from "./routes/AppRoutes";

import { ErrorBoundary } from "./components/ErrorBoundary";

// Construct TanStack Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <AuthProvider>
            <HashRouter>
              <AppRoutes />
              {/* Global toast notifications config */}
              <Toaster
                position="top-center"
                containerStyle={{
                  top: '12px',
                }}
                toastOptions={{
                  className: "bg-card text-card-foreground border border-border shadow-md rounded-lg text-sm",
                  duration: 4000,
                }}
              />
            </HashRouter>
          </AuthProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};
export default App;
