/* src/components/layout/AppShell.tsx */
import React, { useState, useEffect, useRef } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import * as registryService from "../../services/registry/registryService";
import { 
  Shield, 
  LayoutDashboard, 
  HeartPulse,
  History,
  Users,
  LogOut, 
  Menu, 
  X,
  User as UserIcon,
  Library,
  Brain,
  Cpu,
  Plug,
  GitBranch,
  Database,
  Building2,
  Link2,
  ChevronDown,
  ChevronRight,
  ChevronLeft,
  Search,
  Loader2,
  Sparkles
} from "lucide-react";
import { CommandPalette } from "./CommandPalette";
import "./AppShell.css";

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const { currentUser, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false); // Mobile drawer
  const [isCollapsed, setIsCollapsed] = useState(false); // Desktop collapse
  const [registryOpen, setRegistryOpen] = useState(location.pathname.startsWith("/registry"));

  // Global Search State
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchDropdown, setShowSearchDropdown] = useState(false);
  
  const searchContainerRef = useRef<HTMLDivElement>(null);

  // Close dropdown on route change
  useEffect(() => {
    setShowSearchDropdown(false);
    setSearchQuery("");
  }, [location.pathname]);

  // Click outside listener
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
        setShowSearchDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Escape key listener
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setShowSearchDropdown(false);
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Debounced search fetch
  useEffect(() => {
    if (searchQuery.trim().length < 2) {
      setSearchResults(null);
      setShowSearchDropdown(false);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    const delayDebounceFn = setTimeout(async () => {
      try {
        const res = await registryService.globalSearch(searchQuery);
        if (res.data) {
          setSearchResults(res.data);
          setShowSearchDropdown(true);
        }
      } catch (err) {
        console.error("Global search failed:", err);
      } finally {
        setIsSearching(false);
      }
    }, 400);

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery]);

  const handleResultClick = (item: any, type: string) => {
    setShowSearchDropdown(false);
    setSearchQuery("");
    
    const base = type.toLowerCase().replace("_", "-");
    let route = "";
    if (type === "USER") {
      route = `/registry/users-roles?tab=users&search=${encodeURIComponent(item.code)}`;
    } else if (type === "ROLE") {
      route = `/registry/users-roles?tab=roles&search=${encodeURIComponent(item.code)}`;
    } else {
      route = `/registry/${base}s?search=${encodeURIComponent(item.code || item.name)}`;
    }
    navigate(route);
  };

  const getGroupTitle = (key: string) => {
    if (key === "models") return "AI Models";
    if (key === "agents") return "AI Agents";
    if (key === "tools") return "Tools";
    if (key === "workflows") return "Workflows";
    if (key === "data_sources") return "Data Sources";
    if (key === "users") return "Identities";
    return key;
  };

  // Check if any results were found
  const hasResults = searchResults && Object.keys(searchResults).some(key => {
    const list = searchResults[key];
    return Array.isArray(list) && list.length > 0;
  });

  const registrySubItems = [
    { label: "AI Models", path: "/registry/models", icon: Brain },
    { label: "AI Agents", path: "/registry/agents", icon: Cpu },
    { label: "Tools", path: "/registry/tools", icon: Plug },
    { label: "Workflows", path: "/registry/workflows", icon: GitBranch },
    { label: "Data Sources", path: "/registry/data-sources", icon: Database },
    { label: "Departments", path: "/registry/departments", icon: Building2 },
    { label: "Users & Roles", path: "/registry/users-roles", icon: Users },
    { label: "Relationships", path: "/registry/relationships", icon: Link2 },
  ];

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
    { label: "Executions", path: "/executions", icon: GitBranch },
    { label: "Register All", path: "/register-all", icon: Sparkles },
  ];

  // Admin and Superuser items
  const isAdmin = currentUser?.roles?.includes("admin") || currentUser?.is_superuser;
  if (isAdmin) {
    navItems.push({ label: "Tenants", path: "/tenants", icon: Users });
  }

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

  return (
    <div className={`app-container ${isCollapsed ? 'sidebar-collapsed' : ''}`}>
      {/* Desktop Sidebar Collapse Toggle */}
      <button 
        className="sidebar-collapse-toggle" 
        onClick={() => setIsCollapsed(!isCollapsed)}
        aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>

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

          {/* Registry Collapsible Section */}
          <div className="sidebar-registry-section" style={{ display: "flex", flexDirection: "column", gap: "0.25rem", marginTop: "0.5rem" }}>
            <button
              type="button"
              className={`sidebar-link sidebar-section-toggle ${location.pathname.startsWith("/registry") ? "active" : ""}`}
              onClick={() => setRegistryOpen(!registryOpen)}
              style={{
                width: "100%",
                background: "transparent",
                border: "none",
                textAlign: "left",
                justifyContent: "flex-start",
                cursor: "pointer",
                fontFamily: "inherit",
                fontSize: "inherit",
                fontWeight: "inherit"
              }}
            >
              <Library size={18} />
              <span>Registry</span>
              <span style={{ marginLeft: "auto", display: "flex", alignItems: "center" }}>
                {registryOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </span>
            </button>

            {registryOpen && (
              <div className="sidebar-sub-nav" style={{ paddingLeft: "1rem", display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                {registrySubItems.map((subItem) => {
                  const SubIcon = subItem.icon;
                  const isSubActive = location.pathname === subItem.path;
                  return (
                    <Link
                      key={subItem.path}
                      to={subItem.path}
                      className={`sidebar-link sidebar-sub-link ${isSubActive ? "active" : ""}`}
                      onClick={() => setSidebarOpen(false)}
                      style={{
                        fontSize: "0.8rem",
                        padding: "0.4rem 0.75rem",
                        gap: "var(--spacing-md)"
                      }}
                    >
                      <SubIcon size={14} />
                      <span>{subItem.label}</span>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
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

          {/* Task D: Global Search Bar Component */}
          <div className="header-search-bar" ref={searchContainerRef}>
            <div className="search-input-box">
              <Search className="search-input-icon" size={16} />
              <input
                type="text"
                placeholder="Search registry assets..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => searchQuery.trim().length >= 2 && setShowSearchDropdown(true)}
                className="search-text-input"
              />
              {isSearching && <Loader2 className="search-spinner-icon" size={16} />}
            </div>

            {showSearchDropdown && searchResults && (
              <div className="search-results-dropdown animate-fade-in">
                {hasResults ? (
                  Object.keys(searchResults).map((groupKey) => {
                    const items = (searchResults as any)[groupKey] || [];
                    if (!Array.isArray(items) || items.length === 0) return null;
                    const groupTitle = getGroupTitle(groupKey);

                    return (
                      <div key={groupKey} className="search-result-group">
                        <div className="search-group-header">{groupTitle}</div>
                        <div className="search-group-items">
                          {items.slice(0, 5).map((item: any) => (
                            <button
                              key={item.id}
                              type="button"
                              onClick={() => handleResultClick(item, item.entity_type)}
                              className="search-result-row"
                            >
                              <div className="search-row-main">
                                <span className="search-row-code">{item.code || item.name}</span>
                                <span className="search-row-name">{item.name}</span>
                              </div>
                              <span className={`search-row-status-badge ${String(item.status).toLowerCase()}`}>
                                {item.status}
                              </span>
                            </button>
                          ))}
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="search-no-results">
                    No registry assets found for "{searchQuery}"
                  </div>
                )}
              </div>
            )}
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

      <CommandPalette />
    </div>
  );
};
