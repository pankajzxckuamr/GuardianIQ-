import { AuthProvider } from "./context/AuthContext";
import { AppRouter } from "./routes/AppRouter";
import "./styles/app.css";

export default function App() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  );
}
