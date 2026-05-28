import React, { useEffect, useState } from "react";
import { PageHeader } from "../components/common/PageHeader";
import { Card } from "../components/common/Card";
import { Badge } from "../components/common/Badge";
import { Table } from "../components/common/Table";
import { Loader } from "../components/common/Loader";
import { useAuth } from "../hooks/useAuth";
import { storage } from "../utils/storage";
import { 
  User as UserIcon, 
  Mail, 
  Shield, 
  Clock, 
  LogOut,
  Calendar
} from "lucide-react";
import "./ProfilePage.css";

// Basic JWT decode to get exp and iat
const decodeJWT = (token: string) => {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
};

export const ProfilePage: React.FC = () => {
  const { currentUser, logout, loading: authLoading } = useAuth();
  const [sessionInfo, setSessionInfo] = useState<{ exp: Date | null, iat: Date | null }>({ exp: null, iat: null });

  useEffect(() => {
    const token = storage.get<string>("guardianiq_access_token");
    if (token) {
      const decoded = decodeJWT(token);
      if (decoded) {
        setSessionInfo({
          exp: decoded.exp ? new Date(decoded.exp * 1000) : null,
          iat: decoded.iat ? new Date(decoded.iat * 1000) : null,
        });
      }
    }
  }, []);

  if (authLoading) {
    return <div className="profile-loading"><Loader /></div>;
  }

  // Handle null currentUser gracefully
  if (!currentUser) {
    return <div className="profile-error">Failed to load user profile.</div>;
  }

  const permissionsData = currentUser.permissions?.map((p, index) => ({ id: index.toString(), permission: p })) || [];
  
  const permColumns = [
    { key: "permission", header: "Permission Name" }
  ];

  return (
    <div className="profile-page">
      <div className="profile-header-container">
        <PageHeader 
          title="User Profile" 
          description="View your current account details and session information." 
        />
        <button className="btn-logout" onClick={() => logout()}>
          <LogOut size={16} />
          <span>Logout</span>
        </button>
      </div>

      <div className="profile-grid">
        <div className="profile-column">
          <Card title="Account Details" subtitle="Your personal information">
            <div className="profile-info-list">
              <div className="profile-info-item">
                <UserIcon className="info-icon" size={20} />
                <div className="info-content">
                  <span className="info-label">Full Name</span>
                  <span className="info-value">{currentUser.full_name || currentUser.name || "N/A"}</span>
                </div>
              </div>
              
              <div className="profile-info-item">
                <Mail className="info-icon" size={20} />
                <div className="info-content">
                  <span className="info-label">Email Address</span>
                  <span className="info-value">{currentUser.email}</span>
                </div>
              </div>

              <div className="profile-info-item">
                <Shield className="info-icon" size={20} />
                <div className="info-content">
                  <span className="info-label">Roles</span>
                  <div className="info-badges">
                    {currentUser.is_superuser && <Badge label="Superuser" variant="warning" />}
                    {currentUser.roles?.map(role => (
                      <Badge key={role} label={role} variant="info" />
                    ))}
                    {(!currentUser.roles || currentUser.roles.length === 0) && !currentUser.is_superuser && (
                      <span className="info-value">No roles assigned</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="profile-info-item">
                <div className={`status-indicator ${currentUser.is_active !== false ? 'active' : 'inactive'}`} />
                <div className="info-content">
                  <span className="info-label">Account Status</span>
                  <span className="info-value">{currentUser.is_active !== false ? "Active" : "Inactive"}</span>
                </div>
              </div>
            </div>
          </Card>

          <Card title="Session Information" subtitle="Current authentication status">
            <div className="profile-info-list">
              <div className="profile-info-item">
                <Clock className="info-icon" size={20} />
                <div className="info-content">
                  <span className="info-label">Session Started</span>
                  <span className="info-value">
                    {sessionInfo.iat ? sessionInfo.iat.toLocaleString() : "Unknown"}
                  </span>
                </div>
              </div>

              <div className="profile-info-item">
                <Calendar className="info-icon" size={20} />
                <div className="info-content">
                  <span className="info-label">Token Expiry</span>
                  <span className="info-value">
                    {sessionInfo.exp ? sessionInfo.exp.toLocaleString() : "Unknown"}
                  </span>
                </div>
              </div>
            </div>
          </Card>
        </div>

        <div className="profile-column">
          <Card title="Assigned Permissions" subtitle="Capabilities granted to your account">
            {permissionsData.length > 0 ? (
              <Table 
                columns={permColumns} 
                data={permissionsData} 
              />
            ) : (
              <div className="no-permissions">No specific permissions assigned.</div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
