import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { FormField } from "../components/common/FormField";
import { Button } from "../components/common/Button";
import { Card } from "../components/common/Card";
import { Shield, AlertCircle } from "lucide-react";
import { changePassword } from "../services/auth/authService";
import { storage } from "../utils/storage";
import "./LoginPage.css";

export const LoginPage: React.FC = () => {
  const { login, completeFirstLogin } = useAuth();
  const navigate = useNavigate();
  
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [needsChange, setNeedsChange] = useState(false);
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
      const res = await login(username, password);
      if (res.needsPasswordChange) {
        setNeedsChange(true);
      } else {
        navigate("/dashboard");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Invalid credentials or server error.");
    } finally {
      setLoading(false);
    }
  };

  const handleChangePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPassword || !confirmPassword) {
      setError("Please fill in all fields.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (newPassword.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }
    
    setError(null);
    setLoading(true);
    try {
      const token = storage.get<string>("guardianiq_access_token");
      if (!token) throw new Error("Authentication token not found.");
      
      await changePassword(newPassword, token);
      await completeFirstLogin(token);
      navigate("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to change password.");
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
          {needsChange ? (
            <form className="login-form" onSubmit={handleChangePasswordSubmit}>
              <div className="login-logo-header">
                <Shield className="login-logo-icon animate-pulse-glow" size={48} />
                <h1 className="login-title">Change Password</h1>
                <p className="login-subtitle">You are using a default password. Please choose a new password.</p>
              </div>

              {error && (
                <div className="login-error-alert">
                  <AlertCircle size={18} className="error-alert-icon" />
                  <span className="error-alert-text">{error}</span>
                </div>
              )}

              <div className="login-fields">
                <FormField
                  label="New Password"
                  type="password"
                  placeholder="Enter your new password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  disabled={loading}
                  required
                />

                <FormField
                  label="Confirm Password"
                  type="password"
                  placeholder="Confirm your new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
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
                Change Password & Sign In
              </Button>
            </form>
          ) : (
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
          )}
        </Card>
      </div>
    </div>
  );
};
