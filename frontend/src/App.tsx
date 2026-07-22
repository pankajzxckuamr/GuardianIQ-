import { AuthProvider } from "./context/AuthContext";
import { ToastProvider } from "./context/ToastContext";
import { SessionProvider } from "./context/SessionContext";
import { NavigationProvider } from "./context/NavigationContext";
import { FilterProvider } from "./context/FilterContext";
import { AppRouter } from "./routes/AppRouter";
import "./styles/app.css";

export default function App() {
  return (
    <AuthProvider>
      <SessionProvider>
        <NavigationProvider>
          <FilterProvider>
            <ToastProvider>
              <AppRouter />
            </ToastProvider>
          </FilterProvider>
        </NavigationProvider>
      </SessionProvider>
    </AuthProvider>
  );
}
