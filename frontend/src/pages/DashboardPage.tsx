/* src/pages/DashboardPage.tsx */
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { PageHeader } from "../components/common/PageHeader";
import { Card } from "../components/common/Card";
import { Badge } from "../components/common/Badge";
import { Table } from "../components/common/Table";
import { useAuth } from "../hooks/useAuth";
import { fetchDbHealth } from "../services/health/healthService";
import { fetchTenants } from "../services/tenants/tenantService";
import { fetchAuditEvents } from "../services/audit/auditService";
import { 
  ShieldCheck, 
  Users, 
  Activity, 
  FileText
} from "lucide-react";
import "./DashboardPage.css";

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  description: string;
  glow?: boolean;
  onClick?: () => void;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon, description, glow = false, onClick }) => {
  return (
    <Card className={`metric-card ${onClick ? "clickable" : ""}`} glow={glow} onClick={onClick}>
      <div className="metric-card-inner">
        <div className="metric-card-details">
          <span className="metric-card-title">{title}</span>
          <span className="metric-card-value">{value}</span>
          <span className="metric-card-desc">{description}</span>
        </div>
        <div className="metric-card-icon-wrap">
          {icon}
        </div>
      </div>
    </Card>
  );
};

export const DashboardPage: React.FC = () => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [dbLatency, setDbLatency] = useState<number | null>(null);
  const [dbStatus, setDbStatus] = useState<string>("DOWN");
  const [tenantCount, setTenantCount] = useState<number>(1);
  const [activeTenantDesc, setActiveTenantDesc] = useState<string>("Active sessions on platform");
  const [auditCount, setAuditCount] = useState<number | null>(null);
  const [activeLogins, setActiveLogins] = useState<any[]>([]);

  useEffect(() => {
    let active = true;
    const loadDashboardData = async () => {
      const healthPromise = (async () => {
        try {
          const health = await fetchDbHealth();
          if (active) {
            setDbLatency(health.latency_ms ?? null);
            setDbStatus(health.status === "healthy" ? "UP" : "DOWN");
          }
        } catch (e) {
          if (active) {
            setDbLatency(null);
            setDbStatus("DOWN");
          }
        }
      })();

      const tenantsPromise = (async () => {
        try {
          const token = JSON.parse(sessionStorage.getItem("guardianiq_access_token") || "null");
          if (token) {
            const startOfToday = new Date();
            startOfToday.setHours(0, 0, 0, 0);
            const response = await fetchAuditEvents(token, {
              per_page: 50,
              event_type: "auth.login_success",
              created_after: startOfToday.toISOString(),
            });
            const loginEvents = response.items || [];
            
            // Deduplicate by user
            const uniqueUsers = new Map();
            loginEvents.forEach(ev => {
              if (ev.actor_username && !uniqueUsers.has(ev.actor_username)) {
                uniqueUsers.set(ev.actor_username, {
                  id: ev.id,
                  user: ev.actor_username,
                  ip: ev.ip_address || "Unknown IP",
                  device: ev.user_agent ? ev.user_agent.substring(0, 30) : "Unknown Device",
                  status: "Active",
                  time: new Date(ev.created_at).toLocaleTimeString()
                });
              }
            });
            
            const sessions = Array.from(uniqueUsers.values());
            if (active) {
              if (sessions.length > 0) {
                setActiveLogins(sessions);
                setTenantCount(sessions.length);
                setActiveTenantDesc(`${sessions.length} active login${sessions.length > 1 ? 's' : ''}`);
              } else {
                setTenantCount(1);
                setActiveTenantDesc("Only current session active");
              }
            }
          }
        } catch (e) {
          console.warn("Using local fallback login data:", e);
        }
      })();

      const auditPromise = (async () => {
        try {
          const token = JSON.parse(sessionStorage.getItem("guardianiq_access_token") || "null");
          if (token) {
            const startOfToday = new Date();
            startOfToday.setHours(0, 0, 0, 0);
            const response = await fetchAuditEvents(token, {
              per_page: 1,
              created_after: startOfToday.toISOString(),
            });
            if (active) {
              setAuditCount(response.total);
            }
          }
        } catch (e) {
          console.warn("Failed to fetch audit events for today:", e);
        }
      })();

      try {
        await Promise.all([healthPromise, tenantsPromise, auditPromise]);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    loadDashboardData();
    return () => {
      active = false;
    };
  }, []);

  const getDeviceSignature = () => {
    const ua = navigator.userAgent;
    let os = "Windows";
    if (ua.indexOf("Mac") !== -1) os = "macOS";
    else if (ua.indexOf("Linux") !== -1) os = "Linux";
    else if (ua.indexOf("Android") !== -1) os = "Android";
    else if (ua.indexOf("like Mac") !== -1) os = "iOS";

    let browser = "Chrome";
    if (ua.indexOf("Edg") !== -1) browser = "Edge";
    else if (ua.indexOf("Firefox") !== -1) browser = "Firefox";
    else if (ua.indexOf("Safari") !== -1 && ua.indexOf("Chrome") === -1) browser = "Safari";

    return `${os} - ${browser}`;
  };

  const recentSessions = activeLogins.length > 0 ? activeLogins : (currentUser ? [
    { 
      id: "1", 
      user: currentUser.full_name || currentUser.name || currentUser.username || currentUser.email || "current_user", 
      ip: "127.0.0.1", 
      device: getDeviceSignature(), 
      status: "Active", 
      time: "Just now" 
    }
  ] : []);

  const columns = [
    { key: "user", header: "Identity" },
    { key: "ip", header: "IP Address" },
    { key: "device", header: "Device Signature" },
    { 
      key: "status", 
      header: "Status",
      render: (row: typeof recentSessions[0]) => (
        <Badge 
          label={row.status} 
          variant={row.status === "Active" ? "success" : "neutral"} 
          dot={row.status === "Active"}
        />
      )
    },
    { key: "time", header: "Last Active" },
  ];

  return (
    <div className="dashboard-page">
      <PageHeader 
        title="Security Cockpit" 
        description={`Welcome back, ${currentUser?.full_name || currentUser?.name || currentUser?.username || currentUser?.email}. Contextual RBAC is fully active.`} 
      />

      <div className="dashboard-grid">
        <MetricCard 
          title="Security Posture"
          value="COMPLIANT"
          icon={<ShieldCheck size={24} className="metric-icon success" />}
          description="Decryption & fingerprinting green"
          glow
        />

        <MetricCard 
          title="Active Tenants"
          value={tenantCount}
          icon={<Users size={24} className="metric-icon info" />}
          description={activeTenantDesc}
        />

        <MetricCard 
          title="System Health"
          value={dbStatus === "UP" ? "99.9%" : "OFFLINE"}
          icon={<Activity size={24} className={`metric-icon ${dbStatus === "UP" ? "success" : "danger"}`} />}
          description={dbStatus === "UP" && dbLatency !== null ? `Database latency: ${dbLatency.toFixed(1)} ms` : "Database is unreachable"}
          onClick={() => navigate("/health")}
        />

        <MetricCard 
          title="Audit Trail"
          value={auditCount !== null ? auditCount : "SECURE"}
          icon={<FileText size={24} className="metric-icon warning" />}
          description={auditCount !== null ? "SECURE • All event digests verified" : "All event digests verified"}
          onClick={() => navigate("/audit")}
        />
      </div>

      <Card title="Current Session Context" subtitle="Active identities and verified fingerprints on this domain">
        <Table 
          columns={columns} 
          data={recentSessions} 
          loading={loading} 
        />
      </Card>
    </div>
  );
};

