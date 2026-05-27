/* src/components/layout/AppShell.tsx */
import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { 
  Shield, 
  LayoutDashboard, 
  HeartPulse, 
  History, 
  Users, 
  LogOut, 
  Menu, 
  X,
  User as UserIcon
} from "lucide-react";
import "./AppShell.css";

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const { currentUser, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/login");
    } catch (e) {
      console.error("Logout failed:", e);
    }
  };

  const navItems = [
    { label: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
    { label: "Foundation Health", path: "/health", icon: HeartPulse },
    { label: "Audit Logs", path: "/audit", icon: History },
  ];

  // Admin and Superuser items
  const isAdmin = currentUser?.roles?.includes("admin") || currentUser?.is_superuser;
  if (isAdmin) {
    navItems.push({ label: "Tenants", path: "/tenants", icon: Users });
  }

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className={`app-sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="sidebar-logo">
          <Shield className="sidebar-logo-icon" size={24} />
          <span className="sidebar-logo-text">GuardianIQ</span>
          <button className="sidebar-close-btn" onClick={toggleSidebar} aria-label="Close menu">
            <X size={20} />
          </button>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`sidebar-link ${isActive ? "active" : ""}`}
                onClick={() => setSidebarOpen(false)}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          {currentUser && (
            <div className="sidebar-user">
              <div className="user-avatar">
                {(currentUser.name || currentUser.username || currentUser.email || "US").substring(0, 2).toUpperCase()}
              </div>
              <div className="user-info">
                <span className="user-name">{currentUser.name || currentUser.username || currentUser.email}</span>
                <span className="user-role-badge">
                  {currentUser.is_superuser ? "SUPERADMIN" : currentUser.roles?.[0] || "USER"}
                </span>
              </div>
            </div>
          )}
          <button className="sidebar-logout-btn" onClick={handleLogout}>
            <LogOut size={16} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Layout */}
      <div className="app-main">
        <header className="app-header">
          <div className="header-title-section">
            <button className="sidebar-toggle-btn" onClick={toggleSidebar} aria-label="Toggle menu">
              <Menu size={24} />
            </button>
            <span className="header-platform-label">Enterprise Shield Platform</span>
          </div>

          <div className="header-actions">
            {currentUser && (
              <div className="header-profile">
                <UserIcon size={16} />
                <span className="header-profile-name">{currentUser.email}</span>
              </div>
            )}
          </div>
        </header>

        <main className="app-content animate-fade-in">
          {children}
        </main>
      </div>
    </div>
  );
};
