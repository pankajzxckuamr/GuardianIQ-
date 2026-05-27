/* src/pages/LoginPage.tsx */
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { FormField } from "../components/common/FormField";
import { Button } from "../components/common/Button";
import { Card } from "../components/common/Card";
import { Shield, AlertCircle } from "lucide-react";
import "./LoginPage.css";

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setError("Please fill in all fields.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      navigate("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Invalid credentials or server error.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-backdrop-glow login-glow-1" />
      <div className="login-backdrop-glow login-glow-2" />
      
      <div className="login-container">
        <Card className="login-card" glow>
          <form className="login-form" onSubmit={handleSubmit}>
            <div className="login-logo-header">
              <Shield className="login-logo-icon animate-pulse-glow" size={48} />
              <h1 className="login-title">GuardianIQ</h1>
              <p className="login-subtitle">Enterprise Shield Platform</p>
            </div>

            {error && (
              <div className="login-error-alert">
                <AlertCircle size={18} className="error-alert-icon" />
                <span className="error-alert-text">{error}</span>
              </div>
            )}

            <div className="login-fields">
              <FormField
                label="Username / Email"
                placeholder="Enter your corporate username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading}
                required
              />

              <FormField
                label="Password"
                type="password"
                placeholder="Enter your security credentials"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                required
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={loading}
              className="login-submit-btn"
            >
              Sign In to Platform
            </Button>

            <div className="login-footer">
              <p className="login-terms">
                Secured by military-grade AES-256 and context-aware device fingerprinting. 
                Unauthorized access attempts will be audited and prosecuted.
              </p>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
};
